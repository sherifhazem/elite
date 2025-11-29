# 🧭 خريطة مشروع ELITE (نسخة مصححة v13.2)

تم إنشاء هذا الملف بعد مراجعة شاملة للبنية الفعلية للمشروع.  
يُعد المرجع البنيوي الرئيسي لأي تعديل مستقبلي من قبل Codex أو أي مطوّر آخر.

---

## 📦 الـ Blueprints المسجَّلة

| الاسم | المسار (url_prefix) | موقع التعريف | الغرض |
|--------|--------------------|----------------|--------|
| **main** | `/` | `app/modules/members/routes/__init__.py` | الواجهة العامة للموقع |
| **auth** | `/auth` | `app/modules/members/auth/routes.py` | التسجيل وتسجيل الدخول والخروج |
| **admin** | `/admin` | `app/modules/admin/routes/dashboard_routes.py` | لوحة تحكم الأدمن، وتشمل كل الوحدات الفرعية |
| **reports** | `/admin/reports` | `app/modules/admin/routes/reports_routes.py` | عرض تقارير النظام والإحصاءات |
| **company_portal** | `/company` | `app/modules/companies/routes/__init__.py` | واجهة الشركات (العروض، الإحصاءات، الإعدادات) |
| **portal** | `/portal` | `app/modules/members/routes/user_portal_routes.py` | بوابة المستخدمين (العروض، الملف الشخصي) |
| **offers** | `/api/offers` | `app/modules/members/routes/offer_routes.py` | واجهات API الخاصة بالعروض |
| **companies** | `/api/companies` | `app/modules/companies/routes/api_routes.py` | واجهات API للشركات |
| **users** | `/api/users` | `app/modules/members/routes/user_routes.py` | واجهات API للمستخدمين |
| **redemption** | `/api/redemptions` | `app/modules/members/routes/redemption_routes.py` | نظام تفعيل العروض QR |
| **notifications** | `/api/notifications` | `app/modules/members/routes/notification_routes.py` | إدارة الإشعارات العامة |

✅ تمت إزالة Blueprint القديمة `activity_log_bp` ودمجها ضمن `admin`.

---

## 🔀 الـ Endpoints حسب الـ Blueprint (محدَّثة)

### 🔹 main (`app/modules/members/routes/__init__.py`)
- main.index → app/modules/members/routes/__init__.py
- main.about → app/modules/members/routes/__init__.py
- main.health_check → app/modules/members/routes/__init__.py

### 🔹 auth (`app/modules/members/auth/routes.py`)
- auth.api_register → app/modules/members/auth/routes.py
- auth.register_select → app/modules/members/auth/routes.py
- auth.register_member → app/modules/members/auth/routes.py
- auth.register_member_legacy → app/modules/members/auth/routes.py
- auth.register_company → app/modules/members/auth/routes.py
- auth.api_login → app/modules/members/auth/routes.py
- auth.profile → app/modules/members/auth/routes.py
- auth.choose_membership → app/modules/members/auth/routes.py
- auth.login → app/modules/members/auth/routes.py
- auth.login_page → app/modules/members/auth/routes.py
- auth.register_choice → app/modules/members/auth/routes.py
- auth.verify_email → app/modules/members/auth/routes.py
- auth.request_password_reset → app/modules/members/auth/routes.py
- auth.reset_password → app/modules/members/auth/routes.py
- auth.logout → app/modules/members/auth/routes.py

### 🔹 admin (`app/modules/admin/routes/dashboard_routes.py`)
- admin.admin_logout → app/modules/admin/routes/dashboard_routes.py
- admin.dashboard_home → GET /admin/
- admin.dashboard_alias → GET /admin/dashboard (redirect)
- admin.dashboard_users → app/modules/admin/routes/dashboard_routes.py
- admin.view_user → app/modules/admin/routes/dashboard_routes.py
- admin.add_user → app/modules/admin/routes/dashboard_routes.py
- admin.edit_user → app/modules/admin/routes/dashboard_routes.py
- admin.delete_user → app/modules/admin/routes/dashboard_routes.py
- admin.manage_user_roles → app/modules/admin/routes/dashboard_routes.py
- admin.dashboard_offers → app/modules/admin/routes/dashboard_routes.py
- admin.add_offer → app/modules/admin/routes/dashboard_routes.py
- admin.manage_offer → app/modules/admin/routes/dashboard_routes.py
- admin.edit_offer_discount → app/modules/admin/routes/dashboard_routes.py
- admin.delete_offer → app/modules/admin/routes/dashboard_routes.py
- admin.trigger_offer_notification → app/modules/admin/routes/dashboard_routes.py
- admin.settings_home → app/modules/admin/routes/dashboard_routes.py
- admin.update_site_settings → app/modules/admin/routes/dashboard_routes.py
- admin.site_settings_roles → app/modules/admin/routes/dashboard_routes.py
- admin.save_site_settings_roles → app/modules/admin/routes/dashboard_routes.py
- admin.fetch_cities → app/modules/admin/routes/dashboard_routes.py
- admin.fetch_industries → app/modules/admin/routes/dashboard_routes.py
- admin.add_city → app/modules/admin/routes/dashboard_routes.py
- admin.add_industry → app/modules/admin/routes/dashboard_routes.py
- admin.update_city → app/modules/admin/routes/dashboard_routes.py
- admin.update_industry → app/modules/admin/routes/dashboard_routes.py
- admin.delete_city → app/modules/admin/routes/dashboard_routes.py
- admin.delete_industry → app/modules/admin/routes/dashboard_routes.py
- admin.activity_log → app/modules/admin/routes/dashboard_routes.py
- admin.communication_history → app/admin/routes_communications.py
- admin.compose_communication → app/admin/routes_communications.py

### 🔹 reports (`app/modules/admin/routes/reports_routes.py`)
- reports.reports_home → app/modules/admin/routes/reports_routes.py
- reports.summary_api → app/modules/admin/routes/reports_routes.py
- reports.export_pdf → app/modules/admin/routes/reports_routes.py

### 🔹 company_portal (`app/modules/companies/routes/__init__.py`)
- company_portal.complete_registration → app/modules/companies/routes/__init__.py
- company_portal.index → app/modules/companies/routes/__init__.py
- company_portal.dashboard → app/modules/companies/routes/__init__.py
- company_portal.list_offers → app/modules/companies/routes/__init__.py
- company_portal.offer_new → app/modules/companies/routes/__init__.py
- company_portal.offer_create → app/modules/companies/routes/__init__.py
- company_portal.offer_edit → app/modules/companies/routes/__init__.py
- company_portal.offer_update → app/modules/companies/routes/__init__.py
- company_portal.offer_delete → app/modules/companies/routes/__init__.py
- company_portal.redemptions → app/modules/companies/routes/__init__.py
- company_portal.redemptions_data → app/modules/companies/routes/__init__.py
- company_portal.verify_redemption → app/modules/companies/routes/__init__.py
- company_portal.confirm_redemption → app/modules/companies/routes/__init__.py
- company_portal.settings → app/modules/companies/routes/__init__.py

### 🔹 portal (`app/modules/members/routes/user_portal_routes.py`)
- portal.home → app/modules/members/routes/user_portal_routes.py
- portal.home_alias → app/modules/members/routes/user_portal_routes.py
- portal.offers → app/modules/members/routes/user_portal_routes.py
- portal.profile → app/modules/members/routes/user_portal_routes.py
- portal.activations → app/modules/members/routes/user_portal_routes.py
- portal.offer_feedback → app/modules/members/routes/user_portal_routes.py
- portal.company_brief → app/modules/members/routes/user_portal_routes.py
- portal.notifications → app/modules/members/routes/user_portal_routes.py
- portal.upgrade_membership → app/modules/members/routes/user_portal_routes.py

### 🔹 offers (`app/modules/members/routes/offer_routes.py`)
- offers.list_offers → app/modules/members/routes/offer_routes.py
- offers.create_offer → app/modules/members/routes/offer_routes.py
- offers.update_offer → app/modules/members/routes/offer_routes.py
- offers.delete_offer → app/modules/members/routes/offer_routes.py

### 🔹 companies (`app/modules/companies/routes/api_routes.py`)
- companies.register_company → app/modules/companies/routes/api_routes.py
- companies.list_companies → app/modules/companies/routes/api_routes.py
- companies.create_company → app/modules/companies/routes/api_routes.py
- companies.update_company → app/modules/companies/routes/api_routes.py
- companies.delete_company → app/modules/companies/routes/api_routes.py

### 🔹 users (`app/modules/members/routes/user_routes.py`)
- users.list_users → app/modules/members/routes/user_routes.py
- users.create_user → app/modules/members/routes/user_routes.py
- users.update_user → app/modules/members/routes/user_routes.py
- users.delete_user → app/modules/members/routes/user_routes.py
- users.update_membership → app/modules/members/routes/user_routes.py

### 🔹 redemption (`app/modules/members/routes/redemption_routes.py`)
- redemption.create_redemption_endpoint → app/modules/members/routes/redemption_routes.py
- redemption.redemption_status → app/modules/members/routes/redemption_routes.py
- redemption.confirm_redemption → app/modules/members/routes/redemption_routes.py
- redemption.get_qrcode_image → app/modules/members/routes/redemption_routes.py

### 🔹 notifications (`app/modules/members/routes/notification_routes.py`)
- notifications.list_notifications → app/modules/members/routes/notification_routes.py
- notifications.mark_notification_read → app/modules/members/routes/notification_routes.py
- notifications.mark_all_notifications_read → app/modules/members/routes/notification_routes.py
- notifications.delete_notification → app/modules/members/routes/notification_routes.py

---

## 🧩 وراثة القوالب (Template Inheritance)

| المسار | الاستخدام | الموروث من |
|--------|-------------|-------------|
| `app/admin/templates/dashboard/*` | جميع صفحات لوحة الأدمن | `dashboard/admin_base.html` |
| `app/templates/*` | الصفحات العامة | `base.html` |
| `app/templates/company/*` | واجهة الشركات | `company/base.html` |
| `app/templates/portal/*` | واجهة الأعضاء | `portal/base.html` |
| `app/templates/auth/*` | صفحات الدخول والتسجيل | `auth/base.html` |
| `app/templates/dashboard/` | قوالب عامة مثل التقارير أو الإحصاءات | `base.html` أو `admin_base.html` حسب السياق |

✅ تمت إزالة القوالب القديمة `app/templates/admin/settings/`.

---

## 🛠️ أدوات الصيانة والفحص

- `tools/check_endpoints.py`: أداة لمطابقة المسارات الموثقة في `app/PROJECT_MAP.md` مع المسارات المسجلة فعليًا داخل تطبيق Flask، وتنبه إلى وجود مسارات مفقودة، زائدة أو مكررة لضمان اتساق الخريطة مع التطبيق.

---

## 🧠 معالجات السياق والتكوين (Context Processors & Config)

- `inject_user_context` في `app/__init__.py` يوفر المتغيرات التالية في القوالب:  
  `current_user`, `user_role`, `user_permissions`, `user_status_label`, `is_admin`, `is_superadmin`.
- إعدادات التطبيق محمّلة من `app/config.py` عبر `app.config.from_object(Config)`.

---

## 🔗 الخدمات (Services) والنماذج (Models)

| الملف | الوظيفة الأساسية |
|--------|------------------|
| `app/services/company_registration.py` | تسجيل الشركات ومراجعة طلباتها |
| `app/services/notifications.py` | إدارة إشعارات المستخدمين (`get_unread_count`, `get_notifications_for_user`) |
| `app/services/roles.py` | إدارة الديكوريتر `admin_required`, `company_required` |
| `app/services/settings_service.py` | تخزين إعدادات المدن/الأنشطة في Redis |
| `app/services/offers.py` | إدارة عروض الشركات للأعضاء |
| `app/services/redemption.py` | معالجة عمليات استرداد العروض |
| `app/services/mailer.py` | إرسال البريد الإلكتروني للمستخدمين والشركات |

### النماذج (Models)
| النموذج | العلاقات |
|---------|-----------|
| `User` | `company_id` → `Company` |
| `Company` | `offers`, `users` |
| `Offer` | `company_id`, `redemptions` |
| `Redemption` | `user_id`, `offer_id` |
| `Notification` | `user_id` |
| `Permission` | `users` (many-to-many) |

---

## 🔒 Decorators للأمان

| الديكوريتر | الموقع | الغرض |
|-------------|----------|--------|
| `@admin_required` | `app/services/roles.py` | تقييد الوصول لمستخدمي الأدمن والسوبر أدمن |
| `@company_required` | `app/services/roles.py` | تأمين مسارات بوابة الشركات |
| `@login_required` | `flask_login` | حماية عامة للمستخدمين المسجلين |
| `g.current_user` | `app/__init__.py` | تحقق إضافي من الجلسة في الطلبات المحمية |

---

## 🧾 المشاكل المصححة حديثًا

| رقم | المشكلة السابقة | الحالة |
|------|------------------|----------|
| 1 | تكرار `dashboard/base.html` | ✅ محذوف |
| 2 | وراثة خاطئة لقوالب Communications | ✅ مصححة إلى `dashboard/admin_base.html` |
| 3 | القوالب القديمة في `app/templates/admin/settings/` | ✅ محذوفة |
| 4 | تضارب `activity_log_bp` | ✅ مدمجة داخل `admin.activity_log` |
| 5 | BuildError في `company_portal.list_offers` | ✅ endpoint موحد |
| 6 | ImportError في `notifications` | ✅ إضافة `get_notifications_for_user` |
| 7 | AnonymousUserMixin.id | ✅ إضافة `@login_required` |
| 8 | اختلاف تصميم Dashboard | ✅ توحيد الوراثة |
| 9 | توحيد اللغة والتسميات داخل القوالب | ✅ الإنجليزية موحدة للوحة الأدمن |

---

## 🧭 تعليمات لـ Codex

1. **اقرأ هذا الملف بالكامل قبل تنفيذ أي تعديل.**
2. لا تُنشئ Blueprints أو Endpoints غير مذكورة هنا إلا بعد تحديث هذا الملف.
3. حدّث هذا الملف بعد كل تعديل على المسارات أو القوالب أو النماذج.
4. استخدم التسمية الموحدة: blueprint_name.endpoint_name
مثال:  
`admin.edit_user`, `company_portal.offer_create`, `portal.profile`.
5. لا تُنشئ قوالب `base.html` أو `admin_base.html` جديدة.
6. بعد كل تعديل، أضف ملخص التغيير في `README.md`.

---

**تاريخ آخر تحديث:** 2025-10-25  
**الإصدار البنيوي:** ELITE v13.2  

