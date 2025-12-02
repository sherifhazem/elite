آخر تحديث: v13.1 — 2025-10-25
الغرض: خريطة كاملة للمشروع لتوجيه Codex قبل أي تعديل أو تنفيذ.
حالة المشروع: مستقرة بعد تصحيح تضارب الـ Blueprints ووراثة القوالب.

🏗️ المستويات الرئيسية

المجلد	الغرض
app/	الحزمة الأساسية (Flask App Factory + التكوين العام)
app/admin/	لوحة التحكم الإدارية (Admin Panel)
app/auth/	المصادقة وتسجيل الدخول/الخروج
app/company/	بوابة الشركات (عروض + ملفات الشركات)
app/routes/	مسارات عامة (الموقع العام / الواجهة الرئيسية)
app/services/	الخدمات الداخلية (البريد، الإشعارات، التسجيل)
app/models/	ORM models (User, Company, Offer, Notification, etc.)
app/templates/	القوالب العامة والمشتركة
app/static/	الموارد الثابتة (CSS / JS / Images)

🧩 قائمة الـ Blueprints المسجلة
Blueprint	المسار (url_prefix)	الموقع في الكود	الاستخدام
main	/	app/routes/__init__.py	الصفحة الرئيسية والمحتوى العام
auth	/auth	app/auth/routes.py	التسجيل / تسجيل الدخول / الخروج
admin	/admin	app/admin/routes.py	لوحة التحكم الإدارية
reports	/admin/reports	app/admin/routes_reports.py	تقارير النظام
company_portal	/company	app/company/routes/__init__.py	واجهة الشركات بعد التسجيل (مقسمة إلى وحدات routes_*)
notif_bp	/notifications	app/routes/notifications.py	إشعارات عامة (للمستخدمين)
redemption_bp	/api/redemptions	app/routes/redemptions.py	نظام تفعيل العروض
portal_bp	/portal	app/routes/user_portal_routes.py	واجهة المستخدم النهائي
company_routes	/api/companies	app/routes/company_routes.py	واجهات API خاصة بالشركات
offer_routes	/api/offers	app/routes/offer_routes.py	واجهات API للعروض

✅ تمت إزالة أو دمج Blueprints التالية لتجنب التكرار:

activity_log_bp ← تم دمجها داخل Blueprint admin

company_portal_bp ← تم توحيدها إلى company_portal

🧭 Endpoints الأساسية داخل لوحة الأدمن
Endpoint	HTTP	الغرض	القالب المرتبط
admin.dashboard_home	GET	الصفحة الرئيسية للوحة الأدمن	dashboard/home.html
admin.dashboard_users	GET	إدارة المستخدمين	dashboard/users.html
admin.list_companies	GET	قائمة الشركات	dashboard/companies.html
admin.company_detail	GET	عرض تفاصيل شركة	dashboard/company_detail.html
admin.edit_user	GET/POST	تعديل بيانات مستخدم	dashboard/edit_user.html
admin.add_user	GET/POST	إضافة مستخدم جديد	dashboard/add_user.html
admin.settings_home	GET	إعدادات النظام (القوائم والمدن)	dashboard/settings.html
admin.site_settings_roles	GET	إدارة الأدوار والصلاحيات	dashboard/users_roles.html
admin.admin_logout	GET	تسجيل الخروج من الأدمن	—
admin.communication_history	GET	مركز الرسائل	communications/index.html
admin.compose_message	GET/POST	إنشاء رسالة إدارية	communications/compose.html
admin.activity_log	GET	سجل النشاطات الإدارية	dashboard/activity_log.html

✅ تم توحيد كل الروابط داخل القوالب لتستخدم:

url_for('admin.<endpoint_name>')

Endpoint        HTTP    المخرجات        المصدر
company_portal.company_dashboard_redirect    GET     Redirect → dashboard    app/company/routes/routes_dashboard.py
company_portal.company_dashboard_overview        GET     company/dashboard_overview.html  app/company/routes/routes_dashboard.py
company_portal.complete_registration    GET/POST        company/complete_registration.html      app/company/routes/routes_registration.py
company_portal.company_offers_list      GET     company/offers_list.html     app/company/routes/routes_offers.py
company_portal.offer_new        GET     company/offer_form.html app/company/routes/routes_offers.py
company_portal.offer_create     POST    JSON / redirect app/company/routes/routes_offers.py
company_portal.offer_edit       GET     company/offer_form.html app/company/routes/routes_offers.py
company_portal.offer_update     POST/PUT        JSON / redirect app/company/routes/routes_offers.py
company_portal.offer_delete     POST/DELETE     JSON / redirect app/company/routes/routes_offers.py
company_portal.company_redemptions_history      GET     company/redemptions_history.html        app/company/routes/routes_redemptions.py
company_portal.company_redemptions_data GET     JSON    app/company/routes/routes_redemptions.py
company_portal.verify_redemption        POST    JSON    app/company/routes/routes_redemptions.py
company_portal.confirm_redemption       POST    JSON    app/company/routes/routes_redemptions.py
company_portal.company_settings GET/POST        company/company_settings.html   app/company/routes/routes_settings.py

✅ جميعها محمية بـ:

@require_role("company")


المسارات تنظم الآن ضمن app/company/routes/ حسب المجال الوظيفي.


👥 Endpoints في واجهة المستخدم (Member Portal)
Endpoint        HTTP    القالب
portal.member_portal_home     GET     portal/home.html
portal.member_portal_profile  GET/POST        portal/profile.html
portal.member_portal_offers        GET     portal/offers.html
🔐 نظام الصلاحيات والأمان
Decorator	الموقع	الغرض
@admin_required	app/services/roles.py	تقييد الوصول لمسارات الأدمن فقط
@company_required	app/services/roles.py	يسمح فقط بحسابات الشركات
@login_required	flask_login	حماية عامة للجلسات

✅ تم تطبيقها في جميع المسارات الحرجة
(خاصة /admin/api/* و /company/*).

🧱 النماذج Models
Model	الموقع	العلاقات
User	app/models/user.py	علاقة company_id ←→ Company
Company	app/models/company.py	offers, users
Offer	app/models/offer.py	company_id, redemptions
Redemption	app/models/redemption.py	user_id, offer_id
Notification	app/models/notification.py	user_id
Permission	app/models/permission.py	users (many-to-many)
🛠️ الخدمات الداخلية (Services)
ملف	الوظيفة
app/services/mailer.py  إرسال البريد (تأكيد التسجيل، استعادة كلمة المرور)
app/modules/members/services/member_notifications_service.py   إدارة إشعارات المستخدمين — يحتوي الآن على:
get_unread_count(user_id) و get_notifications_for_user(user_id)
app/modules/companies/services/company_registration_service.py    تسجيل الشركات ومراجعتها
app/services/access_control.py   إدارة الديكوريتر admin_required و company_required
🎨 القوالب (Templates)
🔹 القالب الأساسي

app/admin/templates/dashboard/admin_base.html
→ القالب الرئيسي لجميع صفحات لوحة الأدمن.

✅ تم حذف النسخة المكررة dashboard/base.html.

🔹 وراثة صحيحة
النوع	القوالب التي ترث منها
صفحات الأدمن	{% extends "dashboard/admin_base.html" %}
صفحات الشركات	{% extends "company/base.html" %}
صفحات الأعضاء	{% extends "portal/base.html" %}
صفحات المصادقة	{% extends "auth/base.html" %}
🧾 ملفات النظام الإضافية
الملف	الغرض
.env	متغيرات البيئة (DATABASE_URL, SECRET_KEY, REDIS_URL)
README.md	توثيق التحديثات والمهام المنفذة
PROJECT_MAP.md	هذا الملف — مرجع بنيوي للمشروع
🧩 المشاكل السابقة التي تم تصحيحها
رقم	المشكلة	الحالة
1	تضارب Blueprints (activity_log_bp)	✅ تم دمجها في admin
2	تكرار dashboard/base.html	✅ حُذفت
3	روابط خاطئة (company_portal.list_offers)	✅ صُححت
4	BuildError في activity_log	✅ endpoint مضاف داخل admin
5	ImportError في notifications	✅ تمت إضافة get_notifications_for_user
6	AnonymousUserMixin.id	✅ أُضيف @login_required + فحص المصادقة
7	اختلاف تصميم Dashboard	✅ وراثة موحدة من admin_base.html
