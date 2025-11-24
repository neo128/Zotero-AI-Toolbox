# PaperPilot 脚本策略手册

以下内容概述 `scripts/` 目录中主要脚本的设计思路和执行策略，方便快速理解整个自动化流程的组成（例子参考 `scripts/fetch_missing_pdfs.py` 的详细说明）。

## watch_and_import_papers.py
- **作用**：根据 `tag.json` 的关键词 + HuggingFace 热点榜单追踪论文、打分并写入 Zotero。
- **策略**：
  1. **数据准备**：加载标签配置（标签名、示例关键词）、读取 HuggingFace 日/周/月榜单（`fetch_hf_period`）和 Zotero 库索引（DOI/arXiv/URL/标题-年份），以便后续去重。
  2. **候选抓取**：针对每个标签关键词调用 arXiv API (`fetch_arxiv_by_keywords`) 获取候选，同时匹配 HuggingFace trending 条目，记录 `hf_score` 等信息。
  3. **元数据补全**：对候选调用 Semantic Scholar / CrossRef 获取引用数、摘要、DOI 等，用于打分和建模。
  4. **打分筛选**：`compute_score()` 综合 “最近性 + 引用数 + HF 权重”，并提供 `--hf-override-limit` 在得分过低时强制保留前 N 条 HF 候选。
  5. **导入和去重**：用 `identity()` 判断是否重复，若需要可 `--fill-missing` 补写旧条目的 DOI/摘要/URL；新建条目时自动创建集合、添加标签，并据 arXiv/Unpaywall 附加 PDF。
  6. **输出**：写日志、JSON 报告、`.data/new_items_watch.json`（记录新增 key + 时间），为 `fetch_missing_pdfs.py` 等后续步骤提供数据。

## fetch_missing_pdfs.py
- **作用**：在 watch 过的条目或最近更新的条目中，找出缺少本地 PDF 的 Zotero 项，然后自动下载/挂载。
- **详细策略**：
  1. **候选来源**：
     - 读取 `.data/new_items_watch.json`（由 watch 阶段生成），按 `--since-hours` 过滤 `items`，得到“本次 watch 新增”的 key 列表。
     - 如果 JSON 为空或过滤后没有 key，则遍历 `/items/top`，根据 `dateAdded/dateModified` 与 `--since-hours` 选出最近新增/修改的条目。
     - 合并去重后（保持顺序），可用 `--limit` 截断。
  2. **检查附件**：
     - 调用 `fetch_children` 拉取 child items；只有 `itemType == "attachment"` 且 `linkMode` 属于 `imported_file/linked_file/imported_url` 并携带 PDF 才表示已有本地附件。
     - 若是 `linked_url`，会将链接暂存，后续作为下载策略的候选。
     - 已有本地 PDF 的条目输出 `[INFO] Item ... already has local PDF attachments; skipping.`。
  3. **下载策略**（`guess_pdf_sources`）：
     - 现有 `linked_url` → 优先尝试，确保把网页链接转换成本地文件；
     - `url` 末尾是 `.pdf` → 直接下载；
     - URL/extra 中能提取 arXiv ID → 拼 `https://arxiv.org/pdf/<id>.pdf`；
     - 如果有 DOI 且配置了 `UNPAYWALL_EMAIL` → 调用 Unpaywall 获取可下载地址。
  4. **下载和挂载**：
     - `--dry-run` 模式仅打印 `[TRY] key ← label: url`，用于预览；
     - 正常模式：`requests.get()` 下载到 `storage_dir/auto_pdfs/<key>/<title>.pdf`，并调用 `create_linked_file()` 创建 attachment（linkMode=linked_file / tag=auto-pdf）。
  5. **终止条件与统计**：每处理一个候选，更新 `fetched/skipped`；若配置 `--limit` 且 `fetched + skipped == limit` 即停止；最后打印 `[INFO] Completed. PDFs added: X, remaining without PDF: Y.`

## merge_zotero_duplicates.py
- **作用**：根据 DOI/URL/标题年自动合并重复条目。
- **策略**：扫描目标范围（collection/tag/limit），按 `ItemBundle` 收集附件/笔记/时间戳，以 PDF/附件/更新时间为排序指标选择保留者；把其他条目的附件/笔记重新挂到保留者，将集合/标签并集后更新保留者，最后删除冗余条目（支持 `--dry-run`）。

## summarize_zotero_with_doubao.py
- **作用**：用 AI 模型（Doubao/Qwen/OpenAI 兼容）对 Zotero 的 PDF 生成 Markdown 摘要，写回 Notes。
- **策略**：根据 `--collection/--tag/--item-keys` 获取条目，检索本地 PDF（受 `--max-pages/--max-chars` 控制），使用 `pypdf` 提取文本，再通过 `AIChatClient` 调用指定模型生成结构化总结。成功时渲染 Markdown → HTML 并创建 note（除非 `--dry_run`），可通过 `--ai-provider/--ai-api-key` 指定不同模型。

## enrich_zotero_abstracts.py
- **作用**：为缺 `abstractNote` 的条目自动寻找摘要。
- **策略**：在指定 collection/tag 范围内，跳过 Notes/附件；依次尝试 URL meta → CrossRef (DOI) → Semantic Scholar (DOI/ArXiv) → ArXiv API，任一成功就更新条目（`--dry-run` 仅打印操作）。

## sync_zotero_to_notion.py
- **作用**：将 Zotero 条目映射到 Notion 数据库，支持 AI 辅助填充“贡献/局限/机器人平台”等字段。
- **策略**：读取 Notion DB schema，自动匹配 Title/Authors/Year/Tags/URL/DOI 等字段；根据 `tag.json` / AI 辅助输出生成 Notion payload；优先按“Zotero Key” 或 Title 查找已有页面并更新，否则创建新条目。

## Orchestration & Support
- **ai_toolbox_pipeline.sh**：Bash 脚本，按 `--dedupe/--summarize/...` 切换阶段，顺序调用各 Python 脚本。
- **langchain_pipeline.py**：LangChain 版本，构建 `RunnableLambda` 串联 watch → fetch-pdfs → dedupe → summaries → abstracts → notion，统一日志并输出 `--state-json`。
- **ai_utils.py**：解析 AI Provider（Doubao/Qwen/自定义 OpenAI）配置，创建 `OpenAI` 兼容客户端。
- **utils_sources.py**：封装 arXiv/SemanticScholar/CrossRef/HuggingFace 等数据源，提供 HTML 清理、作者标准化等工具。
- **import_ris_folder.py / import_embodied_ai_to_zotero.py / awesome_vla_to_ris.py**：从 RIS 或 README 导入资源到 Zotero；执行策略包括遍历目录、解析条目、可选 enrich，再写入 RIS 或调用 API。

以上策略与 README 的“LangChain 流程”和各脚本说明保持一致，可帮助快速定位每个阶段的功能与扩展方式。
