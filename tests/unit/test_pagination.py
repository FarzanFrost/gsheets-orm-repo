import pytest
from unittest.mock import MagicMock
from gsheets_orm.schema.declarative import Base, clear_registry
from gsheets_orm.schema.columns import Column
from gsheets_orm.types.core_types import String, Integer
from gsheets_orm.orm.query import Query

class Item(Base):
    __tablename__ = "Item"
    id = Column(Integer, primary_key=True)
    name = Column(String)

@pytest.fixture(autouse=True)
def cleanup():
    clear_registry()

def _make_query(data):
    mock_session = MagicMock()
    mock_dialect = MagicMock()
    mock_session.dialect = mock_dialect
    mock_dialect.fetch_worksheet_data.return_value = data
    mock_session.get_from_identity_map.return_value = None
    return Query(mock_session, Item)

def test_offset_skips_first_n():
    data = [
        ["id", "name"],
        ["1", "A"],
        ["2", "B"],
        ["3", "C"],
        ["4", "D"],
        ["5", "E"],
    ]
    results = _make_query(data).offset(2).all()
    assert len(results) == 3
    assert results[0].name == "C"
    assert results[1].name == "D"
    assert results[2].name == "E"

def test_offset_and_limit():
    data = [
        ["id", "name"],
        ["1", "A"],
        ["2", "B"],
        ["3", "C"],
        ["4", "D"],
        ["5", "E"],
    ]
    results = _make_query(data).offset(1).limit(2).all()
    assert len(results) == 2
    assert results[0].name == "B"
    assert results[1].name == "C"

def test_offset_zero_noop():
    data = [
        ["id", "name"],
        ["1", "A"],
        ["2", "B"],
    ]
    results = _make_query(data).offset(0).all()
    assert len(results) == 2
    assert results[0].name == "A"
    assert results[1].name == "B"
