// Handles member account registration form submission.
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('register-form');
    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('register-email');
    const passwordInput = document.getElementById('register-password');
    const submitButton = document.getElementById('register-submit');
    const errorMessage = document.getElementById('register-error');
    const toast = document.getElementById('register-toast');
    const toastMessage = document.getElementById('register-toast-message');

    if (!form) return;

    const persistTokenCookie = (token) => {
        const expires = new Date(Date.now() + 24 * 60 * 60 * 1000).toUTCString();
        const secureFlag = window.location.protocol === 'https:' ? ' Secure;' : '';
        document.cookie = `elite_token=${token}; Path=/;${secureFlag} SameSite=Strict; Expires=${expires}`;
    };

    const showToast = (message) => {
        if (!toast || !toastMessage) return;
        toastMessage.textContent = message || 'تم إنشاء الحساب بنجاح';
        toast.dataset.visible = 'true';
        setTimeout(() => (toast.dataset.visible = 'false'), 3200);
    };

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const username = (usernameInput.value || '').trim();
        const email = (emailInput.value || '').trim();
        const password = passwordInput.value || '';

        if (!username || !email || !password) {
            errorMessage.textContent = 'يرجى تعبئة جميع الحقول المطلوبة.';
            return;
        }

        errorMessage.textContent = '';
        submitButton.disabled = true;
        submitButton.textContent = 'جاري إنشاء الحساب...';

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                errorMessage.textContent = data?.error || 'تعذر إنشاء الحساب، حاول مرة أخرى.';
                return;
            }

            if (data.token) {
                localStorage.setItem('elite_token', data.token);
                persistTokenCookie(data.token);
            }

            showToast('تم إنشاء حسابك بنجاح! جاري تحويلك...');
            const redirectTarget = data.redirect_url || form.dataset.successRedirect || '/portal/';
            setTimeout(() => {
                window.location.replace(redirectTarget);
            }, 1500);
        } catch (error) {
            console.error('Registration failed', error);
            errorMessage.textContent = 'حدث خطأ أثناء التسجيل. تحقق من اتصالك وحاول مجددًا.';
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'إنشاء حساب';
        }
    });
});
