import pytest
from gsheets_orm.schema.columns import Column
from gsheets_orm.types.core_types import String

class MockValidModel:
    code = Column(String, min_length=3, max_length=5, regex=r'^[A-Z]+$')
    optional_code = Column(String, nullable=True, min_length=2, max_length=4)

    def __init__(self):
        self._values = {}

def test_min_length_raises():
    obj = MockValidModel()
    with pytest.raises(ValueError, match="too short"):
        obj.code = "AB"

def test_max_length_raises():
    obj = MockValidModel()
    with pytest.raises(ValueError, match="too long"):
        obj.code = "ABCDEF"

def test_regex_mismatch_raises():
    obj = MockValidModel()
    with pytest.raises(ValueError, match="Regex mismatch"):
        obj.code = "abc"

def test_valid_value_passes():
    obj = MockValidModel()
    obj.code = "ABC"
    assert obj.code == "ABC"
    
    obj.code = "ABCDE"
    assert obj.code == "ABCDE"

def test_nullable_none_bypasses_validation():
    obj = MockValidModel()
    # optional_code is nullable, so None should pass without hitting length/regex checks
    obj.optional_code = None
    assert obj.optional_code is None
