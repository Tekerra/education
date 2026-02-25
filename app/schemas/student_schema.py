from marshmallow import fields, validate

from app.extensions import ma


class StudentRegisterSchema(ma.Schema):
    matric_no = fields.Str(required=True)
    full_name = fields.Str(required=True)
    gender = fields.Str(required=True)
    level = fields.Int(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    department_id = fields.Int(required=True)
    advisor_id = fields.Int(load_default=None)


class StudentSchema(ma.Schema):
    student_id = fields.Int(dump_only=True)
    matric_no = fields.Str(required=True)
    full_name = fields.Str(required=True)
    gender = fields.Str(required=True)
    level = fields.Int(required=True)
    department_id = fields.Int(required=True)
    advisor_id = fields.Int(allow_none=True)
    created_at = fields.DateTime(dump_only=True)

