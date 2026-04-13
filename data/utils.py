from pathlib import Path


def sanitize_filename(file_name: str) -> str:
    """Return a filesystem-safe filename while preserving readable names."""
    cleaned = "".join(c for c in file_name if c.isalnum() or c in (" ", ".", "_", "-")).strip()
    return cleaned or "untitled"


def unique_output_path(download_path: Path, base_name: str, file_id: str) -> Path:
    """Avoid accidental overwrites when two files share the same name."""
    candidate = download_path / base_name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    return download_path / f"{stem}_{file_id[:8]}{suffix}"
