// Offer management interactions for the company portal.

/* global bootstrap */

const OFFER_ENDPOINTS = {
    new: '/company/offers/new',
    edit: (id) => `/company/offers/${id}/edit`,
    update: (id) => `/company/offers/${id}`,
    delete: (id) => `/company/offers/${id}/delete`,
};

const toastContainer = document.getElementById('offers-toast-container');
const modalElement = document.getElementById('offer-modal');
const modalBody = document.getElementById('offer-modal-body');
const modalTitle = modalElement?.querySelector('.modal-title');
const offerModal = modalElement ? new bootstrap.Modal(modalElement) : null;

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

function parseOfferPayload(triggerElement) {
    const wrapper = triggerElement.closest('[data-offer]');
    if (!wrapper) return null;
    try {
        return JSON.parse(wrapper.dataset.offer || '{}');
    } catch (error) {
        console.error('Unable to parse offer payload', error);
        return null;
    }
}

async function loadOfferForm(url, title) {
    if (!offerModal) return;

    modalTitle.textContent = title;
    modalBody.innerHTML = '<p class="text-muted mb-0">Loading form...</p>';
    offerModal.show();

    try {
        const response = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        const html = await response.text();
        modalBody.innerHTML = html;

        const form = modalBody.querySelector('#offer-form');
        if (form) {
            form.addEventListener('submit', submitOfferForm, { once: true });
        }
    } catch (error) {
        modalBody.innerHTML = '<p class="text-danger mb-0">Unable to load the offer form.</p>';
        showToast('Could not open the offer form. Please try again.', 'danger');
    }
}

function normalizeFormData(form) {
    const formData = new FormData(form);
    const payload = {};
    formData.forEach((value, key) => {
        payload[key] = value;
    });

    if (formData.has('send_notifications')) {
        payload.send_notifications = formData.get('send_notifications') === 'on' || formData.get('send_notifications') === 'true';
    }

    return payload;
}

async function submitOfferForm(event) {
    event.preventDefault();
    const form = event.target;
    const action = form.dataset.action || form.getAttribute('action');
    const method = (form.dataset.method || form.getAttribute('method') || 'POST').toUpperCase();
    const payload = normalizeFormData(form);

    try {
        const response = await fetch(action, {
            method,
            headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await response.json();

        if (!response.ok || !data.ok) {
            throw new Error(data.message || 'Unable to save offer.');
        }

        showToast('Offer saved successfully.', 'success');
        offerModal.hide();
        setTimeout(() => window.location.reload(), 400);
    } catch (error) {
        console.error('Offer save failed', error);
        showToast(error.message || 'Unable to save offer.', 'danger');
    }
}

async function deleteOffer(offerId) {
    if (!offerId) return;
    if (!confirm('Are you sure you want to delete this offer? This cannot be undone.')) return;

    try {
        const response = await fetch(OFFER_ENDPOINTS.delete(offerId), {
            method: 'DELETE',
            headers: { Accept: 'application/json' },
        });
        const data = await response.json();

        if (!response.ok || !data.ok) {
            throw new Error(data.message || 'Unable to delete offer.');
        }

        showToast('Offer deleted.', 'success');
        setTimeout(() => window.location.reload(), 300);
    } catch (error) {
        console.error('Offer deletion failed', error);
        showToast(error.message || 'Unable to delete offer.', 'danger');
    }
}

async function updateOfferStatus(offerId, status, triggerElement) {
    const offerPayload = parseOfferPayload(triggerElement);
    if (!offerPayload) {
        showToast('Unable to read offer details. Please refresh and try again.', 'danger');
        return;
    }

    const statusMessages = {
        paused: 'stop this offer',
        archived: 'archive this offer',
        active: 'activate this offer',
    };

    const confirmationLabel = statusMessages[status] || 'update this offer';
    if (!confirm(`Are you sure you want to ${confirmationLabel}?`)) return;

    const payload = {
        ...offerPayload,
        status,
    };

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
            throw new Error(data.message || 'Unable to update offer.');
        }

        const successMessages = {
            paused: 'Offer stopped.',
            archived: 'Offer archived.',
            active: 'Offer activated.',
        };
        showToast(successMessages[status] || 'Offer updated.', 'success');
        setTimeout(() => window.location.reload(), 350);
    } catch (error) {
        console.error('Offer status update failed', error);
        showToast(error.message || 'Unable to update offer.', 'danger');
    }
}

function handleActionButtons() {
    const offerAddButton = document.getElementById('offer-add-btn');
    if (offerAddButton) {
        offerAddButton.addEventListener('click', () => {
            const formUrl = offerAddButton.dataset.offerUrl || OFFER_ENDPOINTS.new;
            loadOfferForm(formUrl, 'Add Offer');
        });
    }

    document.addEventListener('click', (event) => {
        const editButton = event.target.closest('.offer-edit');
        if (editButton) {
            const offerId = editButton.dataset.offerId;
            loadOfferForm(OFFER_ENDPOINTS.edit(offerId), 'Edit Offer');
            return;
        }

        const stopButton = event.target.closest('.offer-stop');
        if (stopButton) {
            updateOfferStatus(stopButton.dataset.offerId, 'paused', stopButton);
            return;
        }

        const archiveButton = event.target.closest('.offer-archive');
        if (archiveButton) {
            updateOfferStatus(archiveButton.dataset.offerId, 'archived', archiveButton);
            return;
        }

        const deleteButton = event.target.closest('.offer-delete');
        if (deleteButton) {
            deleteOffer(deleteButton.dataset.offerId);
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    handleActionButtons();
});
