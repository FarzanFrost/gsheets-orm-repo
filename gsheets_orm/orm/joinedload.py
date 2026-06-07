"""
joinedload — eager-loading support for gsheets-orm.

Usage:
    from gsheets_orm.orm.joinedload import joinedload

    assignments = (
        session.query(Assignment)
        .options(joinedload(Assignment.employee))
        .all()
    )

JoinedLoad.resolve() makes exactly ONE extra network call to fetch the related
sheet regardless of how many primary objects are in the result set, avoiding
the N+1 query problem produced by RelationshipDescriptor's default lazy loading.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, List


class JoinedLoad:
    """Resolves a single relationship eagerly for a list of primary instances."""

    def __init__(self, relationship_attr: Any) -> None:
        # relationship_attr is the RelationshipDescriptor class-level attribute,
        # e.g. Assignment.employee  →  RelationshipDescriptor instance
        self.relationship_attr = relationship_attr

    def resolve(self, session: Any, instances: List[Any]) -> None:
        """
        Fetch the related sheet once, then attach related objects in-memory
        by writing directly into each instance's _values dict.  This pre-population
        prevents RelationshipDescriptor.__get__ from issuing a lazy query.
        """
        if not instances:
            return

        descriptor = self.relationship_attr
        owner_cls = instances[0].__class__

        # --- Locate target model class from the global registry ---
        from gsheets_orm.schema.declarative import get_registered_models
        models = get_registered_models()
        target_cls = models.get(descriptor.target_model_name)
        if not target_cls:
            for m in models.values():
                if m.__name__ == descriptor.target_model_name:
                    target_cls = m
                    break
        if not target_cls:
            return

        # --- Determine FK direction ---
        # Many-to-One: owner has a FK column pointing at target
        fk_col = None
        for col_name, col in owner_cls._columns.items():
            if col.foreign_key:
                ref_table = col.foreign_key.column_ref.split('.')[0]
                if ref_table in (target_cls.__tablename__, target_cls.__name__):
                    fk_col = col_name
                    break

        if fk_col:
            self._resolve_many_to_one(session, instances, descriptor, target_cls, fk_col)
        else:
            self._resolve_one_to_many(session, instances, descriptor, owner_cls, target_cls)

    # ------------------------------------------------------------------
    # Many-to-One: collect unique FK values → one fetch → attach object
    # ------------------------------------------------------------------
    def _resolve_many_to_one(
        self,
        session: Any,
        instances: List[Any],
        descriptor: Any,
        target_cls: Any,
        fk_col: str,
    ) -> None:
        fk_values = {
            getattr(inst, fk_col)
            for inst in instances
            if getattr(inst, fk_col) is not None
        }
        if not fk_values:
            for inst in instances:
                inst._values[descriptor.name] = None
            return

        if not target_cls._primary_keys:
            return
        target_pk = target_cls._primary_keys[0]

        # ONE network call — results land in the identity map
        related_objs = session.query(target_cls).all()
        lookup = {getattr(obj, target_pk): obj for obj in related_objs}

        for inst in instances:
            fk_val = getattr(inst, fk_col)
            inst._values[descriptor.name] = lookup.get(fk_val)

    # ------------------------------------------------------------------
    # One-to-Many: one fetch → group by FK → attach list
    # ------------------------------------------------------------------
    def _resolve_one_to_many(
        self,
        session: Any,
        instances: List[Any],
        descriptor: Any,
        owner_cls: Any,
        target_cls: Any,
    ) -> None:
        # Find the FK column on the target that references the owner
        target_fk_col = None
        for col_name, col in target_cls._columns.items():
            if col.foreign_key:
                ref_table = col.foreign_key.column_ref.split('.')[0]
                if ref_table in (owner_cls.__tablename__, owner_cls.__name__):
                    target_fk_col = col_name
                    break
        if not target_fk_col:
            return

        # ONE network call
        related_objs = session.query(target_cls).all()

        # Group by FK value
        grouped: dict = defaultdict(list)
        for obj in related_objs:
            grouped[getattr(obj, target_fk_col)].append(obj)

        from gsheets_orm.orm.session import get_pk_value
        for inst in instances:
            my_pk = get_pk_value(inst)
            inst._values[descriptor.name] = grouped.get(my_pk, [])


def joinedload(relationship_attr: Any) -> JoinedLoad:
    """
    Return a JoinedLoad eager-loader for the given relationship attribute.

    Example::

        session.query(Assignment).options(joinedload(Assignment.employee)).all()
    """
    return JoinedLoad(relationship_attr)
