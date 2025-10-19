// LINKED: Shared Offers & Redemptions Integration (no schema changes)
/* Redemption verification workflow supporting manual input and QR scanning. */
/* UPDATED: Responsive Company Portal with Restricted Editable Fields. */

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("redemption-verify-form");
    const codeInput = document.getElementById("redemption-code");
    const resultContainer = document.getElementById("redemption-result");
    const toastContainer = document.getElementById("redemption-toast-container");
    const scanButton = document.getElementById("redemption-scan-btn");
    const verifyButton = document.getElementById("redemption-verify-btn");
    const scannerWrapper = document.getElementById("qr-scanner");
    const videoElement = document.getElementById("qr-video");
    const stopButton = document.getElementById("qr-stop-btn");
    const filterForm = document.getElementById("redemption-filter");
    const refreshButton = document.getElementById("redemption-refresh");
    const tableBody = document.querySelector("#recent-redemptions tbody");
    const cardsContainer = document.querySelector("[data-redemption-cards]");

    let lastRedemptionId = null;
    let barcodeDetector = null;
    let scanStream = null;
    let scanning = false;

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

    const toggleButtonLoading = (button, loading, label = "Processing") => {
        if (!button) return;
        if (loading) {
            button.dataset.originalContent = button.innerHTML;
            button.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>${label}`;
            button.disabled = true;
        } else if (button.dataset.originalContent) {
            button.innerHTML = button.dataset.originalContent;
            button.disabled = false;
            delete button.dataset.originalContent;
        }
    };

    const renderResult = (status, message, redemptionId = null) => {
        lastRedemptionId = redemptionId;
        const isSuccess = status === "pending" || status === "redeemed";
        const badgeClass = status === "redeemed" ? "bg-success" : status === "pending" ? "bg-warning" : "bg-secondary";
        const confirmButton = status === "pending" && redemptionId
            ? `<button class="btn btn-elite-primary mt-3" id="redemption-confirm-btn">Redeem now</button>`
            : "";
        resultContainer.innerHTML = `
            <div class="alert ${isSuccess ? "alert-success" : "alert-danger"}" role="alert">
                <div class="d-flex justify-content-between align-items-center gap-3 flex-wrap">
                    <span>${message}</span>
                    <span class="badge ${badgeClass} text-uppercase">${status || "unknown"}</span>
                </div>
                ${confirmButton}
            </div>`;
        if (confirmButton) {
            const confirmAction = document.getElementById("redemption-confirm-btn");
            confirmAction.addEventListener("click", () => confirmRedemption(confirmAction));
        }
    };

    const verifyCode = async (code) => {
        toggleButtonLoading(verifyButton, true, "Verifying");
        try {
            const response = await fetch("/company/redemptions/verify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
                body: JSON.stringify({ code }),
            });
            const result = await response.json();
            if (!response.ok || !result.ok) {
                throw new Error(result.message || "Verification failed");
            }
            const status = result.status || "pending";
            renderResult(status, `Code ${code} is valid.`, result.redemption_id);
            showToast("Code verified successfully.");
            refreshRedemptionListing();
        } catch (error) {
            renderResult("error", error.message);
            showToast(error.message, "danger");
        } finally {
            toggleButtonLoading(verifyButton, false);
        }
    };

    const confirmRedemption = async (button) => {
        if (!lastRedemptionId && !codeInput.value) return;
        toggleButtonLoading(button, true, "Confirming");
        try {
            const response = await fetch("/company/redemptions/confirm", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
                body: JSON.stringify({ redemption_id: lastRedemptionId, code: codeInput.value }),
            });
            const result = await response.json();
            if (!response.ok || !result.ok) {
                throw new Error(result.message || "Unable to confirm redemption");
            }
            renderResult(result.status, "Redemption confirmed.", lastRedemptionId);
            showToast("Redemption confirmed.");
            refreshRedemptionListing();
        } catch (error) {
            showToast(error.message, "danger");
        } finally {
            toggleButtonLoading(button, false);
        }
    };

    const buildParams = () => {
        if (!filterForm) return new URLSearchParams();
        const formData = new FormData(filterForm);
        const params = new URLSearchParams();
        formData.forEach((value, key) => {
            if (value) {
                params.append(key, value);
            }
        });
        return params;
    };

    const formatDate = (value) => {
        if (!value) return "—";
        try {
            const date = new Date(value);
            if (Number.isNaN(date.getTime())) return value;
            return date.toLocaleString(undefined, { hour12: false });
        } catch (error) {
            return value;
        }
    };

    const refreshRedemptionListing = async () => {
        if (!tableBody) return;
        try {
            const params = buildParams();
            const query = params.toString();
            const response = await fetch(`/company/redemptions/data${query ? `?${query}` : ""}`, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                credentials: "same-origin",
            });
            if (!response.ok) {
                throw new Error("Unable to refresh redemptions");
            }
            const payload = await response.json();
            const items = Array.isArray(payload.items) ? payload.items : [];
            tableBody.innerHTML = "";
            if (items.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">No redemption attempts recorded.</td></tr>';
            } else {
                items.forEach((item) => {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td>${item.code || "—"}</td>
                        <td>${item.user && item.user.username ? `${item.user.username}<br><small class="text-muted">${item.user.email || ""}</small>` : "—"}</td>
                        <td>${item.offer && item.offer.title ? item.offer.title : "—"}</td>
                        <td>${item.status || "pending"}</td>
                        <td>${formatDate(item.created_at)}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }
            if (cardsContainer) {
                cardsContainer.innerHTML = "";
                if (items.length === 0) {
                    cardsContainer.innerHTML = '<p class="text-muted mb-0">No redemption attempts recorded.</p>';
                } else {
                    items.forEach((item) => {
                        const card = document.createElement("article");
                        card.className = "redemption-card-item";
                        card.innerHTML = `
                            <div><span class="label">Code</span><span class="value">${item.code || "—"}</span></div>
                            <div><span class="label">Member</span><span class="value">${item.user && item.user.username ? item.user.username : "—"}</span></div>
                            <div><span class="label">Offer</span><span class="value">${item.offer && item.offer.title ? item.offer.title : "—"}</span></div>
                            <div><span class="label">Status</span><span class="value">${item.status || "pending"}</span></div>
                            <div><span class="label">Created</span><span class="value">${formatDate(item.created_at)}</span></div>
                        `;
                        cardsContainer.appendChild(card);
                    });
                }
            }
        } catch (error) {
            console.error("Failed to refresh redemptions", error);
        }
    };

    form?.addEventListener("submit", (event) => {
        event.preventDefault();
        const code = codeInput.value.trim();
        if (!code) return;
        verifyCode(code);
    });

    filterForm?.addEventListener("submit", (event) => {
        event.preventDefault();
        refreshRedemptionListing();
    });

    refreshButton?.addEventListener("click", (event) => {
        event.preventDefault();
        refreshRedemptionListing();
    });

    refreshRedemptionListing();

    const stopScanner = () => {
        scanning = false;
        scannerWrapper?.setAttribute("hidden", "hidden");
        if (scanStream) {
            scanStream.getTracks().forEach((track) => track.stop());
            scanStream = null;
        }
    };

    const scanLoop = async () => {
        if (!scanning || !barcodeDetector || !videoElement) return;
        try {
            const barcodes = await barcodeDetector.detect(videoElement);
            if (barcodes.length > 0) {
                const code = barcodes[0].rawValue;
                stopScanner();
                verifyCode(code);
                codeInput.value = code;
                return;
            }
        } catch (error) {
            console.error("Barcode detection error", error);
        }
        if (scanning) {
            requestAnimationFrame(scanLoop);
        }
    };

    const startScanner = async () => {
        if (!("BarcodeDetector" in window)) {
            showToast("QR scanning is not supported in this browser.", "warning");
            return;
        }
        try {
            barcodeDetector = new BarcodeDetector({ formats: ["qr_code"] });
            scanStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
            if (!videoElement) return;
            videoElement.srcObject = scanStream;
            scannerWrapper?.removeAttribute("hidden");
            scanning = true;
            requestAnimationFrame(scanLoop);
        } catch (error) {
            showToast("Unable to start camera. Check permissions.", "danger");
        }
    };

    scanButton?.addEventListener("click", () => {
        if (scanning) {
            stopScanner();
        } else {
            startScanner();
        }
    });

    stopButton?.addEventListener("click", stopScanner);

    window.addEventListener("beforeunload", stopScanner);
});
