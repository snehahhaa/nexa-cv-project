"""
utils.py - Shared Utility Functions
Miscellaneous helpers used across the AI Resume Analyzer application.
"""

import re
import os
from pathlib import Path
from typing import List, Optional


# ── Text helpers ──────────────────────────────────────────────────────────────
def sanitize_text(text: str, max_length: int = 10_000) -> str:
    """
    Remove control characters and excessive whitespace from raw text.
    Optionally truncate to max_length characters.
    """
    if not text:
        return ""
    # Remove null bytes and other control characters (except newline/tab)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Collapse repeated blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    if max_length and len(text) > max_length:
        text = text[:max_length] + "\n…[truncated]"
    return text


def format_bullet_list(items: List[str], prefix: str = "•") -> str:
    """Convert a list of strings into a bullet-point string."""
    return "\n".join(f"{prefix} {item}" for item in items if item.strip())


def truncate(text: str, max_chars: int = 200, suffix: str = "…") -> str:
    """Truncate text to max_chars, appending suffix if truncated."""
    if not text or len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + suffix


# ── CSS helpers ───────────────────────────────────────────────────────────────
def load_css(filepath: str) -> str:
    """
    Read a CSS file from disk and return its contents.
    Returns empty string if file not found.
    """
    path = Path(filepath)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


# ── Score utilities ───────────────────────────────────────────────────────────
def score_to_color(score: int) -> str:
    """Return a hex colour string based on a 0-100 score."""
    if score >= 70:
        return "#22c55e"   # green
    if score >= 40:
        return "#f59e0b"   # amber
    return "#ef4444"       # red


def score_to_label(score: int) -> str:
    """Return a human-readable label for a 0-100 score."""
    if score >= 80: return "Excellent"
    if score >= 65: return "Good"
    if score >= 50: return "Average"
    if score >= 35: return "Below Average"
    return "Poor"


# ── File helpers ──────────────────────────────────────────────────────────────
def ensure_dir(path: str) -> Path:
    """Create directory (and parents) if it does not exist. Return Path object."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_filename(name: str) -> str:
    """Replace characters that are unsafe in filenames."""
    return re.sub(r"[^\w\s\-.]", "_", name).strip()


# ── Environment helpers ───────────────────────────────────────────────────────
def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve an environment variable with an optional default."""
    return os.environ.get(key, default)


def check_api_key() -> bool:
    """Return True if GOOGLE_API_KEY is set in the environment."""
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    return bool(key) and key != "your_google_api_key_here"


# ── List utilities ────────────────────────────────────────────────────────────
def deduplicate(items: List[str]) -> List[str]:
    """Remove duplicates while preserving order, case-insensitively."""
    seen = set()
    result = []
    for item in items:
        lower = item.lower()
        if lower not in seen:
            seen.add(lower)
            result.append(item)
    return result


def chunk_list(lst: list, size: int) -> list:
    """Split a list into chunks of at most `size` elements."""
    return [lst[i:i+size] for i in range(0, len(lst), size)]
