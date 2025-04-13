import sys
import argparse
import gradio as gr
import json
import logging
import time
from pathlib import Path

from code_summarizer import (
    clone_repo,
    summarize_repo,
    upload_summary_to_firebase,
    get_summaries_by_repo,
    is_firestore_available
)
from code_summarizer.summarizer import device as summarizer_device, MODEL_LOADED as SUMMARIZER_LOADED

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
log = logging.getLogger(__name__)

REPO_CLONE_DIR_CLI = "cloned_repo_cli"
REPO_CLONE_DIR_GRADIO = "cloned_repo_gradio"
OUTPUT_DIR = Path("outputs")
OUTPUT_FILE = OUTPUT_DIR / "summaries.json"

def format_summaries_for_display(summaries: list) -> str:
    if not summaries: return "No summaries generated."
    limit = 5
    output = f"Found {len(summaries)} functions.\n"
    output += f"Firestore: {'Yes' if is_firestore_available() else 'No'}\n---\n"
    for i, summary in enumerate(summaries[:limit]):
         output += f"File: {summary.get('file_path', '?')}\nLang: {summary.get('language', '?')}\n"
         output += f"Summary: {summary.get('summary', '?')}\n"
         output += f"Embedding: {'Yes' if 'embedding' in summary else 'No'}\n---\n"
    if len(summaries) > limit:
        output += f"... and {len(summaries) - limit} more."
    return output

def summarize_from_url(repo_url: str):
    """Gradio action: Clones, summarizes, uploads, yields status updates."""
    log.info(f"Gradio request for URL: {repo_url}")
    if not repo_url or not repo_url.startswith("https"):
        yield "❌ Invalid HTTPS GitHub URL."
        return

    if not SUMMARIZER_LOADED:
         yield "❌ Summarizer Model Not Loaded. Cannot proceed."
         log.error("Gradio: Summarizer model not loaded.")
         return

    firestore_ready = is_firestore_available()
    if not firestore_ready:
        log.warning("Gradio: Firebase is not available.")

    yield "⏳ Cloning repository..."
    clone_dir_path = Path(REPO_CLONE_DIR_GRADIO)
    if not clone_repo(repo_url, str(clone_dir_path)):
        yield "❌ Failed to clone repo."
        log.error(f"Gradio: Failed to clone {repo_url}")
        return

    yield f"⏳ Summarizing code (using {summarizer_device})..."
    summaries = summarize_repo(clone_dir_path, repo_url)
    if not summaries:
        yield "⚠️ Repo cloned, but no functions found."
        log.warning(f"Gradio: No functions found in {repo_url}")
        return

    status = f"✅ Summarized {len(summaries)} functions."
    yield status + " Uploading to Firebase..."

    upload_count = 0
    if firestore_ready:
        for summary in summaries:
            try:
                upload_summary_to_firebase(summary)
                upload_count += 1
            except Exception as e:
                log.error(f"Gradio: Firebase upload error: {e}")
        status += f" Uploaded {upload_count} to Firebase."
        log.info(f"Gradio: Uploaded {upload_count} summaries for {repo_url}")
        yield status + "\n---\n" + format_summaries_for_display(summaries)
    else:
        status += " Firebase unavailable, skipping upload."
        log.warning(f"Gradio: Skipped Firebase upload for {repo_url}")
        yield status + "\n---\n" + format_summaries_for_display(summaries)

def perform_web_search(query: str):
    """Gradio action: Placeholder for web search."""
    log.info(f"Gradio: Web search placeholder: {query}")
    # Placeholder - Replace with actual search implementation
    return f"🔎 Web search (placeholder) for: '{query}'"

def run_pipeline(repo_url: str, skip_existing: bool = False, save_local: bool = True):
    """CLI action: Runs the full pipeline."""
    start_time = time.time()
    log.info(f"CLI: Pipeline starting for: {repo_url}")

    if not SUMMARIZER_LOADED:
         log.error("CLI: Summarizer Model Not Loaded. Exiting.")
         sys.exit(1)

    firestore_ready = is_firestore_available()
    if not firestore_ready:
        log.warning("CLI: Firebase is not available. Uploads/Checks will be skipped.")

    if skip_existing and firestore_ready:
        log.info("CLI: Checking for existing summaries...")
        if get_summaries_by_repo(repo_url):
            log.warning("CLI: Skipping. Found existing summaries in Firebase.")
            return

    log.info("CLI: Cloning repository...")
    clone_dir_path = Path(REPO_CLONE_DIR_CLI)
    if not clone_repo(repo_url, str(clone_dir_path)):
        log.error("CLI: Repo cloning failed. Exiting.")
        sys.exit(1)

    log.info(f"CLI: Running summarization (device: {summarizer_device})...")
    summaries = summarize_repo(clone_dir_path, repo_url)
    if not summaries:
        log.warning("CLI: No functions found or summarization failed.")
        return

    log.info(f"CLI: Summarization complete. Found {len(summaries)} functions.")

    if firestore_ready:
        log.info(f"CLI: Uploading {len(summaries)} summaries to Firebase...")
        upload_count = 0
        for i, summary in enumerate(summaries):
            upload_summary_to_firebase(summary)
            upload_count +=1
            if (i + 1) % 100 == 0:
                 log.info(f"CLI:   Uploaded {i+1}/{len(summaries)}...")
        log.info(f"CLI: Finished uploading {upload_count} summaries.")
    else:
        log.info("CLI: Skipping Firebase upload.")

    if save_local:
        log.info(f"CLI: Saving summaries locally to {OUTPUT_FILE}...")
        try:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
                json.dump(summaries, f, indent=2, default=str)
            log.info(f"CLI: Saved local backup to {OUTPUT_FILE}")
        except Exception as e:
            log.error(f"CLI: Failed to save local backup: {e}", exc_info=True)

    duration = time.time() - start_time
    log.info(f"CLI: ✅ Pipeline completed in {duration:.2f} seconds.")

if not SUMMARIZER_LOADED:
     log.error("Summarizer model failed to load. Gradio interface may be limited or fail.")
if not is_firestore_available():
     log.warning("Firebase is not available. Upload/check functionality will be disabled in Gradio interface.")

with gr.Blocks(title="Code Summarizer", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🔍 Code Summarizer & Search")

    with gr.Tab("Repo Summarizer"):
        repo_url_input = gr.Textbox(label="GitHub Repo URL", placeholder="https://github.com/user/repo")
        summarize_button = gr.Button("Summarize & Upload", variant="primary")
        status_output = gr.Textbox(label="Status / Output", lines=10, interactive=False)
        summarize_button.click(fn=summarize_from_url, inputs=repo_url_input, outputs=status_output)

    with gr.Tab("Web Code Search (Placeholder)"):
        search_query_input = gr.Textbox(label="Search Query", placeholder="e.g., binary search tree cpp")
        search_button = gr.Button("Search Web", variant="secondary")
        search_output_display = gr.Textbox(label="Web Search Results", lines=5, interactive=False)
        search_button.click(fn=perform_web_search, inputs=search_query_input, outputs=search_output_display)


if __name__ == "__main__":
    if len(sys.argv) > 1 and "--url" in sys.argv:
        parser = argparse.ArgumentParser(
            description="Code Summarizer CLI.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument(
            "--url",
            required=True,
            help="HTTPS URL of the public GitHub repository."
        )
        parser.add_argument(
            "--skip_existing",
            action="store_true",
            help="Skip if repo already summarized in Firebase."
        )
        parser.add_argument(
            "--no_save",
            action="store_true",
            help="Disable saving local summaries.json."
        )

        try:
            args = parser.parse_args()
            log.info("Running in CLI mode.")
            run_pipeline(
                repo_url=args.url,
                skip_existing=args.skip_existing,
                save_local=not args.no_save
            )
        except SystemExit as e:
            if e.code != 0:
                log.error(f"Argument parsing error (Exit Code: {e.code}). Ensure --url is provided for CLI mode.")
            sys.exit(e.code)
    else:
        log.info("Launching Gradio UI...")
        demo.launch()
