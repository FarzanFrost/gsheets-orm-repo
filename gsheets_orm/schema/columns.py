import re
from typing import Any, Optional, Union

class BinaryExpression:
    def __init__(self, column: 'Column', operator: str, value: Any):
        self.column = column
        self.operator = operator
        self.value = value

    def __repr__(self) -> str:
        return f"<BinaryExpression: {self.column.name} {self.operator} {self.value}>"

class ForeignKey:
    def __init__(self, column_ref: str):
        self.column_ref = column_ref

    def __repr__(self) -> str:
        return f"ForeignKey('{self.column_ref}')"

class Column:
    def __init__(
        self,
        type_class: Any,
        *args: Any,
        primary_key: bool = False,
        nullable: bool = True,
        default: Any = None,
        prefix: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        regex: Optional[str] = None
    ):
        if isinstance(type_class, type):
            self.type = type_class()
        else:
            self.type = type_class

        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.prefix = prefix
        self.min_length = min_length
        self.max_length = max_length
        self.regex = regex
        self.name: Optional[str] = None
        self.foreign_key: Optional[ForeignKey] = None

        for arg in args:
            if isinstance(arg, ForeignKey):
                self.foreign_key = arg

    def __set_name__(self, owner: Any, name: str):
        self.name = name

    def __get__(self, instance: Any, owner: Any) -> Any:
        if instance is None:
            return self
        
        # Ensure _values exists on the instance
        if not hasattr(instance, '_values'):
            instance._values = {}

        if self.name not in instance._values:
            val = self.default() if callable(self.default) else self.default
            instance._values[self.name] = val
        
        return instance._values[self.name]

    def __set__(self, instance: Any, value: Any):
        if not hasattr(instance, '_values'):
            instance._values = {}

        # Run cast
        casted_val = self.type.to_python(value)

        if casted_val is None and not self.nullable:
            raise ValueError(f"Column '{self.name}' is not nullable")

        if casted_val is not None:
            str_val = str(casted_val)
            if self.min_length is not None and len(str_val) < self.min_length:
                raise ValueError(
                    f"'{self.name}' too short: {len(str_val)} chars (min {self.min_length})"
                )
            if self.max_length is not None and len(str_val) > self.max_length:
                raise ValueError(
                    f"'{self.name}' too long: {len(str_val)} chars (max {self.max_length})"
                )
            if self.regex is not None and not re.fullmatch(self.regex, str_val):
                raise ValueError(
                    f"Regex mismatch for '{self.name}': pattern {self.regex!r} does not match {str_val!r}"
                )

        old_val = instance._values.get(self.name)
        instance._values[self.name] = casted_val

        # Mark dirty if value has changed
        if old_val != casted_val and hasattr(instance, '_mark_dirty'):
            instance._mark_dirty()

    def __eq__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, "==", other)

    def __ne__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, "!=", other)

    def __lt__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, "<", other)

    def __le__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, "<=", other)

    def __gt__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, ">", other)

    def __ge__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, ">=", other)

    def contains(self, value: str) -> BinaryExpression:
        return BinaryExpression(self, "contains", value)

    def startswith(self, value: str) -> BinaryExpression:
        return BinaryExpression(self, "startswith", value)

    def endswith(self, value: str) -> BinaryExpression:
        return BinaryExpression(self, "endswith", value)

    def like(self, value: str) -> BinaryExpression:
        """Case-insensitive substring match."""
        return BinaryExpression(self, "like", value)

    def __repr__(self) -> str:
        return f"<Column: {self.name}>"
