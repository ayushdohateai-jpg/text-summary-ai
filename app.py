"""
Text Summary AI
----------------
A self-contained extractive text summarization tool.

No external AI API keys or heavy ML downloads required — the summarizer
uses a classic frequency-based sentence scoring algorithm (similar in
spirit to Luhn's algorithm), implemented in pure Python.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""

import re
import math
from collections import Counter
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# A compact English stopword list (kept local so no NLTK download is needed).
STOPWORDS = set("""
a about above after again against all am an and any are aren't as at be
because been before being below between both but by can't cannot could
couldn't did didn't do does doesn't doing don't down during each few for
from further had hadn't has hasn't have haven't having he he'd he'll he's
her here here's hers herself him himself his how how's i i'd i'll i'm i've
if in into is isn't it it's its itself let's me more most mustn't my
myself no nor not of off on once only or other ought our ours ourselves
out over own same shan't she she'd she'll she's should shouldn't so some
such than that that's the their theirs them themselves then there there's
these they they'd they'll they're they've this those through to too under
until up very was wasn't we we'd we'll we're we've were weren't what
what's when when's where where's which while who who's whom why why's
with won't would wouldn't you you'd you'll you're you've your yours
yourself yourselves
""".split())

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")
WORD_RE = re.compile(r"[A-Za-z']+")


def split_sentences(text: str):
    text = text.strip().replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    if not text:
        return []
    sentences = SENTENCE_SPLIT_RE.split(text)
    return [s.strip() for s in sentences if s.strip()]


def word_frequencies(sentences):
    freqs = Counter()
    for sent in sentences:
        for word in WORD_RE.findall(sent.lower()):
            if word not in STOPWORDS and len(word) > 1:
                freqs[word] += 1
    if not freqs:
        return {}
    max_freq = max(freqs.values())
    return {word: count / max_freq for word, count in freqs.items()}


def score_sentences(sentences, freqs):
    scores = []
    for idx, sent in enumerate(sentences):
        words = WORD_RE.findall(sent.lower())
        if not words:
            scores.append(0.0)
            continue
        raw_score = sum(freqs.get(w, 0.0) for w in words)
        # Normalize by sentence length so long sentences don't dominate purely
        # by word count, but keep a mild bias toward information-dense ones.
        normalized = raw_score / math.sqrt(len(words))
        # Slight positional bonus: leading sentences often carry topic info.
        position_bonus = 1.15 if idx == 0 else (1.05 if idx == 1 else 1.0)
        scores.append(normalized * position_bonus)
    return scores


def summarize(text: str, ratio: float = 0.3, max_sentences: int = None):
    sentences = split_sentences(text)
    n = len(sentences)
    if n == 0:
        return {"summary": "", "sentence_count": 0, "summary_sentence_count": 0, "sentence_breakdown": []}

    if max_sentences:
        target = max(1, min(max_sentences, n))
    else:
        target = max(1, round(n * ratio))

    if target >= n:
        return {
            "summary": " ".join(sentences),
            "sentence_count": n,
            "summary_sentence_count": n,
            "sentence_breakdown": [{"text": s, "kept": True} for s in sentences],
        }

    freqs = word_frequencies(sentences)
    scores = score_sentences(sentences, freqs)

    ranked_idx = sorted(range(n), key=lambda i: scores[i], reverse=True)[:target]
    kept_set = set(ranked_idx)
    ranked_idx.sort()  # restore original order for readability

    summary_sentences = [sentences[i] for i in ranked_idx]
    sentence_breakdown = [
        {"text": sent, "kept": i in kept_set} for i, sent in enumerate(sentences)
    ]
    return {
        "summary": " ".join(summary_sentences),
        "sentence_count": n,
        "summary_sentence_count": len(summary_sentences),
        "sentence_breakdown": sentence_breakdown,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/summarize", methods=["POST"])
def summarize_endpoint():
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("text") or "").strip()
    length_mode = data.get("length", "medium")  # short | medium | long

    if not text:
        return jsonify({"error": "Please provide some text to summarize."}), 400

    if len(WORD_RE.findall(text)) < 40:
        return jsonify({"error": "Please provide a longer passage (at least ~40 words) for a meaningful summary."}), 400

    ratio_map = {"short": 0.15, "medium": 0.3, "long": 0.5}
    ratio = ratio_map.get(length_mode, 0.3)

    result = summarize(text, ratio=ratio)

    original_words = len(WORD_RE.findall(text))
    summary_words = len(WORD_RE.findall(result["summary"]))
    reduction = round((1 - summary_words / original_words) * 100) if original_words else 0

    return jsonify({
        "summary": result["summary"],
        "sentence_breakdown": result["sentence_breakdown"],
        "original_sentence_count": result["sentence_count"],
        "summary_sentence_count": result["summary_sentence_count"],
        "original_word_count": original_words,
        "summary_word_count": summary_words,
        "reduction_percent": reduction,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
