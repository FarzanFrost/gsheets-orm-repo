from datetime import datetime
from typing import Any, Optional

class ColumnType:
    def to_python(self, value: Any) -> Any:
        raise NotImplementedError

    def to_sheet(self, value: Any) -> str:
        raise NotImplementedError

class String(ColumnType):
    def to_python(self, value: Any) -> Optional[str]:
        if value is None or value == "":
            return None
        return str(value)

    def to_sheet(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value)

class Integer(ColumnType):
    def to_python(self, value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Value '{value}' cannot be converted to Integer")

    def to_sheet(self, value: Any) -> str:
        if value is None:
            return ""
        return str(int(value))

class Float(ColumnType):
    def to_python(self, value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Value '{value}' cannot be converted to Float")

    def to_sheet(self, value: Any) -> str:
        if value is None:
            return ""
        return str(float(value))

class Boolean(ColumnType):
    def to_python(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        val_str = str(value).strip().lower()
        return val_str in ("true", "yes", "1")

    def to_sheet(self, value: Any) -> str:
        return "TRUE" if value else "FALSE"

class DateTime(ColumnType):
    DEFAULT_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, date_format: str = DEFAULT_FORMAT):
        self.date_format = date_format

    def to_python(self, value: Any) -> Optional[datetime]:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value
        try:
            # Handle float or other representation if necessary, but standard is string
            return datetime.strptime(str(value), self.date_format)
        except ValueError:
            raise ValueError(f"Value '{value}' does not match format '{self.date_format}'")

    def to_sheet(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime(self.date_format)
        raise ValueError("Value must be a datetime object")
