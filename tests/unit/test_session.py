import pytest
from unittest.mock import MagicMock
from gsheets_orm.schema.declarative import Base, clear_registry
from gsheets_orm.schema.columns import Column
from gsheets_orm.types.core_types import String, Boolean, Integer
from gsheets_orm.orm.session import Session

class Product(Base):
    __tablename__ = "Product"
    prod_id = Column(String, primary_key=True, prefix="PRD")
    name = Column(String)
    price = Column(Integer)

class User(Base):
    __tablename__ = "User"
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    is_deleted = Column(Boolean, default=False)

@pytest.fixture(autouse=True)
def cleanup():
    clear_registry()

def test_session_identity_map():
    engine = MagicMock()
    session = Session(engine)
    
    p1 = Product(prod_id="PRD_001", name="Laptop", price=1000)
    session.add_to_identity_map(p1)
    
    cached = session.get_from_identity_map(Product, "PRD_001")
    assert cached is p1
    
    assert session.get_from_identity_map(Product, "PRD_999") is None

def test_session_add_new():
    engine = MagicMock()
    dialect = MagicMock()
    engine.connect.return_value = dialect
    session = Session(engine)
    session.dialect = dialect
    
    # Mock worksheet fetch (empty except headers)
    dialect.fetch_worksheet_data.return_value = [
        ["prod_id", "name", "price"]
    ]
    
    p = Product(name="Phone", price=500)
    session.add(p)
    assert p in session._new
    
    session.commit()
    
    # Check that ID was generated: PRD_001
    assert p.prod_id == "PRD_001"
    # Verify append_rows was called with the headers match
    dialect.append_rows.assert_called_once_with("Product", [["PRD_001", "Phone", "500"]])
    assert p not in session._new

def test_session_update_dirty():
    engine = MagicMock()
    dialect = MagicMock()
    engine.connect.return_value = dialect
    session = Session(engine)
    session.dialect = dialect
    
    # Mock headers in the sheet
    dialect.fetch_worksheet_data.return_value = [
        ["prod_id", "name", "price"]
    ]
    
    # Create an object as if it was loaded from the database (row_num=3)
    p = Product(prod_id="PRD_002", name="Tablet", price=300)
    p._row_num = 3
    p._session = session
    session.add_to_identity_map(p)
    
    # Modify property
    p.price = 350
    assert p in session._dirty
    
    session.commit()
    
    # price is the 3rd column -> col C
    dialect.batch_update.assert_called_once_with("Product", [
        {"range": "A3:C3", "values": [["PRD_002", "Tablet", "350"]]}
    ])
    assert p not in session._dirty

def test_session_soft_delete():
    engine = MagicMock()
    dialect = MagicMock()
    engine.connect.return_value = dialect
    session = Session(engine)
    session.dialect = dialect
    
    dialect.fetch_worksheet_data.return_value = [
        ["user_id", "username", "is_deleted"]
    ]
    
    u = User(user_id=1, username="Alice", is_deleted=False)
    u._row_num = 2
    u._session = session
    session.add_to_identity_map(u)
    
    session.delete(u)
    assert u in session._deleted
    
    session.commit()
    
    # Should perform batch update to toggle is_deleted to TRUE
    dialect.batch_update.assert_called_once_with("User", [
        {"range": "A2:C2", "values": [["1", "Alice", "TRUE"]]}
    ])

def test_session_hard_delete_fallback():
    # Product has no 'is_deleted' column, so delete should clear the row
    engine = MagicMock()
    dialect = MagicMock()
    engine.connect.return_value = dialect
    session = Session(engine)
    session.dialect = dialect
    
    dialect.fetch_worksheet_data.return_value = [
        ["prod_id", "name", "price"]
    ]
    
    p = Product(prod_id="PRD_003", name="Speaker", price=50)
    p._row_num = 4
    p._session = session
    session.add_to_identity_map(p)
    
    session.delete(p)
    session.commit()
    
    # Hard delete clears row A4:C4 with empty strings
    dialect.batch_update.assert_called_once_with("Product", [
        {"range": "A4:C4", "values": [["", "", ""]]}
    ])
