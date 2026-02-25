from app.utils.constants import GRADE_SCALE, RISK_HIGH, RISK_LOW, RISK_MEDIUM


def compute_total(ca_score: float, exam_score: float) -> float:
    return round(float(ca_score) + float(exam_score), 2)


def compute_grade(total_score: float) -> str:
    for boundary, grade in GRADE_SCALE:
        if total_score >= boundary:
            return grade
    return "F"


def compute_risk_level(total_score: float) -> str:
    if total_score < 40:
        return RISK_HIGH
    if 40 <= total_score <= 49:
        return RISK_MEDIUM
    return RISK_LOW


def success_response(message: str, data=None, status: int = 200):
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return payload, status


def error_response(message: str, status: int = 400, error: str | None = None):
    payload = {"message": message}
    if error:
        payload["error"] = error
    return payload, status

