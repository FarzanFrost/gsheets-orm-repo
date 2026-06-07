import urllib.parse
import os
from typing import Tuple
import google.auth
from google.oauth2 import service_account
import gspread

from gsheets_orm.exceptions import DialectError

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def parse_uri(uri: str) -> Tuple[str, str]:
    if not uri.startswith("gsheets://"):
        raise DialectError("Invalid connection URI scheme. Must start with 'gsheets://'")
    
    parsed = urllib.parse.urlparse(uri)
    params = urllib.parse.parse_qs(parsed.query)
    
    spreadsheet_id = params.get("spreadsheet_id", [None])[0]
    if not spreadsheet_id:
        raise DialectError("Connection URI must specify 'spreadsheet_id' query parameter")
    
    # Extract credentials file path
    # e.g., gsheets://credentials.json?spreadsheet_id=XYZ
    creds_path = parsed.netloc + parsed.path
    return creds_path, spreadsheet_id

class Engine:
    def __init__(self, uri: str):
        self.uri = uri
        self.creds_path, self.spreadsheet_id = parse_uri(uri)
        self._client = None
        self._spreadsheet = None

    @property
    def client(self) -> gspread.Client:
        if self._client is None:
            self.authenticate()
        return self._client

    @property
    def spreadsheet(self) -> gspread.Spreadsheet:
        if self._spreadsheet is None:
            try:
                self._spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            except Exception as e:
                raise DialectError(f"Failed to open spreadsheet '{self.spreadsheet_id}': {e}")
        return self._spreadsheet

    def authenticate(self):
        try:
            if self.creds_path == "oauth" or not self.creds_path or not os.path.exists(self.creds_path):
                # Fallback to standard application default credentials (OAuth2 / GCP context)
                creds, _ = google.auth.default(scopes=SCOPES)
            else:
                creds = service_account.Credentials.from_service_account_file(
                    self.creds_path, scopes=SCOPES
                )
            self._client = gspread.authorize(creds)
        except Exception as e:
            raise DialectError(f"Authentication failed: {e}")

def create_engine(uri: str) -> Engine:
    return Engine(uri)
