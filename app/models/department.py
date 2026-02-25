from app.extensions import db


class Department(db.Model):
    __tablename__ = "departments"

    department_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculties.faculty_id"), nullable=False)

    faculty = db.relationship("Faculty", back_populates="departments")
    staff_members = db.relationship("Staff", back_populates="department")
    students = db.relationship("Student", back_populates="department")
    courses = db.relationship("Course", back_populates="department")

    __table_args__ = (db.UniqueConstraint("name", "faculty_id", name="uq_department_faculty"),)

