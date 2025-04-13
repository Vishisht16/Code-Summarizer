import logging


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler()) 

from .repo_downloader import clone_repo
from .language_parsers import extract_code_snippets, get_language_by_extension, SUPPORTED_EXTENSIONS
from .summarizer import summarize_repo, summarize_file, get_embedding, generate_summary
from .firebase_db import upload_summary_to_firebase, get_summaries_by_repo, is_firestore_available

VERSION = "0.1.0"

__all__ = [
    "clone_repo",
    "extract_code_snippets",
    "get_language_by_extension",
    "SUPPORTED_EXTENSIONS",
    "summarize_repo",
    "summarize_file",
    "get_embedding",
    "generate_summary",
    "upload_summary_to_firebase",
    "get_summaries_by_repo",
    "is_firestore_available",
    "VERSION"
]

log.info(f"Code Summarizer Package v{VERSION} initialized.")