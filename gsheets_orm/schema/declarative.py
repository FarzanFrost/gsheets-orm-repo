from typing import Any, Dict, List, Optional
from gsheets_orm.schema.columns import Column

_registry: Dict[str, type] = {}

def get_registered_models() -> Dict[str, type]:
    return _registry

def clear_registry():
    _registry.clear()

class Base:
    __tablename__: str = ""
    _columns: Dict[str, Column] = {}
    _primary_keys: List[str] = []

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        if not cls.__tablename__:
            cls.__tablename__ = cls.__name__
        
        cls._columns = {}
        cls._primary_keys = []
        
        # Traverse class hierarchy to collect columns (including inherited ones)
        for base in reversed(cls.__mro__):
            for name, attr in base.__dict__.items():
                if isinstance(attr, Column):
                    cls._columns[name] = attr
                    if attr.primary_key and name not in cls._primary_keys:
                        cls._primary_keys.append(name)
        
        _registry[cls.__tablename__] = cls

    def __init__(self, **kwargs: Any):
        self._values: Dict[str, Any] = {}
        self._session: Any = None
        self._row_num: Optional[int] = None
        
        for key, value in kwargs.items():
            if key in self._columns:
                setattr(self, key, value)
            else:
                raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")
        
        # Populate defaults for any missing columns
        for name, col in self._columns.items():
            if name not in self._values:
                val = col.default() if callable(col.default) else col.default
                self._values[name] = val

    def _mark_dirty(self):
        if self._session:
            self._session._mark_dirty(self)

    def __repr__(self) -> str:
        pk_str = ", ".join(f"{pk}={getattr(self, pk, None)}" for pk in self._primary_keys)
        return f"<{self.__class__.__name__}({pk_str})>"
