// Handles member login submission, validation, and feedback.
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('login-form');
    const emailInput = document.getElementById('login-email');
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
        const email = (emailInput.value || '').trim();
        const password = passwordInput.value || '';

        if (!email || !password) {
            errorMessage.textContent = 'يرجى إدخال البريد الإلكتروني وكلمة المرور.';
            return;
        }

        errorMessage.textContent = '';
        submitButton.disabled = true;
        submitButton.textContent = 'جاري تسجيل الدخول...';

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                errorMessage.textContent = data?.error || 'فشل تسجيل الدخول. تحقق من البيانات.';
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
