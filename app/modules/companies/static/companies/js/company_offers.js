// Offer management interactions for the company portal.

/* global bootstrap */

const OFFER_ENDPOINTS = {
    update: (id) => `/company/offers/${id}`,
    delete: (id) => `/company/offers/${id}/delete`,
};

const toastContainer = document.getElementById('offers-toast-container');

function showToast(message, variant = 'primary') {
    if (!toastContainer) return;

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-bg-${variant} border-0`;
    toastEl.role = 'alert';
    toastEl.ariaLive = 'assertive';
    toastEl.ariaAtomic = 'true';
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

async function deleteOffer(offerId) {
    if (!offerId) return;
    if (!confirm('هل أنت متأكد من رغبتك في حذف هذا العرض؟ لا يمكن التراجع عن هذا الإجراء.')) return;

    try {
        const response = await fetch(OFFER_ENDPOINTS.delete(offerId), {
            method: 'DELETE',
            headers: { Accept: 'application/json' },
        });
        const data = await response.json();

        if (!response.ok || !data.ok) {
            throw new Error(data.message || 'تعذر حذف العرض.');
        }

        showToast('تم حذف العرض بنجاح.', 'success');
        setTimeout(() => window.location.reload(), 300);
    } catch (error) {
        console.error('Offer deletion failed', error);
        showToast(error.message || 'تعذر حذف العرض.', 'danger');
    }
}

async function updateOfferStatus(offerId, status) {
    if (!offerId) return;

    const statusMessages = {
        paused: 'إيقاف هذا العرض مؤقتاً',
        archived: 'أرشفة هذا العرض',
        active: 'تفعيل هذا العرض',
    };
    const confirmationLabel = statusMessages[status] || 'تحديث هذا العرض';
    if (!confirm(`هل أنت متأكد من رغبتك في ${confirmationLabel}؟`)) return;

    const payload = { status };
    if (status === 'paused') {
        const today = new Date();
        payload.valid_until = today.toISOString().slice(0, 10);
    }

    try {
        const response = await fetch(OFFER_ENDPOINTS.update(offerId), {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await response.json();

        if (!response.ok || !data.ok) {
            throw new Error(data.message || 'تعذر تحديث العرض.');
        }

        const successMessages = {
            paused: 'تم إيقاف العرض مؤقتاً.',
            archived: 'تم أرشفة العرض.',
            active: 'تم تفعيل العرض.',
        };
        showToast(successMessages[status] || 'تم تحديث العرض.', 'success');
        setTimeout(() => window.location.reload(), 350);
    } catch (error) {
        console.error('Offer status update failed', error);
        showToast(error.message || 'تعذر تحديث العرض.', 'danger');
    }
}

function handleActionButtons() {
    document.addEventListener('click', (event) => {
        const stopButton = event.target.closest('.offer-stop');
        if (stopButton) {
            updateOfferStatus(stopButton.dataset.offerId, 'paused');
            return;
        }

        const archiveButton = event.target.closest('.offer-archive');
        if (archiveButton) {
            updateOfferStatus(archiveButton.dataset.offerId, 'archived');
            return;
        }

        const activateButton = event.target.closest('.offer-activate');
        if (activateButton) {
            updateOfferStatus(activateButton.dataset.offerId, 'active');
            return;
        }

        const deleteButton = event.target.closest('.offer-delete');
        if (deleteButton) {
            deleteOffer(deleteButton.dataset.offerId);
        }
    });
}

window.addEventListener('DOMContentLoaded', () => {
    handleActionButtons();
});
