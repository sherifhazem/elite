# خريطة مشروع ELITE (محدَّثة)

تم توليد هذه الخريطة بعد مراجعة بنية التطبيق وفق التعليمات. تُستخدم كمرجع رئيسي لأي تعديل مستقبلي.

## 📦 الـ Blueprints المسجَّلة
- **main** (`/`) – `app/routes/__init__.py`
- **auth** (`/auth`) – `app/auth/routes.py`
- **admin** (`/admin`) – `app/admin/routes.py` + الوحدات الفرعية ضمن `app/admin/`
- **reports** (`/admin`) – `app/admin/routes_reports.py`
- **activity_log_bp** (`/admin`) – `app/admin/routes_activity_log.py`
- **company_portal** (`/company`) – `app/company/routes.py`
- **portal** (`/portal`) – `app/routes/user_portal_routes.py`
- **offers** (`/api/offers`) – `app/routes/offer_routes.py`
- **companies** (`/api/companies`) – `app/routes/company_routes.py`
- **users** (`/api/users`) – `app/routes/user_routes.py`
- **redemption** (`/api/redemptions`) – `app/routes/redemption_routes.py`
- **notifications** (`/api/notifications`) – `app/routes/notification_routes.py`
- **notifications API للأدمن** (`/admin/api/notifications`) – `app/admin/routes_notifications.py`

## 🔀 جميع الـ Endpoints حسب الـ Blueprint
### main (app/routes/__init__.py)
- `main.index` → `app/routes/__init__.py`
- `main.about` → `app/routes/__init__.py`
- `main.health_check` → `app/routes/__init__.py`

### auth (app/auth/routes.py)
- `auth.api_register` → `app/auth/routes.py`
- `auth.register_select` → `app/auth/routes.py`
- `auth.register_member` → `app/auth/routes.py`
- `auth.register_member_legacy` → `app/auth/routes.py`
- `auth.register_company` → `app/auth/routes.py`
- `auth.api_login` → `app/auth/routes.py`
- `auth.profile` → `app/auth/routes.py`
- `auth.choose_membership` → `app/auth/routes.py`
- `auth.login` → `app/auth/routes.py`
- `auth.login_page` → `app/auth/routes.py`
- `auth.register_choice` → `app/auth/routes.py`
- `auth.verify_email` → `app/auth/routes.py`
- `auth.request_password_reset` → `app/auth/routes.py`
- `auth.reset_password` → `app/auth/routes.py`
- `auth.logout` → `app/auth/routes.py`

### admin (app/admin/routes.py)
- `admin.admin_logout` → `app/admin/routes.py`
- `admin.dashboard_home` → `app/admin/routes.py`
- `admin.dashboard_alias` → `app/admin/routes.py`
- `admin.dashboard_users` → `app/admin/routes.py`
- `admin.view_user` → `app/admin/routes.py`
- `admin.add_user` → `app/admin/routes.py`
- `admin.edit_user` → `app/admin/routes.py`
- `admin.delete_user` → `app/admin/routes.py`
- `admin.manage_user_roles` → `app/admin/routes.py`
- `admin.dashboard_offers` → `app/admin/routes.py`
- `admin.add_offer` → `app/admin/routes.py`
- `admin.manage_offer` → `app/admin/routes.py`
- `admin.edit_offer_discount` → `app/admin/routes.py`
- `admin.delete_offer` → `app/admin/routes.py`
- `admin.trigger_offer_notification` → `app/admin/routes.py`
- `admin.settings_home` → `app/admin/routes.py`
- `admin.update_site_settings` → `app/admin/routes.py`
- `admin.site_settings_roles` → `app/admin/routes.py`
- `admin.save_site_settings_roles` → `app/admin/routes.py`
- `admin.fetch_cities` → `app/admin/routes.py`
- `admin.fetch_industries` → `app/admin/routes.py`
- `admin.add_city` → `app/admin/routes.py`
- `admin.add_industry` → `app/admin/routes.py`
- `admin.update_city` → `app/admin/routes.py`
- `admin.update_industry` → `app/admin/routes.py`
- `admin.delete_city` → `app/admin/routes.py`
- `admin.delete_industry` → `app/admin/routes.py`

### admin (الوحدات الفرعية)
- `admin.list_companies` → `app/admin/routes_companies.py`
- `admin.view_company` → `app/admin/routes_companies.py`
- `admin.edit_company` → `app/admin/routes_companies.py`
- `admin.delete_company` → `app/admin/routes_companies.py`
- `admin.approve_company` → `app/admin/routes_companies.py`
- `admin.suspend_company` → `app/admin/routes_companies.py`
- `admin.reactivate_company` → `app/admin/routes_companies.py`
- `admin.communication_history` → `app/admin/routes_communications.py`
- `admin.compose_communication` → `app/admin/routes_communications.py`
- `admin.communication_detail` → `app/admin/routes_communications.py`
- `admin.communication_lookup` → `app/admin/routes_communications.py`
- `admin.api_notifications_list` → `app/admin/routes_notifications.py`
- `admin.api_notifications_mark_read` → `app/admin/routes_notifications.py`

### reports (app/admin/routes_reports.py)
- `reports.reports_home` → `app/admin/routes_reports.py`
- `reports.summary_api` → `app/admin/routes_reports.py`
- `reports.export_pdf` → `app/admin/routes_reports.py`

### activity_log_bp (app/admin/routes_activity_log.py)
- `activity_log_bp.activity_log` → `app/admin/routes_activity_log.py`

### company_portal (app/company/routes.py)
- `company_portal.complete_registration` → `app/company/routes.py`
- `company_portal.index` → `app/company/routes.py`
- `company_portal.dashboard` → `app/company/routes.py`
- `company_portal.list_offers` → `app/company/routes.py`
- `company_portal.offer_new` → `app/company/routes.py`
- `company_portal.offer_create` → `app/company/routes.py`
- `company_portal.offer_edit` → `app/company/routes.py`
- `company_portal.offer_update` → `app/company/routes.py`
- `company_portal.offer_delete` → `app/company/routes.py`
- `company_portal.redemptions` → `app/company/routes.py`
- `company_portal.redemptions_data` → `app/company/routes.py`
- `company_portal.verify_redemption` → `app/company/routes.py`
- `company_portal.confirm_redemption` → `app/company/routes.py`
- `company_portal.settings` → `app/company/routes.py`

### portal (app/routes/user_portal_routes.py)
- `portal.home` → `app/routes/user_portal_routes.py`
- `portal.home_alias` → `app/routes/user_portal_routes.py`
- `portal.offers` → `app/routes/user_portal_routes.py`
- `portal.profile` → `app/routes/user_portal_routes.py`
- `portal.activations` → `app/routes/user_portal_routes.py`
- `portal.offer_feedback` → `app/routes/user_portal_routes.py`
- `portal.company_brief` → `app/routes/user_portal_routes.py`
- `portal.notifications` → `app/routes/user_portal_routes.py`
- `portal.upgrade_membership` → `app/routes/user_portal_routes.py`

### offers API (app/routes/offer_routes.py)
- `offers.list_offers` → `app/routes/offer_routes.py`
- `offers.create_offer` → `app/routes/offer_routes.py`
- `offers.update_offer` → `app/routes/offer_routes.py`
- `offers.delete_offer` → `app/routes/offer_routes.py`

### companies API (app/routes/company_routes.py)
- `companies.register_company` → `app/routes/company_routes.py`
- `companies.list_companies` → `app/routes/company_routes.py`
- `companies.create_company` → `app/routes/company_routes.py`
- `companies.update_company` → `app/routes/company_routes.py`
- `companies.delete_company` → `app/routes/company_routes.py`

### users API (app/routes/user_routes.py)
- `users.list_users` → `app/routes/user_routes.py`
- `users.create_user` → `app/routes/user_routes.py`
- `users.update_user` → `app/routes/user_routes.py`
- `users.delete_user` → `app/routes/user_routes.py`
- `users.update_membership` → `app/routes/user_routes.py`

### redemption API (app/routes/redemption_routes.py)
- `redemption.create_redemption_endpoint` → `app/routes/redemption_routes.py`
- `redemption.redemption_status` → `app/routes/redemption_routes.py`
- `redemption.confirm_redemption` → `app/routes/redemption_routes.py`
- `redemption.get_qrcode_image` → `app/routes/redemption_routes.py`

### notifications API (app/routes/notification_routes.py)
- `notifications.list_notifications` → `app/routes/notification_routes.py`
- `notifications.mark_notification_read` → `app/routes/notification_routes.py`
- `notifications.mark_all_notifications_read` → `app/routes/notification_routes.py`
- `notifications.delete_notification` → `app/routes/notification_routes.py`

## 🧩 وراثة القوالب
- `dashboard/admin_base.html` ← جميع قوالب الأدمن داخل `app/admin/templates/dashboard/`
- `base.html` ← القوالب العامة في `app/templates/` (مثل `index.html`, `portal/*`, `auth/*`)
- `company/base.html` ← قوالب بوابة الشركات في `app/templates/company/`
- `portal/base.html` ← واجهة الأعضاء في `app/templates/portal/`
- `auth/base.html` ← صفحات المصادقة في `app/templates/auth/`

## 🧠 معالجات السياق والتكوين
- `inject_user_context` داخل `app/__init__.py` يزوّد القوالب بـ `current_user`, `role`, `user_permissions`, ووسم الحالة.
- إعدادات التطبيق محمّلة من `app/config.py` عبر `app.config.from_object(Config)`.

## 🔗 الخدمات (Services) والنماذج (Models)
- `app/services/company_registration.py` ↔ يستخدم نماذج `User` و`Company` لإنشاء الحسابات ومزامنة المالك.
- `app/services/notifications.py` ↔ يعمل مع نموذج `Notification` لإدارة الإشعارات وقنوات البث.
- `app/services/roles.py` ↔ يعتمد على نموذج `User` والتحقق من الخصائص لتطبيق الزوار والمعرّفات.
- `app/services/settings_service.py` ↔ يخزّن إعدادات القوائم داخل Redis (`redis_client`).
- `app/services/offers.py` ↔ يجلب بيانات `Offer` ويرتبط بـ `Company` و`Redemption` لواجهات الإدارة والشركة.
- `app/services/redemption.py` ↔ يعالج حالات `Redemption` ويرتبط بموديلات `Offer` و`User`.
- `app/services/mailer.py` و`email_service.py` ↔ ترسل رسائل تخص مستخدمي `User` والشركات `Company`.

## 🔒 Decorators للأمان
- `@admin_required` (داخل `app/services/roles.py`) – يحصر الوصول لمستخدمي الأدمن والسوبر أدمن.
- `@require_role("company")` (داخل `app/services/roles.py`) – يؤمّن مسارات بوابة الشركة.
- `@login_required` (من Flask-Login) – مستخدم في API الأدمن للإشعارات.
- مسارات الشركة والأدمن تستفيد أيضًا من فحص `g.current_user` داخل `app/__init__.py` قبل كل طلب.

## 🧾 المشاكل المصحَّحة حديثًا
- ✅ **إزالة مجلد القوالب القديم**: تم حذف `app/templates/admin/settings/` (الملفات legacy) لصالح القوالب الموحدة داخل `app/admin/templates/dashboard/`.
- ✅ توجيه مسارات الإعدادات الآن إلى `dashboard/settings.html` و `dashboard/users_roles.html` فقط لتقليل الازدواجية.

