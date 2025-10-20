# LINKED: Enhanced company registration form (business details + admin review integration)
# Added mandatory fields for phone, industry, city, website, and social links without schema changes.
"""Company registration form definition with extended business metadata."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, TextAreaField
from wtforms.fields import EmailField, URLField
from wtforms.validators import DataRequired, Email, Length, Optional, URL

INDUSTRY_CHOICES = [
    ("", "اختر مجال العمل"),
    ("مطاعم", "مطاعم"),
    ("تجارة إلكترونية", "تجارة إلكترونية"),
    ("خدمات طبية", "خدمات طبية"),
    ("تعليم", "تعليم"),
    ("سياحة", "سياحة"),
]

CITY_CHOICES = [
    ("", "اختر المدينة"),
    ("الرياض", "الرياض"),
    ("جدة", "جدة"),
    ("الدمام", "الدمام"),
    ("الخبر", "الخبر"),
    ("المدينة المنورة", "المدينة المنورة"),
]


class CompanyRegistrationForm(FlaskForm):
    """Capture company account details along with core business metadata."""

    company_name = StringField(
        "اسم الشركة",
        validators=[DataRequired(message="هذا الحقل إلزامي."), Length(max=120)],
        render_kw={
            "placeholder": "مثال: شركة النخبة",
            "autocomplete": "organization",
            "class": "input-control",
        },
    )
    email = EmailField(
        "البريد الإلكتروني الرسمي",
        validators=[DataRequired(message="هذا الحقل إلزامي."), Email()],
        render_kw={
            "placeholder": "company@example.com",
            "autocomplete": "email",
            "class": "input-control",
        },
    )
    password = PasswordField(
        "كلمة المرور",
        validators=[DataRequired(message="هذا الحقل إلزامي."), Length(min=6)],
        render_kw={
            "placeholder": "••••••••",
            "autocomplete": "new-password",
            "class": "input-control",
        },
    )
    phone_number = StringField(
        "رقم الجوال",
        validators=[DataRequired(message="هذا الحقل إلزامي."), Length(min=8)],
        render_kw={
            "placeholder": "05XXXXXXXX",
            "inputmode": "tel",
            "class": "input-control",
        },
    )
    industry = SelectField(
        "مجال عمل الشركة",
        choices=INDUSTRY_CHOICES,
        validators=[DataRequired(message="اختر مجال العمل")],
        render_kw={"class": "input-control"},
    )
    city = SelectField(
        "اسم المدينة",
        choices=CITY_CHOICES,
        validators=[DataRequired(message="اختر المدينة")],
        render_kw={"class": "input-control"},
    )
    website_url = URLField(
        "رابط الموقع الإلكتروني",
        validators=[Optional(), URL(message="الرجاء إدخال رابط صحيح.")],
        render_kw={"placeholder": "https://example.com", "class": "input-control"},
    )
    social_url = URLField(
        "رابط التواصل الاجتماعي",
        validators=[DataRequired(message="هذا الحقل إلزامي."), URL(message="الرجاء إدخال رابط صحيح.")],
        render_kw={
            "placeholder": "https://instagram.com/yourbrand",
            "class": "input-control",
        },
    )
    description = TextAreaField(
        "وصف مختصر",
        validators=[Optional()],
        render_kw={
            "placeholder": "عرفنا عن عروضك المميزة وفريقك.",
            "rows": 4,
            "class": "input-control",
        },
    )


__all__ = [
    "CompanyRegistrationForm",
    "INDUSTRY_CHOICES",
    "CITY_CHOICES",
]
