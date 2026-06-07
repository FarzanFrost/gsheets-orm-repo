# gsheets-orm

A lightweight Object-Relational Mapper (ORM) backed by Google Sheets.

## Installation

Install the library directly from GitHub into your application environment:

```bash
pip install git+https://github.com/FarzanFrost/gsheets-orm-repo.git
```

## Quick Start Guide

### 1. Define Your Models & Relationships
Create Python classes that inherit from `Base` to map to your Google Sheets worksheets. You can define `ForeignKey` and relationship descriptors to link them.

```python
from gsheets_orm import Base, Column, String, Float, Boolean, ForeignKey, relationship

class Department(Base):
    __tablename__ = 'DepartmentSchema'
    
    dept_id = Column(String, primary_key=True, prefix='DEPT')
    name = Column(String)

class Employee(Base):
    __tablename__ = 'EmployeeSchema' # Must match the Worksheet name exactly
    
    emp_id = Column(String, primary_key=True, prefix='EMP')
    name = Column(String, nullable=False)
    salary = Column(Float, default=0.0)
    
    # 1. Define the physical column holding the foreign key string
    fr_department_id = Column(String, ForeignKey('DepartmentSchema.dept_id'))
    
    # 2. Define the ORM relationship to auto-fetch the actual Department model
    department = relationship('Department', back_populates='employees')

    is_deleted = Column(Boolean, default=False)
```

### 2. Setup the Engine & Session
Initialize the engine using your Google Cloud service account credentials and the target Spreadsheet ID.

```python
from gsheets_orm import create_engine, Session

# Replace with your actual credentials path and spreadsheet ID
URI = 'gsheets://path/to/credentials.json?spreadsheet_id=1BxiMVs0XRYFgCE9_L..._a1b2c3d4'
engine = create_engine(URI)

# Open a session to begin a unit of work
session = Session(bind=engine)
```

### 3. Create Records
Add new instances to the session. They are held in memory until you commit.

```python
new_emp = Employee(name="Alice Smith", salary=65000.0)
session.add(new_emp)

# Execute the batched API call to insert rows into Google Sheets
session.commit()
print(f"Created employee with ID: {new_emp.emp_id}")
```

### 4. Query Records & Use Relationships
Use the fluent Query API to retrieve data. Access related objects smoothly via lazy loading.

```python
# Fetch a single record using conditions
developer = session.query(Employee).filter(Employee.name == "Alice Smith").first()
print(developer.salary)

# The ORM automatically queries the DepartmentSchema worksheet when `.department` is accessed
if developer.department:
    print(f"This employee belongs to: {developer.department.name}")
```

### 5. Update and Delete Records
Modify attributes directly on the objects or mark them for deletion.

```python
# Update
developer.salary += 5000.0

# Soft Delete
bad_employee = session.query(Employee).filter_by(emp_id="EMP_002").first()
if bad_employee:
    session.delete(bad_employee)

# Flush all updates and deletes to Google Sheets in one batch
session.commit()
```
