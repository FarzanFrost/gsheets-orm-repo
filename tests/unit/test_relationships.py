import pytest
from unittest.mock import MagicMock
from gsheets_orm.schema.declarative import Base, clear_registry
from gsheets_orm.schema.columns import Column, ForeignKey
from gsheets_orm.types.core_types import String
from gsheets_orm.orm.relationships import relationship

class Department(Base):
    __tablename__ = "Department"
    dept_id = Column(String, primary_key=True)
    name = Column(String)
    employees = relationship("Employee", back_populates="department")

class Employee(Base):
    __tablename__ = "Employee"
    emp_id = Column(String, primary_key=True)
    name = Column(String)
    fr_department_id = Column(String, ForeignKey("Department.dept_id"))
    department = relationship("Department", back_populates="employees")

@pytest.fixture(autouse=True)
def cleanup():
    clear_registry()
    from gsheets_orm.schema.declarative import _registry
    _registry["Department"] = Department
    _registry["Employee"] = Employee

def test_relationship_lazy_load_many_to_one():
    # Setup mocks
    mock_session = MagicMock()
    
    dept = Department(dept_id="D1", name="HR")
    emp = Employee(emp_id="E1", name="Alice", fr_department_id="D1")
    emp._session = mock_session
    
    # Mock query to fetch department
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter_by.return_value = mock_query
    mock_query.first.return_value = dept
    
    # Access relationship -> should lazy load
    assert emp.department == dept
    
    # Verify the query was made correctly
    mock_session.query.assert_called_once_with(Department)
    mock_query.filter_by.assert_called_once_with(dept_id="D1")

def test_relationship_lazy_load_one_to_many():
    mock_session = MagicMock()
    
    dept = Department(dept_id="D1", name="HR")
    dept._session = mock_session
    
    emp1 = Employee(emp_id="E1", name="Alice", fr_department_id="D1")
    emp2 = Employee(emp_id="E2", name="Bob", fr_department_id="D1")
    
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter_by.return_value = mock_query
    mock_query.all.return_value = [emp1, emp2]
    
    # Access employees -> should lazy load list
    assert dept.employees == [emp1, emp2]
    
    mock_session.query.assert_called_once_with(Employee)
    mock_query.filter_by.assert_called_once_with(fr_department_id="D1")

def test_relationship_set_foreign_key():
    dept = Department(dept_id="D2", name="Engineering")
    emp = Employee(emp_id="E3", name="Charlie")
    
    # Set relationship on transient object
    emp.department = dept
    
    # Should automatically assign the foreign key field
    assert emp.fr_department_id == "D2"
    assert emp.department == dept
