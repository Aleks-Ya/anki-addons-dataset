# HuggingFace

## HuggingFace CLI
1. Login: `hf auth login`
2. Verify: `hf auth whoami`

## HuggingFace Spaces
Visualizations: https://huggingface.co/spaces/Ya-Alex/anki-addons

The Space downloads the dataset parquet files from the Hub on startup and logs:

```
Warning: You are sending unauthenticated requests to the HF Hub.
Please set a HF_TOKEN to enable higher rate limits and faster downloads.
```

It is harmless: the dataset is public, so anonymous downloads work. The warning only means the Space
container has no `HF_TOKEN`, hence per-IP rate limits and no accelerated downloads. To silence it, add a
read-only token as a Space secret named `HF_TOKEN` (Space -> Settings -> Variables and secrets);
`huggingface_hub` reads it from the environment, no code change needed. This is unrelated to the
credentials `upload` uses (`hf auth login`).
