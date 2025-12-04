(function () {
    const form = document.querySelector('#company-settings-form');
    if (!form) return;

    const toastContainer = document.getElementById('settings-toast-container');
    const submitButton = document.getElementById('settings-submit-btn');
    const logoInput = document.getElementById('company-logo');
    const logoPreview = document.getElementById('company-logo-preview');

    function showToast(message, level = 'success') {
        if (!toastContainer) {
            alert(message);
            return;
        }

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-bg-${level} border-0`;
        toast.role = 'alert';
        toast.ariaLive = 'assertive';
        toast.ariaAtomic = 'true';

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        toastContainer.appendChild(toast);

        // Bootstrap 5 toast initialization
        const bootstrapToast = new bootstrap.Toast(toast, { delay: 4000 });
        bootstrapToast.show();

        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    }

    function setBusy(state) {
        if (!submitButton) return;
        submitButton.disabled = state;
        submitButton.textContent = state ? 'Saving…' : 'Save changes';
    }

    function previewLogo(file) {
        if (!file || !logoPreview) return;
        const url = URL.createObjectURL(file);
        logoPreview.src = url;
    }

    logoInput?.addEventListener('change', (event) => {
        const file = event.target?.files?.[0];
        previewLogo(file);
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const formData = new FormData(form);
        setBusy(true);

        try {
            const response = await fetch(form.dataset.action, {
                method: 'POST',
                body: formData,
                headers: { Accept: 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
            });

            const payload = await response.json().catch(() => ({}));
            if (payload.ok) {
                if (payload.logo_url && logoPreview) {
                    logoPreview.src = payload.logo_url;
                }
                showToast(payload.message || 'تم حفظ التغييرات بنجاح.', 'success');
            } else {
                const message = payload.message || 'تعذر حفظ الإعدادات. حاول مرة أخرى.';
                showToast(message, 'danger');
            }
        } catch (error) {
            showToast('حدث خطأ غير متوقع أثناء الحفظ.', 'danger');
        } finally {
            setBusy(false);
        }
    });
})();
