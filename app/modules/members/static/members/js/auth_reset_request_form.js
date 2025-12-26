// Handles password reset request submission and messaging.
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('reset-request-form');
    const emailInput = document.getElementById('reset-email');
    const submitButton = document.getElementById('reset-submit');
    const feedback = document.getElementById('reset-feedback');

    if (!form) return;

    const setFeedback = (message, isSuccess = false) => {
        if (!feedback) return;
        feedback.textContent = message || '';
        feedback.classList.remove('text-success', 'text-danger');
        feedback.classList.add(isSuccess ? 'text-success' : 'text-danger');
    };

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const email = (emailInput.value || '').trim();

        if (!email) {
            setFeedback('يرجى إدخال البريد الإلكتروني.', false);
            return;
        }

        setFeedback('جاري إرسال الرابط إلى بريدك الإلكتروني...', true);
        submitButton.disabled = true;
        submitButton.textContent = 'جارٍ الإرسال...';

        try {
            const response = await fetch('/api/auth/reset-request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });

            const data = await response.json();

            if (!response.ok) {
                const message = data?.message || 'تعذر إرسال الرابط. تحقق من البريد الإلكتروني وأعد المحاولة.';
                setFeedback(message, false);
                return;
            }

            setFeedback('إذا كان البريد الإلكتروني مسجلاً لدينا، ستصلك رسالة لإعادة تعيين كلمة المرور.', true);
        } catch (error) {
            console.error('Password reset request failed', error);
            setFeedback('حدث خطأ غير متوقع. حاول مرة أخرى لاحقًا.', false);
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'إرسال رابط إعادة التعيين';
        }
    });
});
