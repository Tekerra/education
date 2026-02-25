from io import StringIO

import pandas as pd

from app.extensions import db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.services.analytics_service import compute_and_store_analytics

REQUIRED_COLUMNS = {"matric_no", "course_code", "ca_score", "exam_score"}


def process_result_csv(file_storage, lecturer_id: int, session: str, semester: str):
    content = file_storage.read().decode("utf-8")
    df = pd.read_csv(StringIO(content))
    columns = {c.strip() for c in df.columns}
    if not REQUIRED_COLUMNS.issubset(columns):
        missing = list(REQUIRED_COLUMNS - columns)
        raise ValueError(f"CSV missing required columns: {missing}")

    summary = {"processed": 0, "created_enrollments": 0, "errors": []}

    for idx, row in df.iterrows():
        try:
            matric_no = str(row["matric_no"]).strip()
            course_code = str(row["course_code"]).strip().upper()
            ca_score = float(row["ca_score"])
            exam_score = float(row["exam_score"])

            student = Student.query.filter_by(matric_no=matric_no).first()
            if not student:
                raise ValueError(f"Student not found for matric_no={matric_no}")

            course = Course.query.filter_by(course_code=course_code).first()
            if not course:
                raise ValueError(f"Course not found for course_code={course_code}")
            if course.lecturer_id != lecturer_id:
                raise ValueError(f"Unauthorized upload for course={course_code}")

            enrollment = Enrollment.query.filter_by(
                student_id=student.student_id,
                course_id=course.course_id,
                session=session,
                semester=semester,
            ).first()
            if not enrollment:
                enrollment = Enrollment(
                    student_id=student.student_id,
                    course_id=course.course_id,
                    session=session,
                    semester=semester,
                )
                db.session.add(enrollment)
                db.session.flush()
                summary["created_enrollments"] += 1

            compute_and_store_analytics(enrollment=enrollment, ca_score=ca_score, exam_score=exam_score)
            summary["processed"] += 1
        except Exception as exc:
            summary["errors"].append({"row": int(idx) + 1, "error": str(exc)})

    db.session.commit()
    return summary

