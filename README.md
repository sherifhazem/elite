# EmployeeTracker Monorepo

The project now organizes the client application inside the `EmployeeTracker/client/`
folder in preparation for adding a complementary `server/` implementation.

```
EmployeeTracker/
└── client/
    ├── attendance_gui/
    ├── background_service/
    ├── commands_listener/
    ├── data_sync/
    ├── local_storage/
    ├── utils/
    ├── README.md
    └── requirements.txt
```

<<<<<<< HEAD
Each package contains placeholder modules that document the future
implementation. Imports within the client codebase have been updated to target
the new package paths so the modules continue to resolve correctly after the
move.
=======
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
>>>>>>> parent of 2a345af (Add attendance login window scaffold (#160))
