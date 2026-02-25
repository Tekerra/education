from datetime import datetime

from app.extensions import bcrypt, db
from app.utils.constants import STAFF_ROLES


class Staff(db.Model):
    __tablename__ = "staff"

    staff_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    department = db.relationship("Department", back_populates="staff_members")
    advised_students = db.relationship("Student", back_populates="advisor", foreign_keys="Student.advisor_id")
    courses = db.relationship("Course", back_populates="lecturer")

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    def validate_role(self) -> None:
        if self.role not in STAFF_ROLES:
            raise ValueError(f"Invalid staff role: {self.role}")

