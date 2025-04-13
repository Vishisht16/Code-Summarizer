import torch
from transformers import RobertaTokenizer, RobertaModel, logging as hf_logging
from typing import List, Dict, Optional

from code_summarizer.language_parsers import extract_code_snippets, SUPPORTED_EXTENSIONS
from pathlib import Path
import numpy as np
import logging

log = logging.getLogger(__name__)
hf_logging.set_verbosity_error()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
log.info(f"Summarizer using device: {device}")
MODEL_LOADED = False
tokenizer = None
model = None

try:
    log.info("Loading CodeBERT tokenizer/model...")
    tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
    model = RobertaModel.from_pretrained("microsoft/codebert-base")
    model = model.to(device)
    model.eval()
    MODEL_LOADED = True
    log.info("CodeBERT model loaded successfully.")
except Exception as e:
    log.error(f"Failed to load CodeBERT model: {e}", exc_info=True)

def get_embedding(code: str) -> Optional[List[float]]:
    if not MODEL_LOADED or tokenizer is None or model is None:
        return None
    try:
        inputs = tokenizer(code, return_tensors="pt", truncation=True, max_length=512, padding=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
        embedding = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
        return embedding.tolist()
    except Exception as e:
        log.warning(f"Failed to generate embedding: {e}. Snippet start: {code[:50]}...")
        return None

def generate_summary(snippet: str) -> str:
    try:
        lines = snippet.strip().split('\n')
        header = next((line.strip() for line in lines if line.strip() and not (line.strip().startswith('#') or line.strip().startswith('//') or line.strip().startswith('/*'))), "")
        header = (header[:100] + "...") if len(header) > 100 else header
        return f"Function/method starting with `{header}`." if header else "N/A Summary"
    except Exception:
        return "Summary generation failed."

def summarize_file(file_path: Path, repo_url: str) -> List[Dict]:
    language, snippets = extract_code_snippets(file_path)
    if not snippets:
        return []

    results = []
    log.debug(f"Summarizing {len(snippets)} snippets from {file_path}...")
    for snippet in snippets:
        if not snippet or snippet.isspace():
            continue
        embedding = get_embedding(snippet)
        summary = generate_summary(snippet)
        summary_data = {
            "repo_url": repo_url,
            "file_path": str(file_path.as_posix()),
            "language": language,
            "function_code": snippet,
            "summary": summary,
        }
        if embedding is not None:
             summary_data["embedding"] = embedding
        results.append(summary_data)
    return results

def summarize_repo(repo_dir: Path, repo_url: str) -> List[Dict]:
    all_results = []
    log.info(f"Starting summarization for repository: {repo_url}")
    supported_extensions = set(SUPPORTED_EXTENSIONS.keys())
    files_processed_count = 0

    for file in repo_dir.rglob("*"):
        if file.is_file() and file.suffix.lower() in supported_extensions:
            log.debug(f"Processing file: {file}")
            try:
                file_results = summarize_file(file, repo_url)
                if file_results:
                    all_results.extend(file_results)
                    files_processed_count += 1
            except Exception as e:
                log.error(f"Failed to process file {file}: {e}", exc_info=True)

    log.info(f"Summarization complete for {repo_url}. Processed {files_processed_count} files, found {len(all_results)} functions.")
    return all_results