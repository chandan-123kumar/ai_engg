---
title: ai_agent
app_file: src/main.py
sdk: gradio
sdk_version: 6.14.0
---
# AI Learning — LinkedIn Profile Chatbot

A personal AI assistant that answers questions about Chandan Kumar by reading his LinkedIn profile PDF and using OpenAI's GPT-4o-mini with structured output.

## What it does

- Extracts text from a LinkedIn PDF profile
- Serves a Gradio chat UI where you can ask questions about the profile
- Uses OpenAI structured output to return typed answers with a `known` flag
- Sends a Pushover notification if the AI doesn't know the answer, prompting the real person to respond

## Project Structure

```
src/
  main.py          # All application logic
  doc/
    linkedin.pdf   # Source LinkedIn profile PDF
    me.txt         # Extracted text (auto-generated)
```

## Setup

**1. Install dependencies**
```bash
uv sync
```

**2. Create a `.env` file**
```
OPENAI_API_KEY=sk-...
PUSHOVER_TOKEN=...
PUSHOVER_USER=...
```

**3. Run**
```bash
uv run src/main.py
```

Then open the Gradio URL printed in the terminal (usually `http://127.0.0.1:7860`).

## How it works

1. `dump_to_text()` extracts the PDF into `me.txt` on startup
2. `get_context()` reads `me.txt` for use as the system prompt context
3. `get_structured_prompt(message)` builds the OpenAI messages list — system message with profile context + user question
4. `call_open_ai(message)` calls GPT-4o-mini with structured output, returning a `ProfileAnswer` with `answer: str` and `know: bool`
5. If `know` is `False`, a Pushover notification is sent to the real Chandan Kumar

## Dependencies

- `openai` — GPT-4o-mini with structured output
- `pypdf` — PDF text extraction
- `gradio` — Chat UI
- `pydantic` — Structured response model
- `python-dotenv` — Environment variable loading
- `requests` — Pushover notifications
