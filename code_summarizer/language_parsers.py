import os
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import re
import ast
import logging

log = logging.getLogger(__name__)

# Note: ast.get_source_segment requires Python 3.8+
SUPPORTED_EXTENSIONS: Dict[str, str] = {
    ".py": "python", ".js": "javascript", ".java": "java", ".cpp": "cpp",
    ".c": "c", ".cs": "csharp", ".ts": "typescript", ".go": "go"
}

# Regex patterns (simplified, may need adjustment per language)
# WARNING: Regex-based parsing is fragile.
patterns = {
    "javascript": r"^(?:async\s+)?function\s+\w+\s*\([^)]*\)\s*\{[\s\S]*?^\}|(?:export\s+)?(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{[\s\S]*?^\}",
    "typescript": r"^(?:async\s+)?function\s+\w+\s*\([^)]*\)\s*\{[\s\S]*?^\}|(?:export\s+)?(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{[\s\S]*?^\}",
    "java": r"^(?:public|private|protected|static|\s)*\s*[\w<>\[\]]+\s+\w+\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{[\s\S]*?^\}",
    "cpp": r"^(?:[\w:]+)\s+\**\s*[\w:]+\s*\([^)]*\)\s*(?:const)?\s*\{[\s\S]*?^\}",
    "c": r"^(?:[\w:]+)\s+\**\s*[\w:]+\s*\([^)]*\)\s*(?:const)?\s*\{[\s\S]*?^\}",
    "csharp": r"^(?:public|private|protected|internal|static|virtual|async|override|\s)*\s*[\w<>\[\],?]+\s+\w+\s*\([^)]*\)\s*\{[\s\S]*?^\}",
    "go": r"^func(?:\s*\(\s*\w+\s+\*?\w+\s*\))?\s+\w+\s*\([^)]*\)\s*(?:[\w\s,()]+)?\s*\{[\s\S]*?^\}"
}

def get_language_by_extension(file_path: Path) -> Optional[str]:
    return SUPPORTED_EXTENSIONS.get(file_path.suffix.lower())

def extract_python_functions(file_path: Path) -> List[str]:
    functions = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        tree = ast.parse(source, filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                try:
                    segment = ast.get_source_segment(source, node)
                    if segment:
                        functions.append(segment)
                except Exception: # Ignore segment extraction errors
                    pass
    except (FileNotFoundError, SyntaxError, UnicodeDecodeError) as e:
        log.warning(f"Skipping file {file_path} due to parsing error: {e}")
    except Exception as e:
        log.error(f"Unexpected error parsing Python file {file_path}: {e}", exc_info=True)
    return functions

def extract_functions_by_regex(file_path: Path, pattern: str) -> List[str]:
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        return re.findall(pattern, code, re.DOTALL | re.MULTILINE)
    except (FileNotFoundError, UnicodeDecodeError) as e:
         log.warning(f"Skipping file {file_path} due to read error: {e}")
         return []
    except Exception as e:
        log.error(f"Failed regex extraction on {file_path}: {e}", exc_info=True)
        return []

def extract_code_snippets(file_path: Path) -> Tuple[Optional[str], List[str]]:
    language = get_language_by_extension(file_path)
    if language is None:
        return None, []

    if language == "python":
        return language, extract_python_functions(file_path)

    pattern = patterns.get(language)
    if pattern:
        return language, extract_functions_by_regex(file_path, pattern)
    else:
        log.debug(f"No regex pattern defined for language: {language} in file {file_path}")
        return language, []