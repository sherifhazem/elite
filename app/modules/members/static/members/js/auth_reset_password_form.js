// Handles the password reset submission from the browser UI.
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('reset-password-form');
    const passwordInput = document.getElementById('new_password');
    const confirmInput = document.getElementById('confirm_password');
    const submitButton = document.getElementById('reset-submit');
    const feedback = document.getElementById('reset-feedback');

    if (!form) return;

    const endpoint = form.dataset.resetEndpoint;
    const loginUrl = form.dataset.loginUrl || '/login';

    const setFeedback = (message, isSuccess = false) => {
        if (!feedback) return;
        feedback.textContent = message || '';
        feedback.classList.remove('text-success', 'text-danger');
        feedback.classList.add(isSuccess ? 'text-success' : 'text-danger');
    };

    const setLoadingState = (isLoading) => {
        if (!submitButton) return;
        submitButton.disabled = isLoading;
        submitButton.textContent = isLoading ? 'جارٍ الحفظ...' : 'حفظ كلمة المرور';
    };

    const validatePasswords = () => {
        const password = (passwordInput?.value || '').trim();
        const confirmPassword = (confirmInput?.value || '').trim();

        if (!password) {
            setFeedback('يرجى إدخال كلمة مرور جديدة.', false);
            passwordInput?.focus();
            return false;
        }

        if (password.length < 8) {
            setFeedback('يجب ألا تقل كلمة المرور عن 8 أحرف.', false);
            passwordInput?.focus();
            return false;
        }

        if (password !== confirmPassword) {
            setFeedback('كلمتا المرور غير متطابقتين.', false);
            confirmInput?.focus();
            return false;
        }

        setFeedback('');
        return true;
    };

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        if (!validatePasswords()) return;

        setLoadingState(true);
        setFeedback('جارٍ تحديث كلمة المرور...', true);

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: passwordInput.value }),
            });

            const data = await response.json();

            if (!response.ok) {
                const message = data?.message || 'تعذر تحديث كلمة المرور. حاول مرة أخرى.';
                setFeedback(message, false);
                return;
            }

            setFeedback('تم تحديث كلمة المرور بنجاح! سيتم تحويلك لتسجيل الدخول.', true);
            submitButton.textContent = 'تم الحفظ';
            submitButton.disabled = true;

            setTimeout(() => {
                window.location.href = loginUrl;
            }, 1500);
        } catch (error) {
            console.error('Password reset failed', error);
            setFeedback('حدث خطأ غير متوقع. حاول مرة أخرى لاحقًا.', false);
        } finally {
            setLoadingState(false);
        }
    });
});
