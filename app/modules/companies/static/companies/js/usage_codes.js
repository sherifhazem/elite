document.addEventListener("DOMContentLoaded", () => {
    const generateButton = document.querySelector("[data-generate-usage-code]");
    const codeValue = document.querySelector("[data-usage-code-value]");
    const expiresValue = document.querySelector("[data-usage-code-expires]");
    const usageValue = document.querySelector("[data-usage-code-usage]");

    if (!codeValue) {
        return;
    }

    const formatDateTime = (isoString) => {
        if (!isoString) {
            return "مفتوحة";
        }
        const date = new Date(isoString);
        if (Number.isNaN(date.getTime())) {
            return "مفتوحة";
        }
        return date.toLocaleString();
    };

    const updateUsageCode = (payload) => {
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
    };

    const fetchCurrentCode = async () => {
        try {
            const response = await fetch("/company/usage-codes/current", {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "include",
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(payload.error || "Unable to generate code.");
            }

            updateUsageCode(payload);
        } catch (error) {
            console.error("Usage code generation failed", error);
            if (generateButton) {
                generateButton.disabled = false;
            }
        }
    };

    if (generateButton) {
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

                updateUsageCode(payload);
            } catch (error) {
                console.error("Usage code generation failed", error);
                alert(error.message || "Unable to generate usage code.");
            } finally {
                generateButton.disabled = false;
            }
        });
    }

    fetchCurrentCode();
    window.setInterval(fetchCurrentCode, 10000);
});
