"""sports_words.py - Custom project script.

Author: Josiah Davis
Date: 2026-10

Purpose

  Retrieve the Wikipedia article on sports betting, clean the text,
  count word frequencies, and save the charts to docs/images.

Analytical Questions

- What terms dominate a general article about sports betting?
- Do league acronyms like NFL, NBA, and MLB show up once short words are kept?
- How much noise is left after removing filler words?

Changes from the example

- Different page (Sports betting instead of Natural language processing).
- Strips punctuation BEFORE checking length, so "nfl," and "nfl" count the same way.
- Keeps 3-letter words (len > 2) so league acronyms survive (from my D2 experiment).
- Removes a stop word list of filler words and Wikipedia page junk.
- Drops tokens that are only digits (years, page numbers).
- Saves the bar chart and word cloud as PNG files for the docs.

Run from root project folder with:

  uv run python -m nlp.sports_words
"""

# ============================================================
# Section 1. Setup and Imports
# ============================================================
import logging
from pathlib import Path

from bs4 import BeautifulSoup
from datafun_toolkit.logger import get_logger, log_header
import matplotlib.pyplot as plt
import polars as pl
import requests
from wordcloud import WordCloud

LOG: logging.Logger = get_logger("CI", level="DEBUG")
log_header(LOG, "NLP")
LOG.info("START sports_words script.....")

# Charts are saved here so they can display on the docs site.
IMAGES_PATH: Path = Path.cwd() / "docs" / "images"
IMAGES_PATH.mkdir(parents=True, exist_ok=True)

# ============================================================
# Section 2. Retrieve the Web Page
# ============================================================
url: str = "https://en.wikipedia.org/wiki/Sports_betting"

headers: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (compatible; NLP-Course-Example/1.0)"
}

response = requests.get(url, headers=headers, timeout=30)
response.raise_for_status()
html: str = response.text

print(f"Downloaded {len(html):,} characters from:")
print(url)

# ============================================================
# Section 3. Parse HTML and Extract Visible Text
# ============================================================
soup: BeautifulSoup = BeautifulSoup(html, "lxml")
text: str = soup.get_text(separator=" ", strip=True)

# ============================================================
# Section 4. Clean the Text
# ============================================================

# Filler words plus Wikipedia page junk seen in the baseline run
# (edit, retrieved, archived, isbn, etc.).
STOP_WORDS: set[str] = {
    "the",
    "and",
    "for",
    "that",
    "from",
    "with",
    "this",
    "are",
    "was",
    "were",
    "has",
    "have",
    "had",
    "its",
    "which",
    "such",
    "also",
    "can",
    "not",
    "but",
    "been",
    "their",
    "they",
    "into",
    "other",
    "more",
    "than",
    "these",
    "some",
    "any",
    "may",
    "all",
    "one",
    "who",
    "his",
    "her",
    "you",
    "your",
    "our",
    "there",
    "when",
    "where",
    "what",
    "how",
    "most",
    "many",
    "only",
    "between",
    "about",
    "would",
    "will",
    "e.g",
    "i.e",
    "edit",
    "retrieved",
    "archived",
    "original",
    "isbn",
    "doi",
    "pdf",
    "wikipedia",
    "article",
    "page",
    "see",
}

words: list[str] = [word.lower() for word in text.split()]
print(f"Total raw words: {len(words):,}")

# Strip punctuation first, then filter.
stripped: list[str] = [word.strip(".,:;!?()[]\"'") for word in words]
clean_words: list[str] = [
    word
    for word in stripped
    if len(word) > 2 and word not in STOP_WORDS and not word.isdigit()
]
print(f"Total cleaned words: {len(clean_words):,}")

# ============================================================
# Section 5. Frequency Table with Polars
# ============================================================
df: pl.DataFrame = pl.DataFrame({"word": clean_words})
freq_df: pl.DataFrame = df.group_by("word").len().sort("len", descending=True)

print("Top 20 most frequent words:")
with pl.Config(tbl_rows=20):
    print(freq_df.head(20))

# ============================================================
# Section 6. Bar Chart (saved to docs/images)
# ============================================================
top_df: pl.DataFrame = freq_df.head(15)

plt.figure(figsize=(10, 5))
plt.bar(top_df["word"], top_df["len"])
ax = plt.gca()
ax.tick_params(axis="x", labelrotation=45)
plt.title("Sports Betting: Top 15 Words (stop words removed)")
plt.xlabel("Word")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig(IMAGES_PATH / "sports_top_words.png")
plt.show()

# ============================================================
# Section 7. Word Cloud (saved to docs/images)
# ============================================================
freq_dict: dict[str, int] = dict(
    zip(freq_df["word"].to_list(), freq_df["len"].to_list(), strict=True)
)

wc: WordCloud = WordCloud(width=1000, height=500, background_color="white")
wc.generate_from_frequencies(freq_dict)

plt.figure(figsize=(12, 6))
plt.imshow(wc)
plt.axis("off")
plt.title("Sports Betting Word Cloud")
plt.savefig(IMAGES_PATH / "sports_word_cloud.png")
plt.show()

# ============================================================
# Log the end
# ============================================================
LOG.info("========================")
LOG.info("Pipeline executed successfully!")
LOG.info("========================")
LOG.info("END sports_words")
