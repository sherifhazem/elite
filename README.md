# ELITE Backend

إصدار مبسّط يوضح كيفية إعداد وتشغيل خادم ELITE المسؤول عن إدارة العروض، الشركات، وأدوار المستخدمين. يوفر المشروع هيكل Flask منظمًا، تكاملًا مع PostgreSQL وRedis، ونقاط نهاية جاهزة لمتابعة الصحة وإدارة الحسابات.

## نظرة عامة
- **Flask** يستخدم كأساس لتجميع البلوبرنتات الخاصة بالأعضاء، الشركات، ولوحة التحكم الإدارية.
- **PostgreSQL** هو قاعدة البيانات الرئيسية ويتم التعامل معها عبر SQLAlchemy وFlask-Migrate.
- **Redis** يدعم المهام الخلفية والإشعارات المؤقتة.
- **البريد الإلكتروني** مُهيأ عبر SMTP لإرسال رسائل التحقق واستعادة كلمة المرور.

## متطلبات التشغيل
- Python 3.11
- PostgreSQL 13 أو أحدث
- Redis متاح محليًا أو عبر خدمة خارجية

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

## موارد إضافية
- وثائق Flask: <https://flask.palletsprojects.com/>
- وثائق Alembic: <https://alembic.sqlalchemy.org/>
- وثائق Redis: <https://redis.io/docs/>

> آخر تحديث: أكتوبر 2025
