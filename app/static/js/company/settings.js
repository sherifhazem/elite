/* Company settings client script submitting profile updates over fetch. */
/* UPDATED: Responsive Company Portal with Restricted Editable Fields. */

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("company-settings-form");
    const toastContainer = document.getElementById("settings-toast-container");

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
                "<span class='spinner-border spinner-border-sm me-2' role='status' aria-hidden='true'></span>Saving";
            button.disabled = true;
        } else if (button.dataset.originalContent) {
            button.innerHTML = button.dataset.originalContent;
            delete button.dataset.originalContent;
            button.disabled = false;
        }
    };

    const restrictedFields = form?.querySelectorAll("[data-restricted-field]");
    const notifyRestriction = () => {
        showToast("هذا الحقل لا يمكن تعديله إلا بموافقة الإدارة.", "warning");
    };
    restrictedFields?.forEach((field) => {
        field.addEventListener("focus", notifyRestriction);
        field.addEventListener("click", notifyRestriction);
    });

    form?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const submitButton = form.querySelector("[type='submit']");
        toggleButtonLoading(submitButton, true);
        const formData = new FormData(form);
        const payload = Object.fromEntries(formData.entries());
        payload.notify_email = formData.has("notify_email");
        payload.notify_sms = formData.has("notify_sms");

        try {
            const response = await fetch(form.dataset.action, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
                body: JSON.stringify(payload),
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.message || "Unable to save settings");
            }
            if (!result.ok) {
                showToast(result.message || "يتطلب موافقة الإدارة.", result.level || "warning");
                return;
            }
            showToast(result.message || "تم حفظ التغييرات بنجاح.");
        } catch (error) {
            showToast(error.message, "danger");
        } finally {
            toggleButtonLoading(submitButton, false);
        }
    });
});
