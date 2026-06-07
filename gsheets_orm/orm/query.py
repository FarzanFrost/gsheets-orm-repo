from typing import Any, Dict, List, Optional, Type
from gsheets_orm.schema.columns import Column, BinaryExpression
from gsheets_orm.exceptions import ValidationError

class Query:
    def __init__(self, session: Any, model: Type[Any]):
        self.session = session
        self.model = model
        self._filters: List[BinaryExpression] = []
        self._filter_by_dict: Dict[str, Any] = {}
        self._limit: Optional[int] = None

    def filter(self, *expressions: BinaryExpression) -> 'Query':
        for expr in expressions:
            if not isinstance(expr, BinaryExpression):
                raise ValidationError("filter() arguments must be BinaryExpression instances (e.g. Model.field == value)")
            self._filters.append(expr)
        return self

    def filter_by(self, **kwargs: Any) -> 'Query':
        for key, val in kwargs.items():
            if key not in self.model._columns:
                raise ValidationError(f"Model '{self.model.__name__}' has no column '{key}'")
            self._filter_by_dict[key] = val
        return self

    def limit(self, n: int) -> 'Query':
        self._limit = n
        return self

    def _matches_filters(self, instance: Any) -> bool:
        # Evaluate filter_by dict
        for key, expected in self._filter_by_dict.items():
            val = getattr(instance, key, None)
            if val != expected:
                return False

        # Evaluate BinaryExpressions
        for expr in self._filters:
            col_name = expr.column.name
            actual = getattr(instance, col_name, None)
            expected = expr.value
            op = expr.operator

            if op == "==":
                if actual != expected:
                    return False
            elif op == "!=":
                if actual == expected:
                    return False
            elif op == "<":
                if not (actual < expected):
                    return False
            elif op == "<=":
                if not (actual <= expected):
                    return False
            elif op == ">":
                if not (actual > expected):
                    return False
            elif op == ">=":
                if not (actual >= expected):
                    return False
            else:
                return False

        return True

    def all(self) -> List[Any]:
        # Fetch data via dialect
        data = self.session.dialect.fetch_worksheet_data(self.model.__tablename__)
        if not data:
            return []

        header_row = data[0]
        rows = data[1:]
        header_map = {name: idx for idx, name in enumerate(header_row)}

        results = []
        for idx, row in enumerate(rows):
            row_num = idx + 2  # Row 1 is header
            
            # Map sheet cells to python values using DataMapper
            from gsheets_orm.orm.mapper import DataMapper
            attrs = DataMapper.row_to_attrs(self.model, row, header_map)

            # Resolve primary key for identity mapping
            pk_vals = []
            for pk in self.model._primary_keys:
                pk_vals.append(attrs.get(pk))
            
            pk_val = pk_vals[0] if len(pk_vals) == 1 else tuple(pk_vals)
            
            # Check Identity Map first
            instance = self.session.get_from_identity_map(self.model, pk_val)
            if instance is None:
                # Instantiate model object
                instance = self.model(**attrs)
                instance._row_num = row_num
                instance._session = self.session
                self.session.add_to_identity_map(instance)
            else:
                # Update attributes on clean/non-dirty fields
                # In standard ORM, clean attributes are synced from DB, but we keep it simple:
                # Update only if not marked dirty
                for k, v in attrs.items():
                    if not hasattr(instance, "_dirty_fields") or k not in instance._dirty_fields:
                        instance._values[k] = v
                instance._row_num = row_num

            results.append(instance)

        # Apply soft-deletion filter if 'is_deleted' column exists
        # and has not been explicitly queried in filters
        if "is_deleted" in self.model._columns:
            explicit_soft_delete_query = False
            # Check filter_by_dict
            if "is_deleted" in self._filter_by_dict:
                explicit_soft_delete_query = True
            # Check BinaryExpressions
            for expr in self._filters:
                if expr.column.name == "is_deleted":
                    explicit_soft_delete_query = True
                    break

            if not explicit_soft_delete_query:
                # Filter out is_deleted == True
                results = [r for r in results if getattr(r, "is_deleted") is not True]

        # Apply remaining filters
        filtered_results = []
        for instance in results:
            if self._matches_filters(instance):
                filtered_results.append(instance)

        # Apply limit
        if self._limit is not None:
            filtered_results = filtered_results[:self._limit]

        return filtered_results

    def first(self) -> Optional[Any]:
        res = self.all()
        return res[0] if res else None
