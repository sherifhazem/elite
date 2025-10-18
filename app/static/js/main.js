// Main JavaScript file for the ELITE member portal experience.
(function () {
    "use strict";

    /**
     * Update the tooltip for each membership badge for accessibility.
     */
    const badgeElements = document.querySelectorAll(".portal-badge");
    badgeElements.forEach((badge) => {
        badge.setAttribute("title", badge.textContent.trim() + " member tier");
    });

    /**
     * Display a contextual alert message for the upgrade workflow.
     * @param {string} message
     * @param {"success"|"danger"|"warning"} [variant]
     */
    function showUpgradeFeedback(message, variant = "success") {
        const feedbackElement = document.getElementById("upgrade-feedback");
        if (!feedbackElement) {
            alert(message); // Fallback when the alert placeholder is not present.
            return;
        }

        feedbackElement.classList.remove("d-none", "alert-success", "alert-danger", "alert-warning");
        feedbackElement.classList.add(`alert-${variant}`);
        feedbackElement.textContent = message;
    }

    /**
     * Refresh the on-page membership badge and tier border after a successful upgrade.
     * @param {string} newLevel
     */
    function refreshMembershipUI(newLevel) {
        const normalizedLevel = newLevel.toLowerCase();
        const badge = document.querySelector(".portal-badge");
        if (badge) {
            badge.textContent = newLevel;
            badge.className = `badge portal-badge portal-badge-${normalizedLevel}`;
            badge.setAttribute("title", `${newLevel} member tier`);
        }

        const tierCard = document.querySelector(".portal-tier-card");
        if (tierCard) {
            ["portal-tier-basic", "portal-tier-silver", "portal-tier-gold", "portal-tier-premium"].forEach((cls) => {
                tierCard.classList.remove(cls);
            });
            tierCard.classList.add(`portal-tier-${normalizedLevel}`);
        }
    }

    /**
     * Handle the membership upgrade form submission and call the backend endpoint.
     * @param {SubmitEvent} event
     */
    async function upgradeMembership(event) {
        event.preventDefault();

        const form = event.target;
        const select = form.querySelector("select[name='new_level']");
        if (!select || !select.value) {
            showUpgradeFeedback("Please choose a membership level to upgrade.", "warning");
            return;
        }

        const requestBody = { new_level: select.value };

        try {
            const response = await fetch("/portal/upgrade", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "include",
                body: JSON.stringify(requestBody),
            });

            const payload = await response.json().catch(() => ({ error: "Unexpected response" }));

            if (!response.ok) {
                const message = payload.error || payload.message || response.statusText;
                const variant = response.status === 401 ? "warning" : "danger";
                showUpgradeFeedback(message, variant);
                return;
            }

            showUpgradeFeedback(payload.message || "Membership upgraded successfully.");
            refreshMembershipUI(payload.new_level || select.value);

            if (payload.redirect_url) {
                setTimeout(() => {
                    window.location.href = payload.redirect_url;
                }, 1500);
            }
        } catch (error) {
            showUpgradeFeedback("Unable to process the upgrade right now. Please try again.", "danger");
            console.error("Membership upgrade failed", error);
        }
    }

    /**
     * Bind the upgrade form when it is available on the page.
     */
    function initializeUpgradeForm() {
        const form = document.getElementById("membership-upgrade-form");
        if (!form) {
            return;
        }
        if (form.hasAttribute("data-upgrade-inline")) {
            // Inline handler already invokes the upgrade routine; avoid double submission.
            return;
        }
        form.addEventListener("submit", upgradeMembership);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeUpgradeForm);
    } else {
        initializeUpgradeForm();
    }

    // Expose the handler for progressive enhancement scenarios where inline handlers are used.
    window.upgradeMembership = upgradeMembership;
})();
