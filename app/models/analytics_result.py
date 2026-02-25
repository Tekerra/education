from datetime import datetime

from app.extensions import db


class AnalyticsResult(db.Model):
    __tablename__ = "analytics_results"

    analytics_id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey("enrollments.enrollment_id"), nullable=False, unique=True)
    risk_level = db.Column(db.String(20), nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    date_computed = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    enrollment = db.relationship("Enrollment", back_populates="analytics_result")

