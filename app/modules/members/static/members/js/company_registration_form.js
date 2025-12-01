// Validates and handles company registration submission feedback.
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('register-company-form');
    const submitButton = document.getElementById('register-company-submit');
    const errorMessage = document.getElementById('company-error');
    const toast = document.getElementById('company-toast');
    const toastMessage = document.getElementById('company-toast-message');

    if (!form) return;

    const showToast = (message) => {
        if (!toast || !toastMessage) return;
        toastMessage.textContent = message || 'تم إرسال الطلب بنجاح';
        toast.dataset.visible = 'true';
        setTimeout(() => (toast.dataset.visible = 'false'), 3200);
    };

    form.addEventListener('submit', (event) => {
        if (!form.checkValidity()) {
            event.preventDefault();
            errorMessage.textContent = 'يرجى تعبئة جميع الحقول المطلوبة بشكل صحيح.';
            form.classList.add('was-validated');
        } else {
            errorMessage.textContent = '';
            submitButton.disabled = true;
            submitButton.textContent = 'جاري الإرسال...';
            showToast('تم إرسال طلب شركتك بنجاح! سيتم مراجعة الطلب قريبًا.');
        }
    });
});
