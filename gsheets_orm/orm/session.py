import re
import copy
from typing import Any, Dict, List, Set, Type, Tuple, Optional
from gsheets_orm.engine.base import Engine
from gsheets_orm.engine.dialect import Dialect
from gsheets_orm.exceptions import SessionError, ValidationError

def get_col_letter(col_idx: int) -> str:
    letter = ""
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        letter = chr(65 + remainder) + letter
    return letter

def get_pk_value(instance: Any) -> Any:
    pks = instance._primary_keys
    if not pks:
        return None
    if len(pks) == 1:
        return getattr(instance, pks[0], None)
    return tuple(getattr(instance, pk, None) for pk in pks)

def generate_next_key(existing_values: List[str], prefix: Optional[str]) -> Any:
    nums = []
    for val in existing_values:
        if val is None or val == "":
            continue
        val_str = str(val).strip()
        if prefix:
            # Matches prefix + separator + digits (e.g. EMP_001, EMP001, EMP-001)
            # Find the numerical digits suffix at the end of the string
            match = re.search(r'\d+$', val_str)
            if match:
                nums.append(int(match.group(0)))
        else:
            try:
                nums.append(int(float(val_str)))
            except ValueError:
                pass

    next_num = max(nums) + 1 if nums else 1
    if prefix:
        return f"{prefix}_{next_num:03d}"
    return next_num

class Session:
    def __init__(self, bind: Engine):
        self.bind = bind
        self.dialect = Dialect(bind)
        self._new: Set[Any] = set()
        self._dirty: Set[Any] = set()
        self._deleted: Set[Any] = set()
        self._identity_map: Dict[Tuple[Type[Any], Any], Any] = {}
        self._snapshots: Dict[Tuple[Type[Any], Any], Dict] = {}

    def query(self, model_class: Type[Any]) -> Any:
        from gsheets_orm.orm.query import Query
        return Query(self, model_class)

    def add(self, instance: Any):
        instance._session = self
        # Only add to new if it doesn't have a row number (is not persistent)
        if getattr(instance, "_row_num", None) is None:
            self._new.add(instance)

    def delete(self, instance: Any):
        instance._session = self
        # If the object is in _new, just remove it from _new
        if instance in self._new:
            self._new.remove(instance)
        else:
            self._deleted.add(instance)
            # Remove from dirty if present
            if instance in self._dirty:
                self._dirty.remove(instance)

    def _mark_dirty(self, instance: Any):
        if instance not in self._new and instance not in self._deleted:
            self._dirty.add(instance)

    def add_to_identity_map(self, instance: Any):
        pk_val = get_pk_value(instance)
        if pk_val is not None:
            key = (instance.__class__, pk_val)
            self._identity_map[key] = instance
            # Snapshot original state only on first entry (preserve true original)
            if key not in self._snapshots:
                self._snapshots[key] = copy.deepcopy(instance._values)

    def get_from_identity_map(self, model_class: Type[Any], pk_value: Any) -> Optional[Any]:
        if pk_value is None:
            return None
        return self._identity_map.get((model_class, pk_value))

    def rollback(self):
        """Revert all dirty objects to their snapshotted state and clear pending queues."""
        for instance in list(self._dirty):
            pk_val = get_pk_value(instance)
            key = (instance.__class__, pk_val)
            if key in self._snapshots:
                instance._values = copy.deepcopy(self._snapshots[key])
        self._dirty.clear()
        self._new.clear()
        self._deleted.clear()

    def commit(self):
        # Group changes by model class / table
        all_changed_instances = list(self._new) + list(self._dirty) + list(self._deleted)
        classes = set(inst.__class__ for inst in all_changed_instances)

        for cls in classes:
            tablename = cls.__tablename__
            # Fetch worksheet data to resolve structure and key generation
            try:
                sheet_data = self.dialect.fetch_worksheet_data(tablename)
            except Exception:
                sheet_data = []

            if not sheet_data:
                # If sheet is empty/missing, write headers first
                headers = list(cls._columns.keys())
                self.dialect.append_rows(tablename, [headers])
                sheet_data = [headers]

            headers = sheet_data[0]
            header_map = {name: idx for idx, name in enumerate(headers)}
            
            # Map column indices to quickly compute row values
            num_cols = len(headers)
            last_col_letter = get_col_letter(num_cols)

            # 1. Process inserts (_new)
            new_rows = []
            new_instances = [inst for inst in self._new if inst.__class__ is cls]
            
            # Sort new instances to ensure stable generation order
            for inst in new_instances:
                # Generate primary keys if missing
                pk_cols = cls._primary_keys
                is_composite = len(pk_cols) > 1
                for pk_name in pk_cols:
                    current_pk_val = getattr(inst, pk_name, None)
                    if current_pk_val is None:
                        col = cls._columns[pk_name]
                        if is_composite and col.prefix is None:
                            raise ValueError(
                                f"Ambiguous composite PK: column '{pk_name}' on "
                                f"'{cls.__name__}' is None. Composite PK columns without "
                                f"a 'prefix' must be supplied explicitly."
                            )
                        # Extract existing values in the primary key column
                        col_idx = header_map.get(pk_name)
                        existing_values = []
                        if col_idx is not None:
                            for r in sheet_data[1:]:
                                if col_idx < len(r):
                                    existing_values.append(r[col_idx])

                        generated_key = generate_next_key(existing_values, col.prefix)
                        setattr(inst, pk_name, generated_key)

                # Build row values in header order using DataMapper
                from gsheets_orm.orm.mapper import DataMapper
                row_values = DataMapper.model_to_row(inst, headers)

                new_rows.append(row_values)
                # Temporarily add to local sheet_data copy for subsequent key generation
                sheet_data.append(row_values)

            if new_rows:
                self.dialect.append_rows(tablename, new_rows)
                # Assign row numbers and add to identity map
                start_row = len(sheet_data) - len(new_rows) + 1
                for idx, inst in enumerate(new_instances):
                    inst._row_num = start_row + idx
                    self.add_to_identity_map(inst)

            # 2. Process updates (_dirty) and deletes (_deleted)
            batch_updates = []
            
            dirty_instances = [inst for inst in self._dirty if inst.__class__ is cls]
            for inst in dirty_instances:
                row_num = getattr(inst, "_row_num", None)
                if row_num is None:
                    raise SessionError(f"Cannot update instance {inst} without a registered row number")
                
                # Build row values in header order using DataMapper
                from gsheets_orm.orm.mapper import DataMapper
                row_values = DataMapper.model_to_row(inst, headers)

                range_str = f"A{row_num}:{last_col_letter}{row_num}"
                batch_updates.append({"range": range_str, "values": [row_values]})

            deleted_instances = [inst for inst in self._deleted if inst.__class__ is cls]
            for inst in deleted_instances:
                row_num = getattr(inst, "_row_num", None)
                if row_num is None:
                    raise SessionError(f"Cannot delete instance {inst} without a registered row number")

                if "is_deleted" in cls._columns:
                    # Soft-delete: toggle flag
                    setattr(inst, "is_deleted", True)
                    from gsheets_orm.orm.mapper import DataMapper
                    row_values = DataMapper.model_to_row(inst, headers)

                    range_str = f"A{row_num}:{last_col_letter}{row_num}"
                    batch_updates.append({"range": range_str, "values": [row_values]})
                else:
                    # Hard-delete: clear the row by replacing with empty strings
                    row_values = [""] * num_cols
                    range_str = f"A{row_num}:{last_col_letter}{row_num}"
                    batch_updates.append({"range": range_str, "values": [row_values]})

            if batch_updates:
                self.dialect.batch_update(tablename, batch_updates)

        # Reset queues upon successful commit
        self._new.clear()
        self._dirty.clear()
        self._deleted.clear()
