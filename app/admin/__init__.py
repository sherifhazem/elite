# -*- coding: utf-8 -*-
"""Admin blueprint package initialization for dashboard routes."""

from flask import Blueprint

# تعريف Blueprint الأدمن بمسارات صحيحة للقوالب والملفات الثابتة
admin = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates",   # يشير إلى app/admin/templates
    static_folder="../static"      # يستخدم ملفات CSS/JS من app/static
)

# تحميل المسارات الفرعية وربطها بنفس Blueprint
from . import routes  # المسارات العامة للأدمن
from . import routes_communications  # مركز الرسائل
from . import routes_notifications   # الإشعارات
from . import routes_companies       # إدارة الشركات
from . import routes_reports         # التقارير

__all__ = ["admin"]
