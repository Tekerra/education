from collections import defaultdict

from app.models.student import Student
from app.services.aggregation_service import student_gpa_estimate


def _course_status(total_score: float) -> str:
    if total_score < 40:
        return "CRITICAL"
    if total_score < 50:
        return "AT_RISK"
    if total_score < 65:
        return "STABLE"
    return "STRONG"


def _predict_outcome(gpa: float, high_risk_count: int, medium_risk_count: int) -> str:
    if high_risk_count >= 2 or gpa < 2.0:
        return "Needs urgent academic intervention"
    if high_risk_count == 1 or medium_risk_count >= 2 or gpa < 3.0:
        return "Can improve with targeted support"
    return "On track for strong academic standing"


def build_personalized_learning_payload(student: Student) -> dict:
    enrollments = list(student.enrollments)
    course_performance = []
    score_rows = []
    weak_courses = []
    strong_courses = []
    session_scores = defaultdict(list)
    risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}

    latest_grade = None
    latest_risk = None
    latest_recommendation = None
    latest_marker = None

    for enrollment in enrollments:
        course = enrollment.course
        assessment = enrollment.assessment
        analytics = enrollment.analytics_result

        if analytics and analytics.risk_level in risk_counts:
            risk_counts[analytics.risk_level] += 1

        if assessment:
            status = _course_status(assessment.total_score)
            row = {
                "course_code": course.course_code,
                "course_title": course.course_title,
                "credit_units": course.credit_units,
                "session": enrollment.session,
                "semester": enrollment.semester,
                "ca_score": assessment.ca_score,
                "exam_score": assessment.exam_score,
                "total_score": assessment.total_score,
                "grade": assessment.grade,
                "status": status,
            }
            course_performance.append(row)
            score_rows.append(
                {
                    "course_code": course.course_code,
                    "ca_score": assessment.ca_score,
                    "exam_score": assessment.exam_score,
                    "total_score": assessment.total_score,
                }
            )
            session_scores[enrollment.session].append(float(assessment.total_score))

            if status in {"CRITICAL", "AT_RISK"}:
                weak_courses.append(
                    {
                        "course_code": course.course_code,
                        "course_title": course.course_title,
                        "total_score": assessment.total_score,
                        "status": status,
                    }
                )
            if status == "STRONG":
                strong_courses.append(
                    {
                        "course_code": course.course_code,
                        "course_title": course.course_title,
                        "total_score": assessment.total_score,
                    }
                )

            marker = assessment.created_at
            if latest_marker is None or marker > latest_marker:
                latest_marker = marker
                latest_grade = assessment.grade

        if analytics:
            marker = analytics.date_computed
            if latest_marker is None or marker > latest_marker:
                latest_marker = marker
                latest_risk = analytics.risk_level
                latest_recommendation = analytics.recommendation

    trend = []
    for session in sorted(session_scores.keys()):
        values = session_scores[session]
        trend.append(
            {
                "session": session,
                "average_score": round(sum(values) / len(values), 2),
            }
        )

    gpa = student_gpa_estimate(student.student_id)
    assessed_count = len(course_performance)
    enrolled_count = len(enrollments)
    engagement_index = round((assessed_count / enrolled_count) * 100, 2) if enrolled_count else 0.0

    weekly_hours = 8 + (2 * len(weak_courses)) + (2 * risk_counts["HIGH"]) + risk_counts["MEDIUM"]
    weekly_hours = min(max(weekly_hours, 8), 26)

    study_plan = [
        {"day": "Monday", "focus": "Review lecture notes and summarize key concepts", "hours": 2},
        {"day": "Tuesday", "focus": "Practice past questions from weak courses", "hours": 2},
        {"day": "Wednesday", "focus": "Group study and peer explanation", "hours": 2},
        {"day": "Thursday", "focus": "Targeted revision for identified weak topics", "hours": 2},
        {"day": "Friday", "focus": "Mini self-test and reflection", "hours": 1},
    ]

    interventions = [
        "Meet course advisor once weekly if risk is MEDIUM or HIGH",
        "Attend departmental tutorial classes for weak courses",
        "Set bi-weekly progress checkpoints with measurable targets",
    ]
    if risk_counts["HIGH"] >= 1:
        interventions.insert(0, "Immediate remediation plan required with lecturer and advisor")

    next_actions = [
        "Complete one practice test before next class",
        "Spend at least 30 minutes daily on weak topic revision",
        "Track weekly goals and update progress every Friday",
    ]

    return {
        "student_info": {
            "student_id": student.student_id,
            "matric_no": student.matric_no,
            "full_name": student.full_name,
            "level": student.level,
            "department_id": student.department_id,
        },
        "enrolled_courses": [
            {
                "course_code": e.course.course_code,
                "course_title": e.course.course_title,
                "credit_units": e.course.credit_units,
                "session": e.session,
                "semester": e.semester,
            }
            for e in enrollments
        ],
        "scores": score_rows,
        "grade": latest_grade,
        "risk_level": latest_risk,
        "recommendation": latest_recommendation,
        "GPA_estimate": gpa,
        "engagement_index": engagement_index,
        "risk_breakdown": risk_counts,
        "performance_trend": trend,
        "course_performance": course_performance,
        "weak_courses": weak_courses,
        "strength_courses": strong_courses,
        "predicted_outcome": _predict_outcome(gpa, risk_counts["HIGH"], risk_counts["MEDIUM"]),
        "personalized_study_plan": {
            "weekly_target_hours": weekly_hours,
            "weekly_schedule": study_plan,
        },
        "intervention_recommendations": interventions,
        "next_actions": next_actions,
    }

