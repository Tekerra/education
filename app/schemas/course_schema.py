from marshmallow import fields

from app.extensions import ma


class CourseSchema(ma.Schema):
    course_id = fields.Int(dump_only=True)
    course_code = fields.Str(required=True)
    course_title = fields.Str(required=True)
    credit_units = fields.Int(required=True)
    semester = fields.Str(required=True)
    department_id = fields.Int(required=True)
    lecturer_id = fields.Int(allow_none=True)

