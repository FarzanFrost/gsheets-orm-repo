import pytest
from unittest.mock import MagicMock
from gsheets_orm.schema.declarative import Base, clear_registry
from gsheets_orm.schema.columns import Column
from gsheets_orm.types.core_types import String, Boolean
from gsheets_orm.orm.query import Query

class Employee(Base):
    __tablename__ = "Employee"
    emp_id = Column(String, primary_key=True)
    name = Column(String)
    role = Column(String)
    is_deleted = Column(Boolean, default=False)

@pytest.fixture(autouse=True)
def cleanup():
    clear_registry()

def test_query_filter_by():
    # Setup mock session and dialect
    mock_session = MagicMock()
    mock_dialect = MagicMock()
    mock_session.dialect = mock_dialect
    
    # Mock return data from Google Sheets:
    # First row is header, rest are rows
    mock_dialect.fetch_worksheet_data.return_value = [
        ["emp_id", "name", "role", "is_deleted"],
        ["EMP_001", "Alice", "ENGINEER", "FALSE"],
        ["EMP_002", "Bob", "MANAGER", "FALSE"],
        ["EMP_003", "Charlie", "ENGINEER", "TRUE"],
    ]
    
    # Mock identity map check (returns the object if it exists, otherwise store it)
    mock_session.get_from_identity_map.return_value = None
    
    # Perform query
    q = Query(mock_session, Employee)
    results = q.filter_by(role="ENGINEER").all()
    
    # Should only return Alice (Charlie is soft-deleted!)
    assert len(results) == 1
    assert results[0].name == "Alice"
    assert results[0].emp_id == "EMP_001"
    assert results[0]._row_num == 2 # 1-indexed row index (header is 1, Alice is row 2)

def test_query_filter_operators():
    mock_session = MagicMock()
    mock_dialect = MagicMock()
    mock_session.dialect = mock_dialect
    
    mock_dialect.fetch_worksheet_data.return_value = [
        ["emp_id", "name", "role", "is_deleted"],
        ["EMP_001", "Alice", "ENGINEER", "FALSE"],
        ["EMP_002", "Bob", "MANAGER", "FALSE"],
    ]
    mock_session.get_from_identity_map.return_value = None
    
    q = Query(mock_session, Employee)
    results = q.filter(Employee.name != "Alice").all()
    
    assert len(results) == 1
    assert results[0].name == "Bob"

def test_query_limit():
    mock_session = MagicMock()
    mock_dialect = MagicMock()
    mock_session.dialect = mock_dialect
    
    mock_dialect.fetch_worksheet_data.return_value = [
        ["emp_id", "name", "role", "is_deleted"],
        ["EMP_001", "Alice", "ENGINEER", "FALSE"],
        ["EMP_002", "Bob", "MANAGER", "FALSE"],
    ]
    mock_session.get_from_identity_map.return_value = None
    
    q = Query(mock_session, Employee)
    results = q.limit(1).all()
    
    assert len(results) == 1
    assert results[0].name == "Alice"

def test_query_first():
    mock_session = MagicMock()
    mock_dialect = MagicMock()
    mock_session.dialect = mock_dialect
    
    mock_dialect.fetch_worksheet_data.return_value = [
        ["emp_id", "name", "role", "is_deleted"],
        ["EMP_001", "Alice", "ENGINEER", "FALSE"],
    ]
    mock_session.get_from_identity_map.return_value = None
    
    q = Query(mock_session, Employee)
    first_emp = q.first()
    assert first_emp is not None
    assert first_emp.name == "Alice"
