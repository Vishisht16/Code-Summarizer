# Code Summarizer Search

> Automated code understanding and search from GitHub repositories using CodeBERT and Firebase.

This tool clones public GitHub repositories, parses code across multiple languages, extracts functions or methods, generates embeddings using CodeBERT, and stores structured metadata in Firebase Firestore. It offers both a Gradio-based web interface and a CLI for flexible usage.

[![Hugging Face Spaces](https://img.shields.io/badge/Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/Vishisht16/code-summarizer) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Input Source

The input is a public GitHub repository URL. Examples:

```
https://github.com/pallets/flask
https://github.com/gradio-app/gradio
```

---

## How It Works

### Pipeline Overview:

```
GitHub URL → Git Clone
          → Code File Iteration (.py, .js, .java, .cpp, etc.)
            → Function/Method Extraction
              → CodeBERT Embedding
                → Summary Generation
                  → Firebase Firestore Storage
```

### Components:
- **Git Cloning:** Uses GitPython to clone public repositories.
- **Language Parsing:** Python AST for Python, Regex-based parsing for others (JavaScript, Java, C/C++, etc.).
- **Embedding:** Uses `microsoft/codebert-base` from Hugging Face Transformers.
- **Summarization:** Generates simple template-based summaries.
- **Storage:** Results are stored in Firebase Firestore for future querying and integration.

---

## Features

- Automatic cloning of GitHub repositories
- Support for multiple programming languages: Python, JavaScript, Java, C/C++, C#, TypeScript, Go
- Function-level embeddings using CodeBERT
- Simple summarization of code components
- Firebase Firestore integration for structured storage
- Web interface via Gradio (compatible with Hugging Face Spaces)
- CLI for advanced usage and automation

---

## Live Demo

Try the hosted version on Hugging Face Spaces:

[Live Demo](https://huggingface.co/spaces/Vishisht16/code-summarizer)

_Note: Initial load may take a few seconds due to free tier limitations._

---

## Model Used

- **Model:** `microsoft/codebert-base`
- **Framework:** Hugging Face Transformers
- The model is downloaded automatically when the application runs

```python
from transformers import RobertaTokenizer, RobertaModel

model = RobertaModel.from_pretrained("microsoft/codebert-base")
tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
```

---

## How to Run

### Run Online

Visit the Hugging Face Space:
```
https://huggingface.co/spaces/Vishisht16/code-summarizer
```

### Run Locally

```bash
# Clone the repository
https://github.com/Vishisht/Code-Summarizer.git
cd Code-Summarizer

# Set up environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Firebase Setup (for local use)

- Create a directory named `firebase_config/`
- Place the `serviceAccountKey.json` inside it
- This file is ignored via `.gitignore` and should never be committed

### Launch the Web Interface
```bash
python app.py
```
Visit the localhost URL (e.g., http://127.0.0.1:7860)

### Run in CLI Mode
```bash
# Basic
python app.py --url https://github.com/pallets/flask

# Skip if already summarized
python app.py --url https://github.com/pallets/flask --skip_existing

# Skip local JSON save
python app.py --url https://github.com/pallets/flask --no_save
```

---

## Hugging Face Deployment

Set the Firebase key as a secret:
- **Key:** `FIREBASE_SERVICE_ACCOUNT_JSON`
- **Value:** Full content of `serviceAccountKey.json`

This allows the app to work with Firestore in Spaces securely.

---

## Project Structure

```
YourRepoName/
├── app.py                  # Entry point (Gradio UI + CLI)
├── core.py                 # Core pipeline logic
├── requirements.txt
├── README.md
├── LICENSE
│
├── code_summarizer/
│   ├── __init__.py
│   ├── repo_downloader.py
│   ├── language_parsers.py
│   ├── summarizer.py
│   ├── firebase_db.py
│
├── firebase_config/        # Ignored in Git
│   └── serviceAccountKey.json
│
└── outputs/                # Output summaries (optional, local only)
    └── summaries.json
```

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
