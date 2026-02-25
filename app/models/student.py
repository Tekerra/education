from datetime import datetime

from app.extensions import bcrypt, db


class Student(db.Model):
    __tablename__ = "students"

    student_id = db.Column(db.Integer, primary_key=True)
    matric_no = db.Column(db.String(40), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"), nullable=False)
    advisor_id = db.Column(db.Integer, db.ForeignKey("staff.staff_id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    department = db.relationship("Department", back_populates="students")
    advisor = db.relationship("Staff", back_populates="advised_students", foreign_keys=[advisor_id])
    enrollments = db.relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

