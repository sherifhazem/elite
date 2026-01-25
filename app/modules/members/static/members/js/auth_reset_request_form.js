// Handles password reset request submission and messaging.
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('reset-request-form');
    const identifierInput = document.getElementById('reset-identifier');
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
        const identifier = (identifierInput.value || '').trim();

        if (!identifier) {
            setFeedback('يرجى إدخال البريد الإلكتروني أو رقم الجوال.', false);
            return;
        }

        setFeedback('جاري معالجة طلبك...', true);
        submitButton.disabled = true;
        submitButton.textContent = 'جارٍ الإرسال...';

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

            const response = await fetch('/api/auth/reset-request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ identifier }),
            });

            const data = await response.json();

            if (!response.ok) {
                const message = data?.message || 'تعذر إرسال الطلب. تحقق من البيانات وأعد المحاولة.';
                setFeedback(message, false);
                return;
            }

            setFeedback('إذا كان الحساب مسجلاً لدينا، ستصلك رسالة لإعادة تعيين كلمة المرور عبر البريد أو الجوال.', true);
        } catch (error) {
            console.error('Password reset request failed', error);
            setFeedback('حدث خطأ غير متوقع. حاول مرة أخرى لاحقًا.', false);
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'إرسال رابط إعادة التعيين';
        }
    });
});
