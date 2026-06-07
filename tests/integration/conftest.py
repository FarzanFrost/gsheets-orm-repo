import os
import pytest
import gspread
from google.oauth2 import service_account
from gsheets_orm import create_engine, Session

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

INTEGRATION_SHEET_PREFIX = "Integration"


def _delete_integration_worksheets(spreadsheet: gspread.Spreadsheet) -> None:
    """Delete all worksheets whose title starts with INTEGRATION_SHEET_PREFIX.

    Google Sheets requires at least one worksheet to exist at all times.
    A temporary placeholder sheet is added before deletion to satisfy that
    constraint, then removed afterwards.
    """
    worksheets = spreadsheet.worksheets()
    targets = [ws for ws in worksheets if ws.title.startswith(INTEGRATION_SHEET_PREFIX)]

    if not targets:
        return

    # Add a temporary placeholder so we never hit the "last sheet" constraint.
    placeholder = spreadsheet.add_worksheet(title="_cleanup_placeholder", rows=1, cols=1)

    for ws in targets:
        spreadsheet.del_worksheet(ws)

    spreadsheet.del_worksheet(placeholder)


@pytest.fixture(scope="session", autouse=True)
def cleanup_integration_sheets():
    """Wipe Integration* worksheets before and after the full test session.

    Runs unconditionally (autouse) so the sheet is always in a clean state
    at the start of every CI run, even when the previous run failed mid-way.
    """
    creds_path = os.getenv("GSHEETS_CREDENTIALS_PATH")
    spreadsheet_id = os.getenv("GSHEETS_SPREADSHEET_ID")

    # Skip silently when env vars are absent (unit-test runs, local dev without creds).
    if not creds_path or not spreadsheet_id:
        yield
        return

    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)

    # --- Pre-test cleanup ---
    _delete_integration_worksheets(spreadsheet)

    yield  # Run the test session.

    # --- Post-test cleanup ---
    _delete_integration_worksheets(spreadsheet)


@pytest.fixture
def live_session():
    creds_path = os.getenv("GSHEETS_CREDENTIALS_PATH")
    spreadsheet_id = os.getenv("GSHEETS_SPREADSHEET_ID")
    uri = f"gsheets://{creds_path}?spreadsheet_id={spreadsheet_id}"
    engine = create_engine(uri)
    return Session(engine)
