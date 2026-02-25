from datetime import datetime

from flask import Blueprint, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity

from app.models.enrollment import Enrollment
from app.models.student import Student
from app.services.personalization_service import build_personalized_learning_payload
from app.services.report_service import build_student_report_csv, build_student_report_pdf
from app.utils.constants import STUDENT
from app.utils.helpers import error_response, success_response
from app.utils.role_required import role_required

student_bp = Blueprint("student", __name__)


def _current_student() -> Student | None:
    identity = get_jwt_identity()
    user_type, user_id = identity.split(":")
    if user_type != "student":
        return None
    return Student.query.get(int(user_id))


@student_bp.get("/courses")
@role_required(STUDENT)
def student_courses():
    student = _current_student()
    if not student:
        data, status = error_response("Student profile not found", 404)
        return jsonify(data), status

    enrollments = Enrollment.query.filter_by(student_id=student.student_id).all()
    payload = [
        {
            "course_code": e.course.course_code,
            "course_title": e.course.course_title,
            "credit_units": e.course.credit_units,
            "session": e.session,
            "semester": e.semester,
        }
        for e in enrollments
    ]
    data, status = success_response("Student courses fetched", payload)
    return jsonify(data), status


@student_bp.get("/dashboard")
@role_required(STUDENT)
def dashboard():
    student = _current_student()
    if not student:
        data, status = error_response("Student profile not found", 404)
        return jsonify(data), status

    payload = build_personalized_learning_payload(student)
    data, status = success_response("Student dashboard fetched", payload)
    return jsonify(data), status


@student_bp.get("/personalized-learning")
@role_required(STUDENT)
def personalized_learning():
    student = _current_student()
    if not student:
        data, status = error_response("Student profile not found", 404)
        return jsonify(data), status
    payload = build_personalized_learning_payload(student)
    data, status = success_response("Personalized learning analytics fetched", payload)
    return jsonify(data), status


@student_bp.get("/personalized-learning-report")
@role_required(STUDENT)
def personalized_learning_report():
    student = _current_student()
    if not student:
        data, status = error_response("Student profile not found", 404)
        return jsonify(data), status

    payload = build_personalized_learning_payload(student)
    export_format = (request.args.get("format") or "csv").strip().lower()
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{student.matric_no.replace('/', '_')}_personalized_report_{stamp}"

    try:
        if export_format == "pdf":
            report_bytes = build_student_report_pdf(payload)
            response = make_response(report_bytes)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = f"attachment; filename={base_filename}.pdf"
            return response

        report_bytes = build_student_report_csv(payload)
        response = make_response(report_bytes)
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = f"attachment; filename={base_filename}.csv"
        return response
    except RuntimeError as exc:
        data, status = error_response(str(exc), 501)
        return jsonify(data), status
