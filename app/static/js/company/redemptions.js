/* Redemption verification workflow supporting manual input and QR scanning. */

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("redemption-verify-form");
    const codeInput = document.getElementById("redemption-code");
    const resultContainer = document.getElementById("redemption-result");
    const toastContainer = document.getElementById("redemption-toast-container");
    const scanButton = document.getElementById("redemption-scan-btn");
    const scannerWrapper = document.getElementById("qr-scanner");
    const videoElement = document.getElementById("qr-video");
    const stopButton = document.getElementById("qr-stop-btn");

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

    const renderResult = (status, message, redemptionId = null) => {
        lastRedemptionId = redemptionId;
        const isSuccess = status === "pending" || status === "redeemed";
        const badgeClass = status === "redeemed" ? "bg-success" : status === "pending" ? "bg-warning" : "bg-secondary";
        const confirmButton = status === "pending" && redemptionId
            ? `<button class="btn btn-success mt-3" id="redemption-confirm-btn">Confirm redemption</button>`
            : "";
        resultContainer.innerHTML = `
            <div class="alert ${isSuccess ? "alert-success" : "alert-danger"}" role="alert">
                <div class="d-flex justify-content-between align-items-center">
                    <span>${message}</span>
                    <span class="badge ${badgeClass} text-uppercase">${status || "unknown"}</span>
                </div>
                ${confirmButton}
            </div>`;
        if (confirmButton) {
            document.getElementById("redemption-confirm-btn").addEventListener("click", confirmRedemption);
        }
    };

    const verifyCode = async (code) => {
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
        } catch (error) {
            renderResult("error", error.message);
            showToast(error.message, "danger");
        }
    };

    const confirmRedemption = async () => {
        if (!lastRedemptionId && !codeInput.value) return;
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
        } catch (error) {
            showToast(error.message, "danger");
        }
    };

    form?.addEventListener("submit", (event) => {
        event.preventDefault();
        const code = codeInput.value.trim();
        if (!code) return;
        verifyCode(code);
    });

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
