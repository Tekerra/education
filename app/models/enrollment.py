from app.extensions import db


class Enrollment(db.Model):
    __tablename__ = "enrollments"

    enrollment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.course_id"), nullable=False)
    session = db.Column(db.String(20), nullable=False)
    semester = db.Column(db.String(20), nullable=False)

    student = db.relationship("Student", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")
    assessment = db.relationship("Assessment", back_populates="enrollment", uselist=False, cascade="all, delete-orphan")
    analytics_result = db.relationship(
        "AnalyticsResult",
        back_populates="enrollment",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", "session", "semester", name="uq_student_course_session"),
    )

