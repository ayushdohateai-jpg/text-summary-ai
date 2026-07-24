const inputText = document.getElementById("inputText");
const wordCountEl = document.getElementById("wordCount");
const summarizeBtn = document.getElementById("summarizeBtn");
const errorMsg = document.getElementById("errorMsg");
const passBody = document.getElementById("passBody");
const summaryPanel = document.getElementById("summaryPanel");
const summaryText = document.getElementById("summaryText");
const statRow = document.getElementById("statRow");
const copyBtn = document.getElementById("copyBtn");
const lenButtons = document.querySelectorAll(".len-btn");

let selectedLength = "medium";

function countWords(text) {
  const matches = text.trim().match(/[A-Za-z']+/g);
  return matches ? matches.length : 0;
}

inputText.addEventListener("input", () => {
  const n = countWords(inputText.value);
  wordCountEl.textContent = `${n} word${n === 1 ? "" : "s"}`;
});

lenButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    lenButtons.forEach((b) => b.classList.remove("is-active"));
    btn.classList.add("is-active");
    selectedLength = btn.dataset.len;
  });
});

function showError(message) {
  errorMsg.textContent = message;
  errorMsg.hidden = false;
}

function hideError() {
  errorMsg.hidden = true;
  errorMsg.textContent = "";
}

async function runSummarizer() {
  const text = inputText.value.trim();
  hideError();
  summaryPanel.hidden = true;

  if (!text) {
    showError("Paste some text first — the marker needs something to work on.");
    return;
  }

  summarizeBtn.disabled = true;
  const originalLabel = summarizeBtn.querySelector(".run-label").textContent;
  summarizeBtn.querySelector(".run-label").textContent = "Reading…";
  passBody.classList.add("empty-state");
  passBody.textContent = "Scanning the manuscript…";

  try {
    const res = await fetch("/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, length: selectedLength }),
    });
    const data = await res.json();

    if (!res.ok) {
      showError(data.error || "Something went wrong. Try again.");
      passBody.textContent = "Your manuscript's sentence-by-sentence edit will appear here once you run the marker.";
      return;
    }

    renderPass(data.sentence_breakdown);
    renderSummary(data);
  } catch (err) {
    showError("Couldn't reach the summarizer. Check that the server is running.");
  } finally {
    summarizeBtn.disabled = false;
    summarizeBtn.querySelector(".run-label").textContent = originalLabel;
  }
}

function renderPass(breakdown) {
  passBody.classList.remove("empty-state");
  passBody.innerHTML = "";

  breakdown.forEach((item, i) => {
    const span = document.createElement("span");
    span.className = "sentence";
    span.textContent = item.text + " ";
    span.style.opacity = "0";
    passBody.appendChild(span);

    setTimeout(() => {
      span.style.transition = "opacity 0.3s ease";
      span.style.opacity = "1";
      // After fading in, apply the kept/dropped styling as the "marker" passes.
      setTimeout(() => {
        span.classList.add(item.kept ? "kept" : "dropped");
      }, 120);
    }, i * 55);
  });
}

function renderSummary(data) {
  summaryText.textContent = data.summary;
  statRow.innerHTML = `
    <span>${data.original_sentence_count} → ${data.summary_sentence_count} sentences</span>
    <span>${data.original_word_count} → ${data.summary_word_count} words</span>
    <span>${data.reduction_percent}% shorter</span>
  `;
  summaryPanel.hidden = false;
  copyBtn.classList.remove("copied");
  copyBtn.textContent = "Copy summary";
}

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(summaryText.textContent);
    copyBtn.textContent = "Copied";
    copyBtn.classList.add("copied");
    setTimeout(() => {
      copyBtn.textContent = "Copy summary";
      copyBtn.classList.remove("copied");
    }, 1600);
  } catch (err) {
    copyBtn.textContent = "Couldn't copy";
  }
});

summarizeBtn.addEventListener("click", runSummarizer);

inputText.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
    runSummarizer();
  }
});
