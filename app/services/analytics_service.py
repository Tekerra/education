from datetime import datetime

from app.extensions import db
from app.models.analytics_result import AnalyticsResult
from app.models.assessment import Assessment
from app.models.enrollment import Enrollment
from app.services.recommendation_engine import generate_recommendation
from app.utils.helpers import compute_grade, compute_risk_level, compute_total


def compute_and_store_analytics(enrollment: Enrollment, ca_score: float, exam_score: float):
    total_score = compute_total(ca_score, exam_score)
    grade = compute_grade(total_score)
    risk_level = compute_risk_level(total_score)
    recommendation = generate_recommendation(risk_level, grade)

    assessment = enrollment.assessment
    if assessment is None:
        assessment = Assessment(
            enrollment_id=enrollment.enrollment_id,
            ca_score=ca_score,
            exam_score=exam_score,
            total_score=total_score,
            grade=grade,
        )
        db.session.add(assessment)
    else:
        assessment.ca_score = ca_score
        assessment.exam_score = exam_score
        assessment.total_score = total_score
        assessment.grade = grade

    analytics = enrollment.analytics_result
    if analytics is None:
        analytics = AnalyticsResult(
            enrollment_id=enrollment.enrollment_id,
            risk_level=risk_level,
            recommendation=recommendation,
            date_computed=datetime.utcnow(),
        )
        db.session.add(analytics)
    else:
        analytics.risk_level = risk_level
        analytics.recommendation = recommendation
        analytics.date_computed = datetime.utcnow()

    db.session.flush()
    return {
        "enrollment_id": enrollment.enrollment_id,
        "total_score": total_score,
        "grade": grade,
        "risk_level": risk_level,
        "recommendation": recommendation,
    }

