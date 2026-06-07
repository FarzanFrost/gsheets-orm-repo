import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from gspread.exceptions import WorksheetNotFound
from gsheets_orm.engine.dialect import Dialect
from gsheets_orm.exceptions import DialectError


def make_dialect():
    engine = MagicMock()
    return Dialect(engine), engine


class TestFetchWorksheetData:
    def test_returns_rows_when_worksheet_exists(self):
        dialect, engine = make_dialect()
        ws = MagicMock()
        ws.get_all_values.return_value = [["id", "name"], ["1", "Alice"]]
        engine.spreadsheet.worksheet.return_value = ws

        result = dialect.fetch_worksheet_data("Sheet1")
        assert result == [["id", "name"], ["1", "Alice"]]

    def test_returns_empty_list_when_worksheet_not_found(self):
        dialect, engine = make_dialect()
        engine.spreadsheet.worksheet.side_effect = WorksheetNotFound("Sheet1")

        result = dialect.fetch_worksheet_data("Sheet1")
        assert result == []

    def test_raises_dialect_error_on_unexpected_exception(self):
        dialect, engine = make_dialect()
        engine.spreadsheet.worksheet.side_effect = RuntimeError("network error")

        with pytest.raises(DialectError, match="Failed to fetch worksheet"):
            dialect.fetch_worksheet_data("Sheet1")


class TestAppendRows:
    def test_creates_worksheet_when_not_found_then_appends(self):
        dialect, engine = make_dialect()
        new_ws = MagicMock()
        engine.spreadsheet.worksheet.side_effect = WorksheetNotFound("NewSheet")
        engine.spreadsheet.add_worksheet.return_value = new_ws

        dialect.append_rows("NewSheet", [["id", "name"], ["1", "Alice"]])

        engine.spreadsheet.add_worksheet.assert_called_once_with(
            title="NewSheet", rows=1000, cols=26
        )
        new_ws.append_rows.assert_called_once_with(
            [["id", "name"], ["1", "Alice"]], value_input_option="USER_ENTERED"
        )

    def test_appends_to_existing_worksheet(self):
        dialect, engine = make_dialect()
        ws = MagicMock()
        engine.spreadsheet.worksheet.return_value = ws

        dialect.append_rows("Sheet1", [["1", "Bob"]])

        ws.append_rows.assert_called_once_with(
            [["1", "Bob"]], value_input_option="USER_ENTERED"
        )

    def test_skips_when_rows_empty(self):
        dialect, engine = make_dialect()
        dialect.append_rows("Sheet1", [])
        engine.spreadsheet.worksheet.assert_not_called()
