/* -*- coding: utf-8 -*- */
// انتظر تحميل عناصر الصفحة قبل تشغيل أي منطق.
document.addEventListener("DOMContentLoaded", () => {
  // التقط عناصر النموذج والأزرار والرسائل من الصفحة.
  const form = document.getElementById("loginForm");
  if (!form) {
    return;
  }
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");
  const submitButton = document.getElementById("login-button");
  const errorMessage = document.getElementById("login-error");
  const forgotPasswordTrigger = document.getElementById(
    "forgot-password-trigger",
  );
  const resetModal = document.getElementById("reset-modal");
  const resetForm = document.getElementById("reset-form");
  const resetEmailInput = document.getElementById("reset-email");
  const resetFeedback = document.getElementById("reset-feedback");
  const resetSubmitButton = document.getElementById("reset-submit");
  const resetCancelButton = document.getElementById("reset-cancel");

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

    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfMeta ? csrfMeta.getAttribute("content") : "";

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
      const response = await fetch(form.action, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
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
        member: "/portal/",
        company: "/company/",
        admin: "/admin/",
        superadmin: "/admin/",
      };
      const target = data.redirect_url || roleRedirects[role] || "/portal/";

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

  // Helper to toggle the password reset modal visibility for accessibility.
  const toggleResetModal = (shouldShow) => {
    resetModal.hidden = !shouldShow;
    if (shouldShow) {
      resetEmailInput.focus();
    } else {
      forgotPasswordTrigger.focus();
      resetForm.reset();
      resetFeedback.textContent = "";
    }
  };

  if (forgotPasswordTrigger) {
    forgotPasswordTrigger.addEventListener("click", () => {
      toggleResetModal(true);
    });
  }

  if (resetCancelButton) {
    resetCancelButton.addEventListener("click", () => {
      toggleResetModal(false);
    });
  }

  if (resetForm) {
    resetForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const email = (resetEmailInput.value || "").trim();
      if (!email) {
        resetFeedback.textContent = "يرجى إدخال البريد الإلكتروني.";
        resetEmailInput.setAttribute("aria-invalid", "true");
        return;
      }

      resetFeedback.textContent = "";
      resetEmailInput.setAttribute("aria-invalid", "false");
      resetSubmitButton.disabled = true;
      resetSubmitButton.textContent = "جاري الإرسال...";

      try {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        const csrfToken = csrfMeta ? csrfMeta.getAttribute("content") : "";

        const response = await fetch("/api/auth/reset-request", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({ email }),
        });
        const data = await response.json();

        if (!response.ok) {
          resetFeedback.textContent = data?.message || "تعذر إرسال البريد.";
          resetEmailInput.setAttribute("aria-invalid", "true");
          return;
        }

        resetFeedback.textContent = "تم إرسال رابط الاستعادة إلى بريدك الإلكتروني.";
        setTimeout(() => toggleResetModal(false), 1800);
      } catch (error) {
        console.error("Password reset request failed", error);
        resetFeedback.textContent = "حدث خطأ أثناء الإرسال، حاول مرة أخرى.";
      } finally {
        resetSubmitButton.disabled = false;
        resetSubmitButton.textContent = "إرسال الرابط";
      }
    });
  }
});
