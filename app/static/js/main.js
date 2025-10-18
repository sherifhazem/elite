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

    /**
     * Update the notification badge count displayed in the navigation bar.
     * @param {number} count
     */
    function setNotificationBadge(count) {
        const badge = document.getElementById("notification-count");
        if (!badge) {
            return;
        }
        const normalized = Math.max(0, Number.isFinite(count) ? count : 0);
        badge.dataset.count = String(normalized);
        badge.textContent = String(normalized);
        if (normalized > 0) {
            badge.removeAttribute("hidden");
        } else {
            badge.setAttribute("hidden", "hidden");
        }
    }

    /**
     * Decrement the unread notification badge by the provided delta.
     * @param {number} delta
     */
    function decrementNotificationBadge(delta) {
        const badge = document.getElementById("notification-count");
        if (!badge) {
            return;
        }
        const current = Number.parseInt(badge.dataset.count || "0", 10) || 0;
        setNotificationBadge(Math.max(0, current - Math.max(delta, 0)));
    }

    /**
     * Refresh UI elements for a single notification row after it is read.
     * @param {HTMLElement} row
     */
    function applyReadStateToRow(row) {
        row.dataset.isRead = "true";
        row.classList.remove("table-warning");
        const statusBadge = row.querySelector('[data-role="notification-status"]');
        if (statusBadge) {
            statusBadge.textContent = "Read";
            statusBadge.classList.remove("bg-warning", "text-dark");
            statusBadge.classList.add("bg-success");
        }
        const markButton = row.querySelector('[data-action="mark-read"]');
        if (markButton) {
            markButton.disabled = true;
        }
    }

    /**
     * Mark a notification as read via the API and update the interface.
     * @param {number} notificationId
     */
    async function markNotificationRead(notificationId) {
        const row = document.querySelector(
            `[data-notification-id="${notificationId}"]`
        );
        if (!row || row.dataset.isRead === "true") {
            return;
        }

        try {
            const response = await fetch(`/api/notifications/${notificationId}/read`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "include",
            });

            if (!response.ok) {
                console.warn("Unable to mark notification as read.");
                return;
            }

            applyReadStateToRow(row);
            decrementNotificationBadge(1);

            const center = document.getElementById("notification-center");
            if (center) {
                const current = Number.parseInt(center.dataset.unreadCount || "0", 10) || 0;
                const next = Math.max(0, current - 1);
                center.dataset.unreadCount = String(next);
                if (next === 0) {
                    const markAllButton = document.getElementById("mark-all-read");
                    if (markAllButton) {
                        markAllButton.disabled = true;
                    }
                }
            }
        } catch (error) {
            console.error("Failed to update notification state", error);
        }
    }

    /**
     * Mark all notifications as read and refresh the on-page indicators.
     */
    async function markAllNotificationsRead() {
        try {
            const response = await fetch("/api/notifications/read-all", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "include",
            });

            if (!response.ok) {
                console.warn("Unable to mark all notifications as read.");
                return;
            }

            document
                .querySelectorAll('[data-notification-id]')
                .forEach((row) => applyReadStateToRow(row));

            const center = document.getElementById("notification-center");
            if (center) {
                center.dataset.unreadCount = "0";
            }
            setNotificationBadge(0);
            const markAllButton = document.getElementById("mark-all-read");
            if (markAllButton) {
                markAllButton.disabled = true;
            }
        } catch (error) {
            console.error("Failed to mark notifications as read", error);
        }
    }

    // Expose handlers globally for inline attributes used in templates.
    window.upgradeMembership = upgradeMembership;
    window.markNotificationRead = markNotificationRead;
    window.markAllNotificationsRead = markAllNotificationsRead;
})();
