/* -*- coding: utf-8 -*- */
// انتظر تحميل عناصر الصفحة قبل تشغيل أي منطق.
document.addEventListener("DOMContentLoaded", () => {
  // التقط عناصر النموذج والأزرار والرسائل من الصفحة.
  const form = document.getElementById("login-form");
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");
  const submitButton = document.getElementById("login-button");
  const errorMessage = document.getElementById("login-error");

  // عرّف دالة مساعدة لحفظ التوكن في Cookie مع تاريخ انتهاء مناسب.
  const persistTokenCookie = (token) => {
    // احسب وقت الانتهاء (24 ساعة من الآن) بصيغة UTC.
    const expires = new Date(Date.now() + 24 * 60 * 60 * 1000).toUTCString();
    // جهّز العلامات الأمنية (Secure وSameSite) بحسب بروتوكول الصفحة الحالية.
    const secureFlag = window.location.protocol === "https:" ? " Secure;" : "";
    document.cookie = `elite_token=${token}; Path=/;${secureFlag} SameSite=Strict; Expires=${expires}`;
  };

  // اربط مستمع حدث الإرسال على النموذج لمعالجة بيانات تسجيل الدخول.
  form.addEventListener("submit", async (event) => {
    // امنع السلوك الافتراضي للنموذج حتى لا يتم إعادة تحميل الصفحة.
    event.preventDefault();

    // نظّف رسالة الخطأ وأعد ضبط مظهر الإدخالات قبل المحاولة.
    errorMessage.textContent = "";
    emailInput.setAttribute("aria-invalid", "false");
    passwordInput.setAttribute("aria-invalid", "false");

    // اجمع بيانات البريد الإلكتروني وكلمة المرور من الحقول.
    const email = (emailInput.value || "").trim();
    const password = passwordInput.value || "";

    // في حال كانت المدخلات ناقصة أظهر رسالة للمستخدم وانهِ التنفيذ مبكرًا.
    if (!email || !password) {
      errorMessage.textContent = "يرجى إدخال البريد الإلكتروني وكلمة المرور.";
      emailInput.setAttribute("aria-invalid", String(!email));
      passwordInput.setAttribute("aria-invalid", String(!password));
      return;
    }

    // عطّل الزر مؤقتًا لمنع النقرات المتكررة أثناء إرسال الطلب.
    submitButton.disabled = true;
    submitButton.textContent = "جاري التحقق...";

    try {
      // أرسل طلب POST إلى واجهة تسجيل الدخول مع البيانات في صيغة JSON.
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      // حلّل الرد ككائن JSON لاستنتاج النجاح أو الفشل.
      const data = await response.json();

      // في حالة فشل المصادقة، عالج الرسالة وأعد تمكين الزر.
      if (!response.ok) {
        const message = data?.error || "تعذر تسجيل الدخول، حاول مرة أخرى.";
        errorMessage.textContent = message;
        emailInput.setAttribute("aria-invalid", "true");
        passwordInput.setAttribute("aria-invalid", "true");
        return;
      }

      // خزّن الـ JWT في localStorage لتستخدمه الطلبات المستقبلية عبر JavaScript.
      localStorage.setItem("elite_token", data.token);

      // خزّن الـ JWT في Cookie حتى يتمكن الخادم من قراءته عند إعادة التوجيه.
      persistTokenCookie(data.token);

      // حدد وجهة الانتقال وفق الدور المرسل من الخادم مع قيمة احتياطية.
      const role = (data.role || "member").toLowerCase();
      const roleRedirects = {
        member: data.redirect_url || "/portal/",
        company: "/company/",
        admin: "/admin/",
        superadmin: "/admin/",
      };
      const target = roleRedirects[role] || "/portal/";

      // استخدم window.location لاستبدال الصفحة الحالية وتجنب الرجوع للوراء.
      window.location.replace(target);
    } catch (error) {
      // في حال حدوث استثناء (مثل انقطاع الشبكة) أخبر المستخدم بالسبب المحتمل.
      console.error("Login failed", error);
      errorMessage.textContent = "حدث خطأ غير متوقع، تحقق من الاتصال وحاول مرة أخرى.";
    } finally {
      // أعد تمكين الزر وأعد النص الافتراضي بعد اكتمال العملية.
      submitButton.disabled = false;
      submitButton.textContent = "تسجيل الدخول";
    }
  });
});
