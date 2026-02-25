from app.utils.constants import RISK_HIGH, RISK_LOW, RISK_MEDIUM


def generate_recommendation(risk_level: str, grade: str) -> str:
    if risk_level == RISK_HIGH:
        return "Immediate intervention required: attend tutorials, meet course advisor weekly, and follow a recovery study plan."
    if risk_level == RISK_MEDIUM:
        return "Moderate risk: increase study hours, attend revision classes, and review weak topics with lecturer support."
    if grade in {"A", "B"}:
        return "Maintain performance: continue consistent study habits and support peers through study groups."
    return "Low risk: keep steady effort and monitor progress with periodic self-assessment."

