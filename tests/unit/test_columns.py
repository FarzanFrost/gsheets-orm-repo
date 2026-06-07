import pytest
from gsheets_orm.schema.columns import Column, ForeignKey, BinaryExpression
from gsheets_orm.types.core_types import String, Integer, Boolean

class MockModel:
    # A simple mock model to test descriptor on
    name = Column(String)
    age = Column(Integer, default=18)
    is_active = Column(Boolean, default=True)
    
    def __init__(self):
        self._values = {}

def test_column_descriptor_defaults():
    obj = MockModel()
    # Test default values
    assert obj.age == 18
    assert obj.is_active is True
    assert obj.name is None

def test_column_descriptor_set_get():
    obj = MockModel()
    obj.name = "Alice"
    obj.age = "30" # Type casting
    
    assert obj.name == "Alice"
    assert obj.age == 30

def test_column_operator_overloads():
    # Test that comparing a Column on the class returns a BinaryExpression
    expr = MockModel.age == 25
    assert isinstance(expr, BinaryExpression)
    assert expr.column == MockModel.age
    assert expr.operator == "=="
    assert expr.value == 25

    expr2 = MockModel.name != "Bob"
    assert isinstance(expr2, BinaryExpression)
    assert expr2.column == MockModel.name
    assert expr2.operator == "!="
    assert expr2.value == "Bob"

def test_column_string_operators():
    # contains
    expr = MockModel.name.contains("ice")
    assert isinstance(expr, BinaryExpression)
    assert expr.column == MockModel.name
    assert expr.operator == "contains"
    assert expr.value == "ice"

    # startswith
    expr2 = MockModel.name.startswith("Al")
    assert isinstance(expr2, BinaryExpression)
    assert expr2.operator == "startswith"
    assert expr2.value == "Al"

    # endswith
    expr3 = MockModel.name.endswith("ce")
    assert isinstance(expr3, BinaryExpression)
    assert expr3.operator == "endswith"
    assert expr3.value == "ce"

    # like (case-insensitive)
    expr4 = MockModel.name.like("ALICE")
    assert isinstance(expr4, BinaryExpression)
    assert expr4.operator == "like"
    assert expr4.value == "ALICE"

def test_foreign_key_definition():
    fk = ForeignKey("Department.dept_id")
    assert fk.column_ref == "Department.dept_id"
