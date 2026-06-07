from typing import Any, Dict, List, Type

class DataMapper:
    @staticmethod
    def model_to_row(instance: Any, headers: List[str]) -> List[str]:
        row = []
        for name in headers:
            col = instance._columns.get(name)
            if col:
                val = getattr(instance, name)
                row.append(col.type.to_sheet(val))
            else:
                row.append("")
        return row

    @staticmethod
    def row_to_attrs(model_cls: Type[Any], row: List[str], header_map: Dict[str, int]) -> Dict[str, Any]:
        attrs = {}
        for name, col in model_cls._columns.items():
            if name in header_map:
                idx = header_map[name]
                cell_val = row[idx] if idx < len(row) else ""
                attrs[name] = col.type.to_python(cell_val)
            else:
                attrs[name] = col.default() if callable(col.default) else col.default
        return attrs
