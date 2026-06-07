import pytest
from unittest.mock import MagicMock
from gsheets_orm.schema.declarative import Base, clear_registry
from gsheets_orm.schema.columns import Column
from gsheets_orm.types.core_types import String
from gsheets_orm.orm.session import Session

class Employee(Base):
    __tablename__ = "Employee"
    emp_id = Column(String, primary_key=True)
    name = Column(String)

@pytest.fixture(autouse=True)
def cleanup():
    clear_registry()

def test_session_rollback_restores_state():
    engine = MagicMock()
    dialect = MagicMock()
    engine.connect.return_value = dialect
    session = Session(engine)
    session.dialect = dialect

    dialect.fetch_worksheet_data.return_value = [
        ["emp_id", "name"],
        ["EMP1", "Original Name"],
    ]

    emp = session.query(Employee).filter_by(emp_id="EMP1").first()
    assert emp is not None
    original_name = emp.name

    emp.name = "Hacked Name"
    assert emp in session._dirty

    session.rollback()

    assert emp.name == original_name
    assert len(session._dirty) == 0

def test_rollback_clears_new_and_deleted():
    engine = MagicMock()
    session = Session(engine)

    # _new logic
    new_emp = Employee(name="Ghost")
    session.add(new_emp)

    # _deleted logic requires an instance that's in the identity map (not just new)
    existing_emp = Employee(emp_id="EMP2", name="Alice")
    existing_emp._row_num = 2
    session.add_to_identity_map(existing_emp)
    
    session.delete(existing_emp)

    assert len(session._new) == 1
    assert len(session._deleted) == 1

    session.rollback()

    assert len(session._new) == 0
    assert len(session._deleted) == 0
