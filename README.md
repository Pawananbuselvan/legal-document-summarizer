# Legal Document Summarizer

A full-stack NLP web application built with **Python, Flask, NLTK, PyPDF2, SQLite, and HTML/CSS/JS** that extracts text from legal PDFs and generates extractive summaries with persistent history tracking.

## Features
- **PDF & Text Extraction:** Parses multi-page legal documents using `PyPDF2`.
- **Extractive NLP Summarization:** Uses `NLTK` tokenization and word-frequency scoring to rank and extract key sentences offline.
- **Persistent SQLite Storage:** Logs uploaded filenames, word counts, and generated summaries in `SQLite` for instant history retrieval.

## Setup & Local Execution
1. Clone the repository:
   ```bash
   git clone [https://github.com/Pawananbuselvan/legal-document-summarizer.git](https://github.com/Pawananbuselvan/legal-document-summarizer.git)
   cd legal-document-summarizer

2.INSTALL DEPENDENCIES:
  ```
  pip install flask pypdf2 nltk
```

3.RUN APPLICATION
```
python app.py
```
Open http://127.0.0.1:5000 in your browser.

