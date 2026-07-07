---
title: AI YouTube Summarizer
emoji: 🎥
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "4.44.1"
app_file: app.py
pinned: false
---

# AI YouTube Summarizer

An AI-powered YouTube Video Summarizer and Q&A application built with Gradio, LangChain, FAISS, and Google Gemini.



# AI YouTube Summarizer

A web app that turns YouTube videos into concise summaries, answers questions about video content, and analyzes transcript sentiment. Built with Google Gemini, LangChain, and Gradio.

## Features

- **Video summarization** — Fetches a YouTube transcript and generates a concise summary of the main points.
- **Question answering** — Ask natural-language questions about a video; relevant transcript sections are retrieved with FAISS and answered by Gemini.
- **Sentiment analysis** — Returns overall sentiment, confidence, key emotions, and a short explanation of the transcript tone.
- **Multi-language output** — Summaries, answers, and sentiment explanations can be generated in:
  - English
  - Hindi
  - Spanish
  - French
  - German
  - Japanese
  - Gujarati
- **Transcript fallback** — If a transcript is not available in the selected language, the app falls back to English (or another available transcript) and translates via Gemini.

## Tech Stack

| Layer | Technology |
| --- | --- |
| UI | [Gradio](https://gradio.app/) |
| LLM | [Google Gemini](https://ai.google.dev/) (`gemini-2.5-flash`) via `langchain-google-genai` |
| Embeddings | Google Generative AI Embeddings (`models/embedding-001`) |
| Orchestration | [LangChain](https://www.langchain.com/) |
| Vector search | [FAISS](https://github.com/facebookresearch/faiss) |
| Transcripts | [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) |
| Config | `python-dotenv` |

## Installation

### Prerequisites

- Python 3.11+ recommended
- A [Google AI Studio API key](https://aistudio.google.com/apikey)

### Steps

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd "AI YOUTUBE SUMMARIZER"
   ```

2. **Create and activate a virtual environment**

   **Windows (PowerShell):**

   ```powershell
   python -m venv my_env
   .\my_env\Scripts\Activate.ps1
   ```

   **macOS / Linux:**

   ```bash
   python3 -m venv my_env
   source my_env/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (see below)

## Environment Variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

| Variable | Required | Description |
| --- | --- | --- |
| `GOOGLE_API_KEY` | Yes | API key from [Google AI Studio](https://aistudio.google.com/apikey). Used for Gemini text generation and embeddings. |

Alternatively, set the variable in your shell before running the app:

**Windows (PowerShell):**

```powershell
$env:GOOGLE_API_KEY = "your_google_api_key_here"
```

**macOS / Linux:**

```bash
export GOOGLE_API_KEY="your_google_api_key_here"
```

> **Note:** Do not commit your `.env` file or API key to version control.

## How to Run Locally

1. Activate your virtual environment (if not already active).

2. Start the app:

   ```bash
   python app.py
   ```

3. Open the URL shown in the terminal (typically `http://127.0.0.1:7860`).

4. In the UI:
   - Paste a YouTube video URL
   - Choose an **Output Language**
   - Click **Summarize Video**, **Ask a Question**, or **Analyze Sentiment**

### Example YouTube URL format

```
https://www.youtube.com/watch?v=VIDEO_ID
```

The video must have captions/transcripts enabled on YouTube for the app to work.

## Project Structure

```
AI YOUTUBE SUMMARIZER/
├── app.py              # Main application (Gradio UI + logic)
├── requirements.txt    # Python dependencies
├── .env                # Local environment variables (not committed)
├── .gitignore
└── README.md
```

## Troubleshooting

- **`GOOGLE_API_KEY environment variable is not set`** — Add the key to `.env` or export it in your shell.
- **`No transcript available for this video`** — The video may not have captions, or transcripts may be disabled by the uploader.
- **`Invalid YouTube URL`** — Use a standard watch URL in the form `https://www.youtube.com/watch?v=...`.
