import os
import io
import time
import csv
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

RETRYABLE_REASONS = {"userRateLimitExceeded", "rateLimitExceeded"}
MAX_RETRIES = 5

# Only download text-like formats
ALLOWED_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
    "text/plain",  # .txt
    "application/vnd.google-apps.document",  # Google Docs (export to .docx)
    "application/vnd.google-apps.presentation",  # Google Slides (export to .pptx)
}

# --- Configuration ---
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
# The folder where your files will be downloaded.
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_PATH = BASE_DIR / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"
DOWNLOAD_PATH = BASE_DIR / "documents"
METADATA_CSV = DOWNLOAD_PATH / "metadata.csv"
# --- End Configuration ---

# MimeTypes for converting Google Docs, Sheets, and Slides for export
GOOGLE_DOCS_MIMETYPES = {
    "application/vnd.google-apps.document": {
        "extension": ".docx",
        "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
    "application/vnd.google-apps.spreadsheet": {
        "extension": ".xlsx",
        "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    },
    "application/vnd.google-apps.presentation": {
        "extension": ".pptx",
        "mimetype": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    },
    "application/vnd.google-apps.drawing": {
        "extension": ".png",
        "mimetype": "image/png"
    },
}

def authenticate():
    """Handles user authentication and returns service credentials."""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with TOKEN_PATH.open("w") as token:
            token.write(creds.to_json())
    return creds

def download_file(service, file_id, file_name, mime_type, download_path):
    """Downloads a single file from Google Drive, handling exports for Google Docs."""
    # Sanitize file name to prevent path issues
    sanitized_name = "".join(c for c in file_name if c.isalnum() or c in (' ', '.', '_')).rstrip()

    # Handle Google Docs, Sheets, Slides by exporting them to a standard format
    if mime_type in GOOGLE_DOCS_MIMETYPES:
        export_details = GOOGLE_DOCS_MIMETYPES[mime_type]
        request = service.files().export_media(
            fileId=file_id, mimeType=export_details["mimetype"]
        )
        file_name_with_ext = f"{sanitized_name}{export_details['extension']}"
    # Handle all other standard file types
    else:
        request = service.files().get_media(fileId=file_id)
        file_name_with_ext = sanitized_name

    file_path = download_path / file_name_with_ext
    
    # Perform the download with progress indication
    with file_path.open("wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        attempt = 0
        done = False
        while not done:
            try:
                status, done = downloader.next_chunk()
            except HttpError as e:
                reason = getattr(e, "resp", None)
                reason = e.error_details[0]["reason"] if getattr(e, "error_details", None) else ""
                if reason in RETRYABLE_REASONS and attempt < MAX_RETRIES:
                    sleep = 2 ** attempt
                    print(f"  Rate limited, retrying in {sleep}s...")
                    time.sleep(sleep)
                    attempt += 1
                    continue
                raise
                
            if status:
                print(f"  Download {int(status.progress() * 100)}%.", end='\r')
            


def main():
    """
    Authenticates with Google Drive, finds all files authored by the user,
    and downloads them to a local directory.
    """
    try:
        creds = authenticate()
        service = build("drive", "v3", credentials=creds)

        # Create download directory if it doesn't exist
        DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
        METADATA_CSV.parent.mkdir(parents=True, exist_ok=True)
        print(f"Download directory: {DOWNLOAD_PATH}")

        page_token = None
        file_count = 0
        metadata_rows = []
        while True:
            # API call to list files. The query "'me' in owners" is the key part.
            mime_filters = " or ".join([f"mimeType='{m}'" for m in ALLOWED_MIME_TYPES])
            response = (
                service.files()
                .list(
                    q=f"'me' in owners and trashed=false and ({mime_filters})",
                    spaces="drive",
                    fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, size)",
                    pageToken=page_token,
                )
                .execute()
            )
            
            files = response.get("files", [])
            if not files:
                print("No files found.")
                break

            for file_item in files:
                file_id = file_item.get("id")
                file_name = file_item.get("name")
                mime_type = file_item.get("mimeType")
                
                if mime_type not in ALLOWED_MIME_TYPES:
                    print(f"Skipping {file_name} ({mime_type})")
                    continue

                # Skip folders and apps, as they cannot be downloaded directly
                if mime_type in ['application/vnd.google-apps.folder', 'application/vnd.google-apps.site']:
                    continue
                
                file_count += 1
                print(f"Processing file {file_count}: {file_name} ({mime_type})")
                download_file(service, file_id, file_name, mime_type, DOWNLOAD_PATH)
                metadata_rows.append(
                    {
                        "id": file_id,
                        "name": file_name,
                        "mimeType": mime_type,
                        "createdTime": file_item.get("createdTime"),
                        "modifiedTime": file_item.get("modifiedTime"),
                        "size": file_item.get("size"),
                    }
                )

            page_token = response.get("nextPageToken", None)
            if page_token is None:
                break
        
        if metadata_rows:
            with METADATA_CSV.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=metadata_rows[0].keys())
                writer.writeheader()
                writer.writerows(metadata_rows)
            print(f"Metadata written to: {METADATA_CSV}")

        print(f"Finished. Downloaded a total of {file_count} files.")

    except HttpError as error:
        print(f"An error occurred: {error}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
