import time
from typing import Any, Dict, List, Tuple
from gspread.exceptions import APIError
from gsheets_orm.engine.base import Engine
from gsheets_orm.exceptions import DialectError

def retry_on_rate_limit(max_retries: int = 5, initial_backoff: float = 1.0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            backoff = initial_backoff
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except APIError as e:
                    # Check for rate limit response status (HTTP 429)
                    # gspread APIError.response contains response info
                    status_code = getattr(e, "code", None)
                    if not status_code and hasattr(e, "response"):
                        status_code = getattr(e.response, "status_code", None)
                    
                    if status_code == 429:
                        if attempt == max_retries - 1:
                            raise DialectError(f"Rate limit exceeded after {max_retries} attempts: {e}")
                        time.sleep(backoff)
                        backoff *= 2.0
                    else:
                        raise DialectError(f"Google Sheets API Error: {e}")
                except Exception as e:
                    raise DialectError(f"Unexpected error: {e}")
            return None
        return wrapper
    return decorator

class Dialect:
    def __init__(self, engine: Engine):
        self.engine = engine

    @retry_on_rate_limit()
    def fetch_worksheet_data(self, worksheet_name: str) -> List[List[str]]:
        try:
            worksheet = self.engine.spreadsheet.worksheet(worksheet_name)
            return worksheet.get_all_values()
        except DialectError:
            raise
        except Exception as e:
            raise DialectError(f"Failed to fetch worksheet '{worksheet_name}': {e}")

    @retry_on_rate_limit()
    def append_rows(self, worksheet_name: str, rows: List[List[Any]]):
        if not rows:
            return
        try:
            worksheet = self.engine.spreadsheet.worksheet(worksheet_name)
            worksheet.append_rows(rows, value_input_option="USER_ENTERED")
        except DialectError:
            raise
        except Exception as e:
            raise DialectError(f"Failed to append rows to worksheet '{worksheet_name}': {e}")

    @retry_on_rate_limit()
    def batch_update(self, worksheet_name: str, updates: List[Dict[str, Any]]):
        if not updates:
            return
        try:
            worksheet = self.engine.spreadsheet.worksheet(worksheet_name)
            # data is a list of updates, e.g. [{"range": "A2:C2", "values": [[...]]}]
            worksheet.batch_update(updates, value_input_option="USER_ENTERED")
        except DialectError:
            raise
        except Exception as e:
            raise DialectError(f"Failed to run batch updates on worksheet '{worksheet_name}': {e}")
