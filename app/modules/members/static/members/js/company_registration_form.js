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
        const normalizeUrl = (value) => {
            const trimmed = (value || '').trim();
            if (!trimmed) return '';

            const lower = trimmed.toLowerCase();
            if (lower.startsWith('http://') || lower.startsWith('https://')) return trimmed;
            if (trimmed.startsWith('www.')) return `https://${trimmed}`;
            if (/^\d/.test(trimmed)) return `https://www.${trimmed}`;
            if (trimmed.includes('.')) return `https://${trimmed}`;
            return trimmed;
        };

        const websiteInput = form.querySelector('[name="website_url"]');
        const socialInput = form.querySelector('[name="social_url"]');

        if (websiteInput) {
            const normalized = normalizeUrl(websiteInput.value);
            websiteInput.value = normalized;
        }
        if (socialInput) {
            const normalized = normalizeUrl(socialInput.value);
            socialInput.value = normalized;
        }

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
