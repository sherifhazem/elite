// LINKED: Shared Offers & Redemptions Integration (no schema changes)
/* Offer management client-side logic handling modal forms and CRUD operations. */
/* UPDATED: Responsive Company Portal with Restricted Editable Fields. */

document.addEventListener("DOMContentLoaded", () => {
    const modalElement = document.getElementById("offer-modal");
    const modalBody = document.getElementById("offer-modal-body");
    const offerModal = modalElement ? new bootstrap.Modal(modalElement) : null;
    const toastContainer = document.getElementById("offers-toast-container");
    const searchInput = document.getElementById("offer-search");
    const table = document.getElementById("offers-table");
    const addButton = document.getElementById("offer-add-btn");

    const showToast = (message, type = "success") => {
        if (!toastContainer) return;
        const wrapper = document.createElement("div");
        wrapper.innerHTML = `
            <div class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>`;
        const toastEl = wrapper.firstElementChild;
        toastContainer.appendChild(toastEl);
        const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
        toast.show();
        toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
    };

    const toggleButtonLoading = (button, loading) => {
        if (!button) return;
        if (loading) {
            button.dataset.originalContent = button.innerHTML;
            button.innerHTML =
                "<span class='spinner-border spinner-border-sm me-2' role='status' aria-hidden='true'></span>Processing";
            button.disabled = true;
        } else if (button.dataset.originalContent) {
            button.innerHTML = button.dataset.originalContent;
            delete button.dataset.originalContent;
            button.disabled = false;
        }
    };

    const loadForm = async (url) => {
        if (!offerModal) return;
        offerModal.show();
        modalBody.innerHTML = "<div class='text-center py-5'><div class='spinner-border' role='status'></div></div>";
        try {
            const response = await fetch(url, { credentials: "same-origin" });
            if (!response.ok) throw new Error("Failed to load form");
            modalBody.innerHTML = await response.text();
            const form = modalBody.querySelector("#offer-form");
            if (form) {
                form.addEventListener("submit", handleFormSubmit);
            }
        } catch (error) {
            modalBody.innerHTML = "<p class='text-danger mb-0'>Unable to load form. Please try again.</p>";
        }
    };

    const handleFormSubmit = async (event) => {
        event.preventDefault();
        const form = event.target;
        const submitButton = form.querySelector("[type='submit']");
        toggleButtonLoading(submitButton, true);
        const formData = new FormData(form);
        const payload = Object.fromEntries(formData.entries());
        payload.send_notifications = formData.has("send_notifications");

        try {
            const response = await fetch(form.dataset.action, {
                method: form.dataset.method || "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
                credentials: "same-origin",
            });
            const result = await response.json();
            if (!response.ok || !result.ok) {
                throw new Error(result.message || "Failed to save offer");
            }
            showToast("Offer saved successfully.");
            offerModal.hide();
            window.location.reload();
        } catch (error) {
            showToast(error.message, "danger");
        } finally {
            toggleButtonLoading(submitButton, false);
        }
    };

    const handleDelete = async (offerId, triggerButton) => {
        if (!confirm("Delete this offer?")) return;
        toggleButtonLoading(triggerButton, true);
        try {
            const response = await fetch(`/company/offers/${offerId}/delete`, {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
                body: JSON.stringify({}),
            });
            const result = await response.json();
            if (!response.ok || !result.ok) {
                throw new Error(result.message || "Unable to delete offer");
            }
            showToast("Offer deleted.");
            window.location.reload();
        } catch (error) {
            showToast(error.message, "danger");
        } finally {
            toggleButtonLoading(triggerButton, false);
        }
    };

    const attachActionHandlers = () => {
        document.querySelectorAll(".offer-edit").forEach((button) => {
            if (button.dataset.enhanced) return;
            button.dataset.enhanced = "true";
            button.addEventListener("click", () => {
                const offerId = button.dataset.offerId;
                loadForm(`/company/offers/${offerId}/edit`);
            });
        });
        document.querySelectorAll(".offer-delete").forEach((button) => {
            if (button.dataset.enhanced) return;
            button.dataset.enhanced = "true";
            button.addEventListener("click", () => handleDelete(button.dataset.offerId, button));
        });
    };

    const sortTable = (key, ascending) => {
        if (!table) return;
        const tbody = table.querySelector("tbody");
        const rows = Array.from(tbody.querySelectorAll("tr"));
        rows.sort((a, b) => {
            const dataA = JSON.parse(a.dataset.offer || "{}");
            const dataB = JSON.parse(b.dataset.offer || "{}");
            const valueA = dataA[key] || "";
            const valueB = dataB[key] || "";
            if (valueA < valueB) return ascending ? -1 : 1;
            if (valueA > valueB) return ascending ? 1 : -1;
            return 0;
        });
        rows.forEach((row) => tbody.appendChild(row));
    };

    const filterRows = (query) => {
        const lowerQuery = query.toLowerCase();
        if (table) {
            table.querySelectorAll("tbody tr").forEach((row) => {
                const titleCell = row.querySelector(".offer-title");
                if (!titleCell) return;
                const matches = titleCell.textContent.toLowerCase().includes(lowerQuery);
                row.hidden = !matches;
            });
        }
        document.querySelectorAll(".offer-card").forEach((card) => {
            const title = card.querySelector(".offer-card-title");
            if (!title) return;
            const matches = title.textContent.toLowerCase().includes(lowerQuery);
            card.hidden = !matches;
        });
    };

    addButton?.addEventListener("click", (event) => {
        toggleButtonLoading(event.currentTarget, true);
        loadForm("/company/offers/new");
        setTimeout(() => toggleButtonLoading(event.currentTarget, false), 400);
    });

    searchInput?.addEventListener("input", (event) => {
        filterRows(event.target.value || "");
    });

    table?.querySelectorAll("th[data-sort-key]").forEach((header) => {
        let ascending = true;
        header.style.cursor = "pointer";
        header.addEventListener("click", () => {
            sortTable(header.dataset.sortKey, ascending);
            ascending = !ascending;
        });
    });

    attachActionHandlers();
});
