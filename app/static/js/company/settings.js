/* Company settings client script submitting profile updates over fetch. */

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

    form?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const submitButton = form.querySelector("[type='submit']");
        submitButton.disabled = true;
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
            if (!response.ok || !result.ok) {
                throw new Error(result.message || "Unable to save settings");
            }
            showToast("Settings saved successfully.");
        } catch (error) {
            showToast(error.message, "danger");
        } finally {
            submitButton.disabled = false;
        }
    });
});
