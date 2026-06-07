import pytest
from datetime import datetime
from gsheets_orm.types.core_types import String, Integer, Float, Boolean, DateTime

def test_string_type():
    t = String()
    assert t.to_python("hello") == "hello"
    assert t.to_python(123) == "123"
    assert t.to_sheet("hello") == "hello"
    assert t.to_sheet(None) == ""

def test_integer_type():
    t = Integer()
    assert t.to_python("123") == 123
    assert t.to_python(456) == 456
    assert t.to_sheet(123) == "123"
    assert t.to_sheet(None) == ""
    with pytest.raises(ValueError):
        t.to_python("abc")

def test_float_type():
    t = Float()
    assert t.to_python("123.45") == 123.45
    assert t.to_python(456.7) == 456.7
    assert t.to_sheet(123.45) == "123.45"
    assert t.to_sheet(None) == ""
    with pytest.raises(ValueError):
        t.to_python("abc")

def test_boolean_type():
    t = Boolean()
    # Sheet to python
    assert t.to_python("TRUE") is True
    assert t.to_python("true") is True
    assert t.to_python("Yes") is True
    assert t.to_python("1") is True
    assert t.to_python("FALSE") is False
    assert t.to_python("false") is False
    assert t.to_python("No") is False
    assert t.to_python("0") is False
    assert t.to_python("") is False
    
    # Python to sheet
    assert t.to_sheet(True) == "TRUE"
    assert t.to_sheet(False) == "FALSE"
    assert t.to_sheet(None) == "FALSE"

def test_datetime_type():
    t = DateTime()
    dt_str = "2026-06-06 15:45:00"
    dt = datetime(2026, 6, 6, 15, 45, 0)
    
    assert t.to_python(dt_str) == dt
    assert t.to_python(dt) == dt
    assert t.to_sheet(dt) == dt_str
    assert t.to_sheet(None) == ""
    
    with pytest.raises(ValueError):
        t.to_python("invalid-date")
