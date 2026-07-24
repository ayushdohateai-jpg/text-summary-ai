# Text Summary

A self-contained AI text-summarization tool with a Flask backend and a
distinctive "marker pass" web UI. It uses a frequency-based extractive
summarization algorithm (in the tradition of Luhn's algorithm) — no
external API keys, no model downloads, works fully offline.

## How it works

1. The input passage is split into sentences.
2. Word frequencies are computed after removing common stopwords.
3. Each sentence is scored by the density of high-frequency, meaningful
   words it contains (normalized by sentence length, with a small bonus
   for early sentences, which tend to carry topic-setting information).
4. The top-scoring sentences (proportional to your chosen length: Brief
   / Balanced / Thorough) are selected and re-assembled in their original
   order to form the summary.

The UI visualizes this as a "marker pass": every sentence from your
original text is shown, with kept sentences highlighted and dropped ones
dimmed, so you can see exactly what the algorithm chose and why.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## Project structure

```
text-summary-ai/
├── app.py                 # Flask backend + summarization engine
├── requirements.txt
├── templates/
│   └── index.html         # Page markup
└── static/
    ├── style.css           # Design system (editorial / highlighter theme)
    └── script.js            # Frontend logic + reveal animation
```

## API

`POST /summarize`

Request body:
```json
{ "text": "your passage here...", "length": "short" | "medium" | "long" }
```

Response body:
```json
{
  "summary": "...",
  "sentence_breakdown": [{ "text": "...", "kept": true }],
  "original_sentence_count": 12,
  "summary_sentence_count": 4,
  "original_word_count": 320,
  "summary_word_count": 98,
  "reduction_percent": 69
}
```

## Extending it

- **Swap in an LLM-based summarizer**: replace the `summarize()` function
  in `app.py` with a call to the Anthropic API (or another provider) for
  abstractive (rewritten) summaries instead of extractive ones.
- **Add file upload**: accept `.txt`/`.pdf` uploads and extract text
  server-side before summarizing.
- **Multi-language support**: swap the stopword list based on detected
  language.
