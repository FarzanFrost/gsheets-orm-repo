import pytest
from gsheets_orm.schema.declarative import Base, get_registered_models, clear_registry
from gsheets_orm.schema.columns import Column
from gsheets_orm.types.core_types import String, Integer

def setup_function():
    clear_registry()

def test_declarative_base_registration():
    class TestUser(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        name = Column(String)

    models = get_registered_models()
    assert "users" in models
    assert models["users"] == TestUser
    
    # Check that columns metadata is populated
    assert hasattr(TestUser, "_columns")
    assert "id" in TestUser._columns
    assert "name" in TestUser._columns
    assert TestUser._primary_keys == ["id"]

def test_declarative_init():
    class TestUser(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        name = Column(String)

    user = TestUser(id=1, name="Alice")
    assert user.id == 1
    assert user.name == "Alice"
