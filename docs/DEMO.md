# Demo Guide

This guide shows how to produce a short terminal demo for PaperPilot.

## Option A (Recommended): VHS -> GIF

Prerequisites:

- Install [VHS](https://github.com/charmbracelet/vhs)
- Ensure your shell can run `bash scripts/demo_quickstart.sh`

Render demo GIF:

```bash
bash docs/demo/generate_demo_gif.sh
```

The generated file will be written to:

```text
docs/assets/paperpilot-demo.gif
```

## Option B: Manual Terminal Recording

Run the script directly for a live walkthrough:

```bash
bash scripts/demo_quickstart.sh
```

This path is useful when recording with your preferred screen recorder.

## Notes

- The demo script is safe: it only executes help and environment commands.
- Keep recordings short (20-40 seconds) for README conversion.
