import csv
from io import BytesIO, StringIO


def build_student_report_csv(payload: dict) -> bytes:
    buffer = StringIO()
    writer = csv.writer(buffer)

    info = payload.get("student_info", {})
    writer.writerow(["Student Personalized Learning Report"])
    writer.writerow([])
    writer.writerow(["Matric No", info.get("matric_no", "")])
    writer.writerow(["Full Name", info.get("full_name", "")])
    writer.writerow(["Level", info.get("level", "")])
    writer.writerow(["GPA Estimate", payload.get("GPA_estimate", "")])
    writer.writerow(["Risk Level", payload.get("risk_level", "")])
    writer.writerow(["Predicted Outcome", payload.get("predicted_outcome", "")])
    writer.writerow(["Engagement Index", payload.get("engagement_index", "")])
    writer.writerow([])

    writer.writerow(["Risk Breakdown"])
    writer.writerow(["LOW", "MEDIUM", "HIGH"])
    rb = payload.get("risk_breakdown", {})
    writer.writerow([rb.get("LOW", 0), rb.get("MEDIUM", 0), rb.get("HIGH", 0)])
    writer.writerow([])

    writer.writerow(["Course Performance"])
    writer.writerow(["Course Code", "Course Title", "Session", "Semester", "CA", "Exam", "Total", "Grade", "Status"])
    for row in payload.get("course_performance", []):
        writer.writerow(
            [
                row.get("course_code", ""),
                row.get("course_title", ""),
                row.get("session", ""),
                row.get("semester", ""),
                row.get("ca_score", ""),
                row.get("exam_score", ""),
                row.get("total_score", ""),
                row.get("grade", ""),
                row.get("status", ""),
            ]
        )
    writer.writerow([])

    writer.writerow(["Performance Trend"])
    writer.writerow(["Session", "Average Score"])
    for row in payload.get("performance_trend", []):
        writer.writerow([row.get("session", ""), row.get("average_score", "")])
    writer.writerow([])

    writer.writerow(["Personalized Study Plan"])
    study_plan = payload.get("personalized_study_plan", {})
    writer.writerow(["Weekly Target Hours", study_plan.get("weekly_target_hours", "")])
    writer.writerow(["Day", "Focus", "Hours"])
    for row in study_plan.get("weekly_schedule", []):
        writer.writerow([row.get("day", ""), row.get("focus", ""), row.get("hours", "")])
    writer.writerow([])

    writer.writerow(["Intervention Recommendations"])
    for item in payload.get("intervention_recommendations", []):
        writer.writerow([item])
    writer.writerow([])

    writer.writerow(["Next Actions"])
    for item in payload.get("next_actions", []):
        writer.writerow([item])

    return buffer.getvalue().encode("utf-8")


def build_student_report_pdf(payload: dict) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception as exc:
        raise RuntimeError("PDF export unavailable. Install reportlab.") from exc

    stream = BytesIO()
    c = canvas.Canvas(stream, pagesize=A4)
    width, height = A4
    y = height - 50

    def line(text: str, bold: bool = False):
        nonlocal y
        if y < 60:
            c.showPage()
            y = height - 50
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 10)
        c.drawString(45, y, text[:120])
        y -= 14

    info = payload.get("student_info", {})
    line("Student Personalized Learning Report", True)
    y -= 4
    line(f"Matric No: {info.get('matric_no', '')}")
    line(f"Name: {info.get('full_name', '')}")
    line(f"Level: {info.get('level', '')}")
    line(f"GPA Estimate: {payload.get('GPA_estimate', '')}")
    line(f"Risk Level: {payload.get('risk_level', '')}")
    line(f"Predicted Outcome: {payload.get('predicted_outcome', '')}")
    y -= 6

    line("Weak Courses", True)
    weak = payload.get("weak_courses", [])
    if not weak:
        line("No weak courses identified.")
    for row in weak:
        line(f"- {row.get('course_code', '')}: {row.get('status', '')} ({row.get('total_score', '')})")

    y -= 6
    line("Personalized Weekly Plan", True)
    study_plan = payload.get("personalized_study_plan", {}).get("weekly_schedule", [])
    for row in study_plan:
        line(f"- {row.get('day', '')}: {row.get('focus', '')} [{row.get('hours', '')}h]")

    y -= 6
    line("Intervention Recommendations", True)
    for item in payload.get("intervention_recommendations", []):
        line(f"- {item}")

    y -= 6
    line("Next Actions", True)
    for item in payload.get("next_actions", []):
        line(f"- {item}")

    c.save()
    stream.seek(0)
    return stream.read()

