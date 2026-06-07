import pytest
from unittest.mock import MagicMock
from gsheets_orm.schema.declarative import Base, clear_registry
from gsheets_orm.schema.columns import Column, ForeignKey
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

def _make_query(data):
    mock_session = MagicMock()
    mock_dialect = MagicMock()
    mock_session.dialect = mock_dialect
    mock_dialect.fetch_worksheet_data.return_value = data
    mock_session.get_from_identity_map.return_value = None
    return Query(mock_session, Employee)

def test_filter_contains():
    data = [
        ["emp_id", "name", "role", "is_deleted"],
        ["E1", "Alice", "ENG", "FALSE"],
        ["E2", "Bob",   "ENG", "FALSE"],
        ["E3", "BatchUser_0", "ENG", "FALSE"],
    ]
    results = _make_query(data).filter(Employee.name.contains("BatchUser")).all()
    assert len(results) == 1
    assert results[0].emp_id == "E3"

def test_filter_startswith():
    data = [
        ["emp_id", "name", "role", "is_deleted"],
        ["E1", "Alice", "ENG", "FALSE"],
        ["E2", "Alberto", "ENG", "FALSE"],
        ["E3", "Bob", "ENG", "FALSE"],
    ]
    results = _make_query(data).filter(Employee.name.startswith("Al")).all()
    assert len(results) == 2
    names = {r.name for r in results}
    assert names == {"Alice", "Alberto"}

def test_filter_endswith():
    data = [
        ["emp_id", "name", "role", "is_deleted"],
        ["E1", "Alice", "ENG", "FALSE"],
        ["E2", "Candice", "ENG", "FALSE"],
        ["E3", "Bob", "ENG", "FALSE"],
    ]
    results = _make_query(data).filter(Employee.name.endswith("ice")).all()
    assert len(results) == 2
    names = {r.name for r in results}
    assert names == {"Alice", "Candice"}

def test_filter_like_case_insensitive():
    data = [
        ["emp_id", "name", "role", "is_deleted"],
        ["E1", "alice", "ENG", "FALSE"],
        ["E2", "ALICE", "ENG", "FALSE"],
        ["E3", "Bob", "ENG", "FALSE"],
    ]
    results = _make_query(data).filter(Employee.name.like("ALICE")).all()
    assert len(results) == 2

def test_filter_contains_none_safe():
    """None values in column must not raise — treated as empty string."""
    data = [
        ["emp_id", "name", "role", "is_deleted"],
        ["E1", None, "ENG", "FALSE"],
        ["E2", "BatchUser_1", "ENG", "FALSE"],
    ]
    results = _make_query(data).filter(Employee.name.contains("BatchUser")).all()
    assert len(results) == 1
    assert results[0].emp_id == "E2"

def test_eager_loading_prevents_n_plus_one(mocker):
    from gsheets_orm.orm.relationships import relationship
    from gsheets_orm.orm.joinedload import joinedload
    
    class MockAssignment(Base):
        __tablename__ = "Assignments"
        id = Column(String, primary_key=True)
        emp_id = Column(String, ForeignKey("Employee.emp_id"))
        employee = relationship("Employee")
        
    from gsheets_orm.schema.declarative import _registry
    _registry["Employee"] = Employee
    
    mock_session = MagicMock()
    mock_dialect = MagicMock()
    mock_session.dialect = mock_dialect
    mock_session.query.return_value = Query(mock_session, Employee)
    
    # Mock read data based on tablename
    def mock_fetch(tablename):
        if tablename == "Assignments":
            return [
                ["id", "emp_id"],
                ["A1", "EMP_001"],
                ["A2", "EMP_002"],
                ["A3", "EMP_001"]
            ]
        elif tablename == "Employee":
            return [
                ["emp_id", "name", "role", "is_deleted"],
                ["EMP_001", "Alice", "ENG", "FALSE"],
                ["EMP_002", "Bob", "MGR", "FALSE"],
            ]
        return []
        
    mock_dialect.fetch_worksheet_data.side_effect = mock_fetch
    mock_session.get_from_identity_map.return_value = None
    
    q = Query(mock_session, MockAssignment)
    
    # We add options(joinedload())
    assignments = q.options(joinedload(MockAssignment.employee)).all()
    
    assert len(assignments) == 3
    assert assignments[0].employee is not None
    assert assignments[0].employee.name == "Alice"
    assert assignments[1].employee.name == "Bob"
    assert assignments[2].employee.name == "Alice"
    
    # Verify the fetch was called exactly twice (Assignments + Employee), not 1 + N
    assert mock_dialect.fetch_worksheet_data.call_count == 2
