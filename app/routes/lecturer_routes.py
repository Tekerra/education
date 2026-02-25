from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func

from app.extensions import db
from app.models.analytics_result import AnalyticsResult
from app.models.assessment import Assessment
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.services.csv_import_service import process_result_csv
from app.utils.constants import LECTURER
from app.utils.helpers import error_response, success_response
from app.utils.role_required import role_required

lecturer_bp = Blueprint("lecturer", __name__)


def _current_lecturer_id() -> int:
    identity = get_jwt_identity()
    _, user_id = identity.split(":")
    return int(user_id)


@lecturer_bp.post("/upload-results")
@role_required(LECTURER)
def upload_results():
    if "file" not in request.files:
        data, status = error_response("CSV file is required", 400)
        return jsonify(data), status

    csv_file = request.files["file"]
    session = (request.form.get("session") or "").strip()
    semester = (request.form.get("semester") or "").strip()
    if not session or not semester:
        data, status = error_response("session and semester are required", 400)
        return jsonify(data), status

    lecturer_id = _current_lecturer_id()
    try:
        summary = process_result_csv(
            file_storage=csv_file,
            lecturer_id=lecturer_id,
            session=session,
            semester=semester,
        )
        data, status = success_response("CSV processed successfully", summary, 201)
        return jsonify(data), status
    except Exception as exc:
        db.session.rollback()
        data, status = error_response("Failed to process CSV", 400, str(exc))
        return jsonify(data), status


@lecturer_bp.get("/class-analytics")
@role_required(LECTURER)
def class_analytics():
    lecturer_id = _current_lecturer_id()
    courses = Course.query.filter_by(lecturer_id=lecturer_id).all()
    results = []
    for c in courses:
        total = (
            db.session.query(func.count(Assessment.assessment_id))
            .join(Enrollment, Enrollment.enrollment_id == Assessment.enrollment_id)
            .filter(Enrollment.course_id == c.course_id)
            .scalar()
            or 0
        )
        passed = (
            db.session.query(func.count(Assessment.assessment_id))
            .join(Enrollment, Enrollment.enrollment_id == Assessment.enrollment_id)
            .filter(Enrollment.course_id == c.course_id, Assessment.total_score >= 50)
            .scalar()
            or 0
        )
        at_risk = (
            db.session.query(func.count(AnalyticsResult.analytics_id))
            .join(Enrollment, Enrollment.enrollment_id == AnalyticsResult.enrollment_id)
            .filter(Enrollment.course_id == c.course_id, AnalyticsResult.risk_level.in_(["HIGH", "MEDIUM"]))
            .scalar()
            or 0
        )
        pass_rate = round((passed / total) * 100, 2) if total else 0.0
        results.append(
            {
                "course_id": c.course_id,
                "course_code": c.course_code,
                "course_title": c.course_title,
                "pass_rate": pass_rate,
                "at_risk_students": at_risk,
                "records": total,
            }
        )

    data, status = success_response("Class analytics fetched", results)
    return jsonify(data), status

