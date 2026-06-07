import os
import pytest
from datetime import datetime
from gsheets_orm import Base, Column, String, Integer, Boolean, DateTime, create_engine, Session

# Check if integration test environment is available
creds_path = os.getenv("GSHEETS_CREDENTIALS_PATH")
spreadsheet_id = os.getenv("GSHEETS_SPREADSHEET_ID")
run_integration = creds_path is not None and spreadsheet_id is not None

pytestmark = pytest.mark.skipif(
    not run_integration,
    reason="Integration tests require GSHEETS_CREDENTIALS_PATH and GSHEETS_SPREADSHEET_ID env vars"
)

class Member(Base):
    __tablename__ = "IntegrationMember"
    member_id = Column(String, primary_key=True, prefix="MEM")
    name = Column(String)
    age = Column(Integer)
    joined_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

def test_live_orm_flow():
    # Construct URI
    # gsheets://path/to/creds.json?spreadsheet_id=XYZ
    uri = f"gsheets://{creds_path}?spreadsheet_id={spreadsheet_id}"
    engine = create_engine(uri)
    session = Session(engine)
    
    # 1. Add new members
    m1 = Member(name="Integration Alice", age=28, joined_at=datetime(2026, 6, 6, 12, 0, 0))
    m2 = Member(name="Integration Bob", age=35, joined_at=datetime(2026, 6, 6, 13, 0, 0))
    session.add(m1)
    session.add(m2)
    session.commit()
    
    # Ensure IDs are auto-generated
    assert m1.member_id is not None
    assert m2.member_id is not None
    
    # 2. Query them back
    queried_alice = session.query(Member).filter_by(name="Integration Alice").first()
    assert queried_alice is not None
    assert queried_alice.age == 28
    
    # 3. Update member
    queried_alice.age = 29
    session.commit()
    
    # Verify updated value
    refetched = session.query(Member).filter_by(member_id=queried_alice.member_id).first()
    assert refetched.age == 29
    
    # 4. Cleanup (Hard delete)
    session.delete(m1)
    session.delete(m2)
    session.commit()
