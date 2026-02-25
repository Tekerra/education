from app.extensions import db


class Course(db.Model):
    __tablename__ = "courses"

    course_id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    course_title = db.Column(db.String(150), nullable=False)
    credit_units = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey("staff.staff_id"), nullable=True)

    department = db.relationship("Department", back_populates="courses")
    lecturer = db.relationship("Staff", back_populates="courses")
    enrollments = db.relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")

