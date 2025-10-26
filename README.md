# ELITE Backend

إصدار مبسّط يوضح كيفية إعداد وتشغيل خادم ELITE المسؤول عن إدارة العروض، الشركات، وأدوار المستخدمين. يوفر المشروع هيكل Flask منظمًا، تكاملًا مع PostgreSQL وRedis، ونقاط نهاية جاهزة لمتابعة الصحة وإدارة الحسابات.

## نظرة عامة
- **Flask** يستخدم كأساس لتجميع البلوبرنتات الخاصة بالأعضاء، الشركات، ولوحة التحكم الإدارية.
- **PostgreSQL** هو قاعدة البيانات الرئيسية ويتم التعامل معها عبر SQLAlchemy وFlask-Migrate.
- **Redis** يدعم المهام الخلفية والإشعارات المؤقتة.
- **البريد الإلكتروني** مُهيأ عبر SMTP لإرسال رسائل التحقق واستعادة كلمة المرور.

## تحديث: تجربة لوحة التحكم الإدارية
- تم إعادة تصميم صفحة النظرة العامة للوحة الإدارة بما يتماشى مع التصميم العام للتطبيق عبر `dashboard/admin_base.html`.
- الواجهة الجديدة تضيف قسمًا ترحيبيًا، وبطاقات إحصائية عصرية، وتدفقات عمل واضحة تغطي إدارة الأعضاء، الشركاء، والعروض.
- تمت إضافة عناصر مرئية مثل المخطط الزمني والأهداف لضمان متابعة المهام اليومية دون الحاجة إلى مصادر خارجية.

## متطلبات التشغيل
- Python 3.11
- PostgreSQL 13 أو أحدث
- Redis متاح محليًا أو عبر خدمة خارجية

## Fix: Resolved Admin Template Shadowing
- Renamed admin base layout to dashboard/admin_base.html.
- Updated all admin templates to extend "dashboard/admin_base.html".
- Removed duplicate dashboard/base.html that conflicted with global template.
- Restored correct sidebar and Companies tab visibility for admin and superadmin roles.

## Fix: AnonymousUserMixin AttributeError in Notifications
- Added @login_required decorator to /admin/api/notifications route.
- Added explicit check for current_user.is_authenticated.
- Prevented crashes when fetching notifications without a valid session.

## Fix: Unified Company Portal Blueprint Name
- Renamed company_portal_bp → company_portal for clarity and consistency.
- Updated registration in app/__init__.py.
- Fixed all url_for calls to use 'company_portal.dashboard'.

## Fix: Restored Company Portal Endpoint Compatibility
- Added endpoint="list_offers" to /company/offers route.
- Ensured url_for('company_portal.list_offers') resolves correctly.
- Unified endpoint names (dashboard, offers, redemptions) across company_portal blueprint.

## Refactor: Unified Blueprint Naming Across ELITE
- Standardized all blueprint names (removed "_bp" suffix).
- Updated registrations in app/__init__.py.
- Updated all url_for() references across templates and routes.
- Ensured consistent naming convention:
  admin, auth, company_portal, portal, reports, offers, companies, users, redemption, notifications.

## Security Fix: Unified Admin Route Protection
- Applied @admin_required decorator to all admin routes (companies, offers, users, reports, communications).
- Ensured consistent enforcement of admin-only access.
- Verified admin_required decorator imported from app.services.roles.
- Prevented non-admin users from accessing /admin/* routes.

## Refactor: Unified Endpoint Naming Convention
- Added explicit endpoint names across all blueprints.
- Standardized endpoint naming by module:  admin.*, auth.*, company_portal.*, portal.*, reports.*, offers.*, users.*.
- Eliminated all ambiguous endpoints to prevent BuildError exceptions.

## التثبيت السريع
1. أنشئ بيئة افتراضية ثم فعّلها:
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```
2. ثبّت الحزم المطلوبة من `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
3. حدّد متغيرات البيئة (انظر الجدول أدناه) داخل ملف `.env` في جذر المشروع.
4. ثبّت قاعدة البيانات وشغّل الترحيلات:
   ```bash
   flask db upgrade
   ```
5. شغّل الخادم التطويري:
   ```bash
   flask run
   ```
   أو عبر:
   ```bash
   python run.py
   ```

## متغيرات البيئة الأساسية
| المتغير | الوصف |
|---------|--------|
| `SECRET_KEY` | مفتاح التشفير لجلسات Flask. |
| `SQLALCHEMY_DATABASE_URI` | سلسلة الاتصال بقاعدة بيانات PostgreSQL. |
| `REDIS_URL` | عنوان خادم Redis المستخدم للتخزين المؤقت والمهام. |
| `TIMEZONE` | المنطقة الزمنية الافتراضية للمهام المجدولة. |
| `MAIL_SERVER` | مضيف SMTP (مثل `smtp.gmail.com`). |
| `MAIL_PORT` | منفذ SMTP (عادة `587`). |
| `MAIL_USERNAME` | اسم المستخدم لحساب البريد المرسل. |
| `MAIL_PASSWORD` | كلمة مرور التطبيق أو بيانات اعتماد SMTP. |
| `MAIL_DEFAULT_SENDER` | البريد والاسم الظاهر في الرسائل الصادرة. |

احفظ القيم الحساسة خارج التحكم بالنسخ وراجع مسؤول البنية التحتية قبل النشر الإنتاجي.

## بنية المشروع المختصرة
```text
app/
  __init__.py         # تهيئة التطبيق والامتدادات
  config.py           # تحميل الإعدادات من البيئة
  company/            # بوابة الشركات (مسارات، واجهات، واجهات برمجية)
  models/             # نماذج SQLAlchemy
  routes/             # التجميع العام للبلو برنت
  services/           # منطق الأعمال ومساعدات الأمان
  static/             # ملفات CSS/JS وموارد الواجهات
  templates/          # القوالب المشتركة وقوالب البوابات
migrations/           # ملفات Alembic
run.py                # نقطة الدخول لتشغيل التطبيق
```

## إعداد قاعدة البيانات
1. تأكد من إنشاء قاعدة بيانات باسم `elite` أو عدّل URI حسب بيئتك.
2. أنشئ ملف الترحيلات عند الحاجة:
   ```bash
   flask db migrate -m "Initial setup"
   ```
3. طبق التغييرات:
   ```bash
   flask db upgrade
   ```

تشمل النماذج الأساسية: المستخدمون (roles، حالة التفعيل، ارتباط الشركة)، الشركات (الوصف، بيانات الاتصال)، والعروض (نسب الخصم وتواريخ الصلاحية).

## البريد الإلكتروني والتحقق
- عند التسجيل يتم إرسال رسالة تحقق تحتوي على رابط موقّع.
- يمكن للمستخدمين طلب إعادة تعيين كلمة المرور واستلام رابط صالح لمدة ساعة.
- استخدم بيانات SMTP آمنة وتأكد من تمكين "كلمة مرور التطبيقات" عند استخدام Gmail.

## الأدوار والصلاحيات
يعتمد النظام على أدوار `member`, `company`, `admin`, و`superadmin` لضبط الوصول.
استخدم الديكوريتر `require_role` لحماية المسارات الحساسة:
```python
from app.services.roles import require_role

@blueprint.route("/admin/secure")
@require_role("admin")
def secure_action():
    ...
```

## مراقبة الصحة والاختبارات
- نقطة الصحة الافتراضية: `GET /health` وتعيد `{ "status": "ok" }` عند نجاح التشغيل.
- ينصح بتشغيل الاختبارات أو التحقق اليدوي من مسارات التسجيل وتسجيل الدخول بعد أي تعديل جوهري.

## مشكلات معروفة ونصائح
- تأكد من تحميل CSRF فقط على المسارات التي تعتمد على النماذج لتجنب أخطاء 400 غير ضرورية.
- عند العمل على لوحة الإدارة، استخدم حسابًا بصلاحيات `admin` أو `superadmin` لمشاهدة الأزرار الكاملة للتفعيل والتعليق.
- في حال تغير بنية النماذج، أعد توليد الترحيلات باستخدام Alembic وراجع النتائج قبل الترقية.

## Cleanup: Removed Old Admin Company Management
- Deleted all templates related to admin company management (companies.html, company_details.html, etc.).
- Removed all /admin/companies routes and related functions from routes_companies.py and routes.py.
- Cleaned imports of Company model and mailer functions from admin modules.
- Prepared project for clean reimplementation of company management with Codex.

## Phase 1: Basic Admin Company Management Routes
- Added clean routes_companies.py for /admin/companies.
- Supports status filtering (pending, approved, suspended, correction).
- Returns companies.html with status tabs and counts.

## Phase 2: Admin Companies Template (Basic)
- Added new clean companies.html template.
- Includes tabs for status filtering and basic company table.
- No action buttons yet (to be added in next phase).
- Compatible with /admin/companies route from Phase 1.

## Phase 3: Admin Company Details Page
- Added /admin/companies/<id> route for viewing company details.
- Created new company_details.html template.
- Displays all company info, links, and admin notes.
- Prepares structure for management actions (Phase 4).

## Phase 4: Admin Company Management Actions
- Added full CRUD actions for companies (view, edit, delete).
- Added admin status controls: Activate, Suspend, Reactivate.
- Integrated email notifications for status changes.
- Simplified routes and templates for clean maintainability.

## Verification: Unified Admin Base Template
- Confirmed all admin templates extend "dashboard/base.html".
- Ensured sidebar and navbar visibility for admin and superadmin roles.

## موارد إضافية
- وثائق Flask: <https://flask.palletsprojects.com/>
- وثائق Alembic: <https://alembic.sqlalchemy.org/>
- وثائق Redis: <https://redis.io/docs/>

> آخر تحديث: أكتوبر 2025

## Cleanup: Removed Legacy Admin Settings Templates
- Deleted folder app/templates/admin/settings/ (home.html, index.html, roles.html).
- Unified all admin settings pages under app/admin/templates/dashboard/.
- Ensured all pages extend dashboard/admin_base.html.
- Reduced template duplication and namespace confusion.
- Updated on: 2025-10-26 05:43 UTC.
