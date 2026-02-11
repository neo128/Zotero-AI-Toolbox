# Support

Use the right channel so issues can be handled quickly and cleanly.

## 1) Bug Reports

Use GitHub Issues with the **Bug report** template when behavior is incorrect.

Please include:

- exact command(s)
- key logs/errors
- Python version and OS
- whether `.env` is set from `.env.example` or profile presets

## 2) Feature Requests

Use GitHub Issues with the **Feature request** template when proposing new behavior.

Please include:

- the workflow pain point
- expected CLI/API behavior
- alternatives considered

## 3) Usage Questions

For setup/usage questions, open a question issue (template provided) and include:

- what you are trying to achieve
- commands already tried
- relevant snippets from logs

## 4) Security Reports

Do not open public issues for security vulnerabilities.

Follow `/SECURITY.md` and use private reporting channels.

## 5) Quick Self-Check

Before opening an issue, run:

```bash
make ci
```

and then try a minimal dry-run command related to your workflow.

## 6) New Contributor Entry

- Starter tasks: see `docs/GOOD_FIRST_ISSUES.md`.
- Triage and response expectations: see `docs/TRIAGE_POLICY.md`.
