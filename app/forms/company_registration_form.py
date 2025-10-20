# LINKED: Added admin-managed dropdown system for Cities and Industries.
# Introduced unified Settings Service and admin UI for dynamic list management.
# LINKED: Enhanced company registration form (business details + admin review integration)
# Added mandatory fields for phone, industry, city, website, and social links without schema changes.
"""Company registration form definition with extended business metadata."""

from __future__ import annotations

from typing import Iterator, List, Sequence, Tuple

from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, TextAreaField
from wtforms.fields import EmailField, URLField
from wtforms.validators import DataRequired, Email, Length, Optional, URL

from app.services.settings_service import get_list


class _DynamicChoiceAdapter(Sequence[Tuple[str, str]]):
    """Adapter returning fresh choices for dynamic dropdowns."""

    def __init__(self, list_type: str, placeholder: str) -> None:
        self.list_type = list_type
        self.placeholder = placeholder

    def _current(self) -> List[Tuple[str, str]]:
        values = get_list(self.list_type)
        return [("", self.placeholder)] + [(value, value) for value in values]

    def as_list(self) -> List[Tuple[str, str]]:
        """Return the current choices as a list of tuples."""

        return list(self._current())

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        return iter(self._current())

    def __len__(self) -> int:  # pragma: no cover - trivial adapter
        return len(self._current())

    def __getitem__(self, index: int) -> Tuple[str, str]:  # pragma: no cover - trivial adapter
        return self._current()[index]


INDUSTRY_CHOICES: Sequence[Tuple[str, str]] = _DynamicChoiceAdapter(
    "industries", "اختر مجال العمل"
)
CITY_CHOICES: Sequence[Tuple[str, str]] = _DynamicChoiceAdapter("cities", "اختر المدينة")


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
        choices=[],
        validators=[DataRequired(message="اختر مجال العمل")],
        render_kw={"class": "input-control"},
    )
    city = SelectField(
        "اسم المدينة",
        choices=[],
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


    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.industry.choices = list(INDUSTRY_CHOICES)
        self.city.choices = list(CITY_CHOICES)


__all__ = ["CompanyRegistrationForm", "INDUSTRY_CHOICES", "CITY_CHOICES"]
