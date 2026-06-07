import os
import pytest
from gsheets_orm.schema.declarative import Base, clear_registry
from gsheets_orm.schema.columns import Column
from gsheets_orm.types.core_types import String, Integer

class Assignment(Base):
    __tablename__ = 'Assignments'
    
    # Composite Primary Keys
    project_id = Column(String, primary_key=True)
    employee_id = Column(String, primary_key=True)
    
    # Validation Rules
    role_code = Column(String, min_length=3, max_length=5, regex=r'^[A-Z]+$')
    hours = Column(Integer, nullable=False)

creds_path = os.getenv("GSHEETS_CREDENTIALS_PATH")
spreadsheet_id = os.getenv("GSHEETS_SPREADSHEET_ID")
run_integration = creds_path is not None and spreadsheet_id is not None

@pytest.fixture(autouse=True)
def setup_teardown(live_session):
    clear_registry()
    # Let Base.__init_subclass__ register the models
    class AssignmentLocal(Assignment):
        pass

    # Ensure Assignments tab exists for the test, clear it if it does
    try:
        live_session.dialect.fetch_worksheet_data("Assignments")
        # Clear existing data except headers if any
        headers = list(AssignmentLocal._columns.keys())
        live_session.dialect.client.open_by_key(live_session.dialect.spreadsheet_id).worksheet("Assignments").clear()
        live_session.dialect.append_rows("Assignments", [headers])
    except Exception:
        # Create sheet
        headers = list(AssignmentLocal._columns.keys())
        sheet = live_session.dialect.client.open_by_key(live_session.dialect.spreadsheet_id).add_worksheet(title="Assignments", rows="100", cols="20")
        sheet.append_row(headers)
    
    yield
    
    # Teardown: delete the Assignments tab to clean up
    try:
        sheet = live_session.dialect.client.open_by_key(live_session.dialect.spreadsheet_id).worksheet("Assignments")
        live_session.dialect.client.open_by_key(live_session.dialect.spreadsheet_id).del_worksheet(sheet)
    except Exception:
        pass

@pytest.mark.skipif(not run_integration, reason="Missing credentials")
def test_live_composite_keys_and_validation(live_session):
    # 1. Test Descriptor Regex Validation (Should fail locally before network call)
    with pytest.raises(ValueError, match="Regex mismatch"):
        Assignment(project_id="P1", employee_id="E1", role_code="invalid-role")
    
    # 2. Test Composite PKs Live
    valid_assignment = Assignment(project_id="P1", employee_id="E1", role_code="DEV", hours=10)
    live_session.add(valid_assignment)
    live_session.commit()
    
    # 3. Query by composite keys
    fetched = live_session.query(Assignment).filter_by(project_id="P1", employee_id="E1").first()
    assert fetched is not None
    assert fetched.hours == 10
