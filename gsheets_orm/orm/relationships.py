from typing import Any, Optional, Type
from gsheets_orm.exceptions import SessionError

class RelationshipDescriptor:
    def __init__(self, target_model_name: str, back_populates: Optional[str] = None):
        self.target_model_name = target_model_name
        self.back_populates = back_populates
        self.name: Optional[str] = None

    def __set_name__(self, owner: Any, name: str):
        self.name = name

    def __get__(self, instance: Any, owner: Any) -> Any:
        if instance is None:
            return self

        # Retrieve target model class from registry
        from gsheets_orm.schema.declarative import get_registered_models
        models = get_registered_models()
        
        # Table names might differ from class names, check both
        target_cls = models.get(self.target_model_name)
        if not target_cls:
            # Try to find class by name
            for m_cls in models.values():
                if m_cls.__name__ == self.target_model_name:
                    target_cls = m_cls
                    break
        
        if not target_cls:
            raise SessionError(f"Target model '{self.target_model_name}' is not registered.")

        # If we have a cached value in values, use it (transient objects, or if already loaded)
        if not hasattr(instance, '_values'):
            instance._values = {}

        session = getattr(instance, "_session", None)
        if not session:
            # For transient objects, return whatever was set
            return instance._values.get(self.name)

        # Check if many-to-one (this instance has ForeignKey referencing target)
        fk_col = None
        for col_name, col in instance._columns.items():
            if col.foreign_key:
                # e.g., 'Department.dept_id' or 'department.dept_id'
                ref_parts = col.foreign_key.column_ref.split('.')
                ref_table_or_cls = ref_parts[0]
                if ref_table_or_cls == target_cls.__tablename__ or ref_table_or_cls == target_cls.__name__:
                    fk_col = col_name
                    break

        if fk_col:
            # Many-to-One
            fk_val = getattr(instance, fk_col)
            if fk_val is None:
                return None
            
            # Find the primary key column name of the target
            if not target_cls._primary_keys:
                raise SessionError(f"Target model '{target_cls.__name__}' must define a primary key")
            target_pk = target_cls._primary_keys[0]
            
            # Query session
            return session.query(target_cls).filter_by(**{target_pk: fk_val}).first()
        else:
            # One-to-Many
            # Find ForeignKey on the target referencing this model
            target_fk_col = None
            for col_name, col in target_cls._columns.items():
                if col.foreign_key:
                    ref_parts = col.foreign_key.column_ref.split('.')
                    ref_table_or_cls = ref_parts[0]
                    if ref_table_or_cls == instance.__class__.__tablename__ or ref_table_or_cls == instance.__class__.__name__:
                        target_fk_col = col_name
                        break

            if not target_fk_col:
                raise SessionError(
                    f"No ForeignKey found on '{target_cls.__name__}' pointing to '{instance.__class__.__name__}'"
                )

            # Query session for all target instances matching this instance's primary key
            from gsheets_orm.orm.session import get_pk_value
            my_pk = get_pk_value(instance)
            if my_pk is None:
                return []
            
            return session.query(target_cls).filter_by(**{target_fk_col: my_pk}).all()

    def __set__(self, instance: Any, value: Any):
        if not hasattr(instance, '_values'):
            instance._values = {}

        from gsheets_orm.schema.declarative import get_registered_models
        models = get_registered_models()
        
        target_cls = models.get(self.target_model_name)
        if not target_cls:
            for m_cls in models.values():
                if m_cls.__name__ == self.target_model_name:
                    target_cls = m_cls
                    break
        
        # Check if many-to-one
        fk_col = None
        for col_name, col in instance._columns.items():
            if col.foreign_key:
                ref_parts = col.foreign_key.column_ref.split('.')
                ref_table_or_cls = ref_parts[0]
                if target_cls and (ref_table_or_cls == target_cls.__tablename__ or ref_table_or_cls == target_cls.__name__):
                    fk_col = col_name
                    break

        if fk_col:
            # Set foreign key value
            if value is None:
                setattr(instance, fk_col, None)
            else:
                if not target_cls._primary_keys:
                    raise SessionError(f"Target model '{target_cls.__name__}' must define a primary key")
                target_pk = target_cls._primary_keys[0]
                setattr(instance, fk_col, getattr(value, target_pk))

        instance._values[self.name] = value

def relationship(target_model_name: str, back_populates: Optional[str] = None) -> RelationshipDescriptor:
    return RelationshipDescriptor(target_model_name, back_populates)
