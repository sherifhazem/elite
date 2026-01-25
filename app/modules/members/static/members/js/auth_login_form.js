// Handles member login submission, validation, and feedback.
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('login-form');
    const identifierInput = document.getElementById('login-identifier');
    const passwordInput = document.getElementById('login-password');
    const submitButton = document.getElementById('login-submit');
    const errorMessage = document.getElementById('login-error');
    const toast = document.getElementById('login-toast');
    const toastMessage = document.getElementById('login-toast-message');

    if (!form) return;

    const showToast = (message) => {
        if (!toast || !toastMessage) return;
        toastMessage.textContent = message || 'تم تسجيل الدخول بنجاح';
        toast.dataset.visible = 'true';
        setTimeout(() => (toast.dataset.visible = 'false'), 3000);
    };

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const identifier = (identifierInput.value || '').trim();
        const password = passwordInput.value || '';

        if (!identifier || !password) {
            errorMessage.textContent = 'يرجى إدخال رقم الجوال/البريد وكلمة المرور.';
            return;
        }

        errorMessage.textContent = '';
        submitButton.disabled = true;
        submitButton.textContent = 'جاري تسجيل الدخول...';

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ identifier, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                errorMessage.textContent = data?.error || 'فشل تسجيل الدخول. تحقق من البيانات.';
                return;
            }

            // Handle legacy user needs (phone link or verification)
            if (data.requires_phone) {
                window.location.replace(`/link-phone?id=${data.id}`);
                return;
            }
            if (data.requires_verification) {
                window.location.replace(`/verify-otp?phone=${data.phone}`);
                return;
            }

            showToast('تم تسجيل الدخول بنجاح! جاري تحويلك...');
            const redirectTarget = data.redirect_url || form.dataset.successRedirect || '/portal/';
            setTimeout(() => {
                window.location.replace(redirectTarget);
            }, 1200);
        } catch (error) {
            console.error('Login failed', error);
            errorMessage.textContent = 'حدث خطأ أثناء تسجيل الدخول. حاول لاحقًا.';
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'تسجيل الدخول';
        }
    });
});
