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
        prefix: Optional[str] = None
    ):
        if isinstance(type_class, type):
            self.type = type_class()
        else:
            self.type = type_class

        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.prefix = prefix
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
