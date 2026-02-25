from app.extensions import db


class Faculty(db.Model):
    __tablename__ = "faculties"

    faculty_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    university_id = db.Column(db.Integer, db.ForeignKey("universities.university_id"), nullable=False)

    university = db.relationship("University", back_populates="faculties")
    departments = db.relationship("Department", back_populates="faculty", cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint("name", "university_id", name="uq_faculty_university"),)

