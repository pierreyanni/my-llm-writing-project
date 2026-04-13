import os
import sys
import csv
import time
import dropbox
from pathlib import Path
from dropbox.exceptions import ApiError, AuthError, HttpError, InternalServerError
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import sanitize_filename, unique_output_path

# Configure the root paths relative to this file so it works from anywhere.
BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "documents"
METADATA_CSV = DOWNLOAD_DIR / "metadata.csv"
ALLOWED_EXTS = {".txt", ".docx", ".pptx"}
MAX_RETRIES = 5

load_dotenv()


def download_with_retry(dbx: dropbox.Dropbox, path_lower: str):
    attempt = 0
    while True:
        try:
            return dbx.files_download(path_lower)
        except (InternalServerError, HttpError) as e:
            if attempt >= MAX_RETRIES:
                raise
            sleep = 2 ** attempt
            print(f"Transient error downloading {path_lower}, retrying in {sleep}s: {e}")
            time.sleep(sleep)
            attempt += 1


def load_downloaded_ids() -> set:
    """Return the set of file IDs already recorded in metadata.csv."""
    if not METADATA_CSV.exists():
        return set()
    with METADATA_CSV.open(newline="") as f:
        reader = csv.DictReader(f)
        return {row["id"] for row in reader}


def get_access_token():
    """
    Read the Dropbox access token from an environment variable.
    Do not hardcode tokens in the file. Set DROPBOX_ACCESS_TOKEN before running.
    """
    return os.environ.get("DROPBOX_ACCESS_TOKEN")


def main():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    access_token = get_access_token()
    if not access_token:
        print("Set DROPBOX_ACCESS_TOKEN in your environment or .env before running.")
        return
    dbx = dropbox.Dropbox(access_token)

    try:
        downloaded_ids = load_downloaded_ids()
        print(f"Skipping {len(downloaded_ids)} already-downloaded file(s).")

        entries = []
        # List recursively from root; change "" to "/some/folder" to scope it
        res = dbx.files_list_folder("", recursive=True)
        entries.extend(res.entries)
        i = 0
        while res.has_more:
            res = dbx.files_list_folder_continue(res.cursor)
            entries.extend(res.entries)

            i += 1
            if i % 10 == 0:
                print(f"{len(entries)} files found so far...; iteration:{i}")

        metadata_rows = []
        for entry in entries:
            if not isinstance(entry, dropbox.files.FileMetadata):
                continue
            _, ext = os.path.splitext(entry.name)
            if ext.lower() not in ALLOWED_EXTS:
                continue

            if entry.id in downloaded_ids:
                print(f"Already downloaded, skipping: {entry.name}")
                continue

            safe_name = sanitize_filename(entry.name)
            dest_path = unique_output_path(DOWNLOAD_DIR, safe_name, entry.id)
            _, resp = download_with_retry(dbx, entry.path_lower)
            with dest_path.open("wb") as f:
                f.write(resp.content)

            metadata_rows.append({
                "id": entry.id,
                "name": entry.name,
                "downloaded_name": dest_path.name,
                "path": entry.path_display,
                "client_modified": entry.client_modified.isoformat(),
                "server_modified": entry.server_modified.isoformat(),
                "size": entry.size,
            })
            print(f"Saved: {dest_path.name}")

        if metadata_rows:
            write_header = not METADATA_CSV.exists()
            with METADATA_CSV.open("a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=metadata_rows[0].keys())
                if write_header:
                    writer.writeheader()
                writer.writerows(metadata_rows)
            print(f"Metadata updated: {METADATA_CSV}")
        print(f"Downloaded {len(metadata_rows)} new file(s) to {DOWNLOAD_DIR}")
    except AuthError:
        print("Dropbox authentication failed. Check DROPBOX_ACCESS_TOKEN.")
    except ApiError as e:
        print(f"Dropbox API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
