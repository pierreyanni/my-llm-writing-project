import os
import csv
import dropbox
from pathlib import Path

# Configure the root paths relative to this file so it works from anywhere.
BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "documents"
METADATA_CSV = DOWNLOAD_DIR / "metadata.csv"
ALLOWED_EXTS = {".txt", ".docx", ".pptx"}

def get_access_token():
    """
    Read the Dropbox access token from an environment variable.
    Do not hardcode tokens in the file. Set DROPBOX_ACCESS_TOKEN before running.
    """
    token = os.environ.get("DROPBOX_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("Set DROPBOX_ACCESS_TOKEN in your environment before running.")
    return token

def main():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    access_token = get_access_token()
    dbx = dropbox.Dropbox(access_token)

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

        dest_path = DOWNLOAD_DIR / entry.name
        md, resp = dbx.files_download(entry.path_lower)
        with dest_path.open("wb") as f:
            f.write(resp.content)

        metadata_rows.append({
            "id": entry.id,
            "name": entry.name,
            "path": entry.path_display,
            "client_modified": entry.client_modified.isoformat(),
            "server_modified": entry.server_modified.isoformat(),
            "size": entry.size,
        })

    if metadata_rows:
        with METADATA_CSV.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=metadata_rows[0].keys())
            writer.writeheader()
            writer.writerows(metadata_rows)
        print(f"Metadata written to {METADATA_CSV}")
    print(f"Downloaded {len(metadata_rows)} files to {DOWNLOAD_DIR}")

if __name__ == "__main__":
    main()
