document.addEventListener("DOMContentLoaded", () => {
    const generateButton = document.querySelector("[data-generate-usage-code]");
    const codeValue = document.querySelector("[data-usage-code-value]");
    const expiresValue = document.querySelector("[data-usage-code-expires]");
    const usageValue = document.querySelector("[data-usage-code-usage]");

    if (!generateButton) {
        return;
    }

    const formatDateTime = (isoString) => {
        if (!isoString) {
            return "—";
        }
        const date = new Date(isoString);
        if (Number.isNaN(date.getTime())) {
            return "—";
        }
        return date.toLocaleString();
    };

    generateButton.addEventListener("click", async () => {
        generateButton.disabled = true;
        try {
            const response = await fetch("/company/usage-codes/generate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "include",
                body: JSON.stringify({}),
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(payload.error || "Unable to generate code.");
            }

            if (codeValue) {
                codeValue.textContent = payload.code || "—";
            }
            if (expiresValue) {
                expiresValue.textContent = formatDateTime(payload.expires_at);
            }
            if (usageValue) {
                const used = payload.usage_count ?? 0;
                const max = payload.max_uses_per_window ?? "—";
                usageValue.textContent = `${used} / ${max}`;
            }
        } catch (error) {
            console.error("Usage code generation failed", error);
            alert(error.message || "Unable to generate usage code.");
        } finally {
            generateButton.disabled = false;
        }
    });
});
