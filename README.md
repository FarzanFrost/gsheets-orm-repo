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

## Relationship Patterns

The library supports standard relationship mappings through the use of `ForeignKey` and `relationship` descriptors. Below are examples of how to implement different relationship types.

### 1. One-to-One (1:1)

A 1:1 relationship is modeled by defining a `ForeignKey` on the dependent (child) model. Accessing the relationship from the model with the foreign key returns the single related parent model.

```python
class User(Base):
    __tablename__ = 'UserSchema'
    user_id = Column(String, primary_key=True, prefix='USR')
    name = Column(String)

class Profile(Base):
    __tablename__ = 'ProfileSchema'
    profile_id = Column(String, primary_key=True, prefix='PRF')
    bio = Column(String)
    
    # Foreign key references UserSchema
    fr_user_id = Column(String, ForeignKey('UserSchema.user_id'))
    
    # Returns the single User model instance
    user = relationship('User')
```

### 2. One-to-Many (1:M)

A 1:M relationship uses a `ForeignKey` on the child model. The parent model defines a relationship back-populating the child. Accessing the relationship from the parent returns a list of child instances, while accessing it from the child returns the single parent.

```python
class Department(Base):
    __tablename__ = 'DepartmentSchema'
    dept_id = Column(String, primary_key=True, prefix='DEPT')
    name = Column(String)
    
    # 1:M relationship: returns a list of Employee instances
    employees = relationship('Employee', back_populates='department')

class Employee(Base):
    __tablename__ = 'EmployeeSchema'
    emp_id = Column(String, primary_key=True, prefix='EMP')
    name = Column(String)
    
    # Foreign key references DepartmentSchema
    fr_department_id = Column(String, ForeignKey('DepartmentSchema.dept_id'))
    
    # Many-to-One relationship: returns a single Department instance
    department = relationship('Department', back_populates='employees')
```

### 3. Many-to-Many (M:N)

M:N relationships are implemented using an association (mapping) model that contains foreign keys referencing both primary models.

```python
class Student(Base):
    __tablename__ = 'StudentSchema'
    student_id = Column(String, primary_key=True, prefix='STU')
    name = Column(String)

class Course(Base):
    __tablename__ = 'CourseSchema'
    course_id = Column(String, primary_key=True, prefix='CRS')
    title = Column(String)

class StudentCourseMap(Base):
    __tablename__ = 'StudentCourseMapSchema'
    map_id = Column(String, primary_key=True, prefix='MAP')
    
    fr_student_id = Column(String, ForeignKey('StudentSchema.student_id'))
    fr_course_id = Column(String, ForeignKey('CourseSchema.course_id'))
    
    # Singular relationships to traverse from mapping
    student = relationship('Student')
    course = relationship('Course')
```

To query the relationship:

```python
# Fetch all student mappings for a specific course
mappings = session.query(StudentCourseMap).filter_by(fr_course_id=course.course_id).all()

# Retrieve list of Student objects from the mappings
students = [m.student for m in mappings]
```

