import os
import pytest
from datetime import datetime
from gsheets_orm import Base, Column, String, Integer, Float, Boolean, DateTime, ForeignKey, relationship, create_engine, Session

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

class UserModel(Base):
    __tablename__ = "IntegrationUser"
    user_id = Column(String, primary_key=True, prefix="USR")
    name = Column(String)

    # Reverse relationship (1:M)
    accounts = relationship("AccountModel", back_populates="owner")

class AccountModel(Base):
    __tablename__ = "IntegrationAccount"
    acc_id = Column(String, primary_key=True, prefix="ACC")
    name = Column(String)
    balance = Column(Float, default=0.0)

    # 1:M Relationship (User -> Account)
    fr_user_id = Column(String, ForeignKey("IntegrationUser.user_id"))
    owner = relationship("UserModel", back_populates="accounts")

    # 1:M Self-Referencing (Parent Account -> Virtual Sub-Account)
    fr_parent_acc_id = Column(String, ForeignKey("IntegrationAccount.acc_id"))
    parent_account = relationship("AccountModel")

class AccountUserMapModel(Base):
    """Association table for M:N relationships (Shared Accounts)"""
    __tablename__ = "IntegrationAccountUserMap"
    map_id = Column(String, primary_key=True, prefix="MAP")

    fr_acc_id = Column(String, ForeignKey("IntegrationAccount.acc_id"))
    fr_user_id = Column(String, ForeignKey("IntegrationUser.user_id"))

    account = relationship("AccountModel")
    user = relationship("UserModel")

@pytest.fixture
def session():
    uri = f"gsheets://{creds_path}?spreadsheet_id={spreadsheet_id}"
    engine = create_engine(uri)
    return Session(engine)

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

def test_one_to_many_relationship(session):
    # 1. Create Parent — commit first so user_id is assigned before FK assignment
    user = UserModel(name="Charlie")
    session.add(user)
    session.commit()

    # 2. Create Children — set relationship descriptor after construction
    acc1 = AccountModel(name="Checking", balance=100.0)
    acc1.owner = user
    acc2 = AccountModel(name="Savings", balance=5000.0)
    acc2.owner = user
    session.add(acc1)
    session.add(acc2)

    # 3. Batch Commit
    session.commit()

    # 4. Verify ID resolution
    assert acc1.fr_user_id == user.user_id
    assert acc2.fr_user_id == user.user_id

    # 5. Test Lazy Loading (clear identity map to force a live query)
    session._identity_map.clear()
    fetched_acc = session.query(AccountModel).filter_by(acc_id=acc1.acc_id).first()

    # Accessing .owner should fetch from IntegrationUser sheet
    assert fetched_acc.owner is not None
    assert fetched_acc.owner.name == "Charlie"

def test_many_to_many_mapping(session):
    # 1. Create entities
    user_diana = UserModel(name="Diana")
    user_evan = UserModel(name="Evan")
    joint_acc = AccountModel(name="Joint Expenses", balance=1000.0)

    session.add(user_diana)
    session.add(user_evan)
    session.add(joint_acc)
    session.commit()  # Commit to generate base IDs

    # 2. Create mappings using FK columns directly (safe — no relationship kwarg in __init__)
    map1 = AccountUserMapModel(fr_acc_id=joint_acc.acc_id, fr_user_id=user_diana.user_id)
    map2 = AccountUserMapModel(fr_acc_id=joint_acc.acc_id, fr_user_id=user_evan.user_id)
    session.add(map1)
    session.add(map2)
    session.commit()

    # 3. Query mappings
    session._identity_map.clear()
    mappings = session.query(AccountUserMapModel).filter_by(fr_acc_id=joint_acc.acc_id).all()

    assert len(mappings) == 2
    # Test relationship traversal from mapping table
    fetched_users = [m.user.name for m in mappings]
    assert "Diana" in fetched_users
    assert "Evan" in fetched_users

def test_self_referencing_relationship(session):
    # 1. Create Parent
    main_acc = AccountModel(name="Main Savings", balance=10000.0)
    session.add(main_acc)
    session.commit()

    # 2. Create Virtual Child — fr_parent_acc_id is a Column, safe to pass directly
    vacation_fund = AccountModel(name="Vacation Fund", balance=2000.0, fr_parent_acc_id=main_acc.acc_id)
    session.add(vacation_fund)
    session.commit()

    # 3. Query and traverse up
    session._identity_map.clear()
    fetched_virtual = session.query(AccountModel).filter_by(name="Vacation Fund").first()

    assert fetched_virtual.fr_parent_acc_id == main_acc.acc_id
    # Test relationship descriptor
    assert fetched_virtual.parent_account is not None
    assert fetched_virtual.parent_account.name == "Main Savings"

def test_batch_commit_across_multiple_sheets(session):
    """
    Ensures that committing across multiple models does not fail
    and handles potential backoff/retry mechanisms smoothly.
    """
    for i in range(5):
        u = UserModel(name=f"BatchUser_{i}")
        session.add(u)
        session.commit()  # Commit user first so acc.owner FK resolves

        a = AccountModel(name=f"BatchAcc_{i}")
        a.owner = u
        session.add(a)
        session.commit()  # Commit account so map FK resolves

        m = AccountUserMapModel(fr_acc_id=a.acc_id, fr_user_id=u.user_id)
        session.add(m)

    # This commit writes the final mapping batch to IntegrationAccountUserMap.
    # Dialect must succeed without raising 429 Errors.
    session.commit()

    # Verification
    assert len(session.query(UserModel).filter(UserModel.name.contains("BatchUser")).all()) == 5
