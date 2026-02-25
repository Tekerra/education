from app.extensions import db


class University(db.Model):
    __tablename__ = "universities"

    university_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    established_year = db.Column(db.Integer, nullable=False)

    faculties = db.relationship("Faculty", back_populates="university", cascade="all, delete-orphan")

