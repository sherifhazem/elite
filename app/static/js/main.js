// Mobile-first interactions for the ELITE portal experience.
(function () {
    "use strict";

    // Cache DOM references used across interactions.
    const shell = document.getElementById("app-shell");
    const headerTitle = document.getElementById("portal-page-title");
    const viewContainer = document.getElementById("portal-view");
    const toastStack = document.getElementById("toast-container");
    const loadingOverlay = document.getElementById("loading-indicator");
    const pullIndicator = document.getElementById("pull-to-refresh");
    const modal = document.getElementById("portal-modal");
    const modalBody = document.getElementById("modal-body");
    const modalTitle = document.getElementById("modal-title");

    let isNavigating = false;
    let pullStartY = null;
    let isPulling = false;

    /** Show the full-screen spinner while asynchronous work occurs. */
    function showSpinner() {
        if (loadingOverlay) {
            loadingOverlay.removeAttribute("hidden");
        }
    }

    /** Hide the full-screen spinner. */
    function hideSpinner() {
        if (loadingOverlay) {
            loadingOverlay.setAttribute("hidden", "hidden");
        }
    }

    /** Display a toast message near the top of the viewport. */
    function showToast(message, variant = "success", timeout = 2600) {
        if (!toastStack) {
            alert(message);
            return;
        }
        const toast = document.createElement("div");
        toast.className = `toast-message toast-message--${variant}`;
        toast.textContent = message;
        toastStack.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, timeout);
    }

    /** Update the bottom navigation active state. */
    function activateNav(target) {
        if (!shell) {
            return;
        }
        shell.dataset.activeNav = target || "";
        document.querySelectorAll("[data-nav-link]").forEach((link) => {
            if (link instanceof HTMLAnchorElement || link instanceof HTMLButtonElement) {
                const navTarget = link.dataset.navTarget || link.dataset.route || "";
                if (link.classList.contains("app-nav__item")) {
                    if (navTarget === target) {
                        link.classList.add("app-nav__item--active");
                    } else {
                        link.classList.remove("app-nav__item--active");
                    }
                }
            }
        });
    }

    /** Update the numeric badge inside the notifications tab. */
    function setNotificationBadge(count) {
        const badge = document.getElementById("notification-count");
        if (!badge) {
            return;
        }
        const normalized = Math.max(0, Number.parseInt(count, 10) || 0);
        badge.dataset.count = String(normalized);
        badge.textContent = String(normalized);
    }

    /** Replace the current view contents with markup from a fetched document. */
    function swapViewContent(sourceDocument, navTarget) {
        const nextView = sourceDocument.getElementById("portal-view");
        if (!nextView || !viewContainer) {
            return false;
        }
        viewContainer.innerHTML = nextView.innerHTML;
        viewContainer.dataset.currentView = nextView.dataset.currentView || navTarget || "";

        const nextHeader = sourceDocument.getElementById("portal-page-title");
        if (nextHeader && headerTitle) {
            headerTitle.textContent = nextHeader.textContent.trim();
        }

        const nextShell = sourceDocument.getElementById("app-shell");
        const nextNav = (nextShell && nextShell.dataset.activeNav) || navTarget || "";
        activateNav(nextNav);

        const newBadge = sourceDocument.getElementById("notification-count");
        if (newBadge) {
            setNotificationBadge(newBadge.dataset.count || newBadge.textContent || "0");
        }

        const sourceTitle = sourceDocument.querySelector("title");
        if (sourceTitle) {
            document.title = sourceTitle.textContent.trim();
        }

        return true;
    }

    /** Fetch a page and transition without reloading the full window. */
    async function fetchAndRender(url, navTarget = "", pushHistory = true) {
        if (isNavigating) {
            return;
        }
        isNavigating = true;
        showSpinner();
        try {
            const response = await fetch(url, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                credentials: "include",
            });
            if (!response.ok) {
                throw new Error(`Navigation failed with status ${response.status}`);
            }
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");
            if (!swapViewContent(doc, navTarget)) {
                window.location.assign(url);
                return;
            }
            if (pushHistory) {
                history.pushState({ url, navTarget }, "", url);
            }
            initializeView();
        } catch (error) {
            console.error("Navigation error", error);
            window.location.assign(url);
        } finally {
            hideSpinner();
            isNavigating = false;
        }
    }

    /** Refresh the currently active view in place. */
    function refreshCurrentView(showIndicator = true) {
        const target = (viewContainer && viewContainer.dataset.currentView) || "";
        const url = window.location.pathname + window.location.search;
        if (showIndicator) {
            showSpinner();
        }
        fetchAndRender(url, target, false);
    }

    /** Handle navigation taps on the bottom bar or inline links. */
    function handleNavTap(event) {
        const target = event.target.closest("[data-nav-link]");
        if (!target) {
            return;
        }
        const href = target.getAttribute("href") || target.dataset.route;
        if (!href || event.metaKey || event.ctrlKey) {
            return;
        }
        event.preventDefault();
        const navTarget = target.dataset.navTarget || "";
        fetchAndRender(href, navTarget, true);
    }

    /** Populate the featured carousel with live offers when available. */
    async function hydrateFeaturedCarousel() {
        const track = viewContainer.querySelector("[data-featured-track]");
        if (!track || track.dataset.hydrated === "true") {
            return;
        }
        try {
            const response = await fetch("/api/offers/", { credentials: "include" });
            if (!response.ok) {
                throw new Error("Unable to fetch offers");
            }
            const offers = await response.json();
            if (!Array.isArray(offers) || offers.length === 0) {
                return;
            }
            track.dataset.hydrated = "true";
            track.innerHTML = "";
            const membershipLevel = track.dataset.membershipLevel || "Basic";
            offers.slice(0, 6).forEach((offer) => {
                const chip = document.createElement("article");
                chip.className = "offer-chip";
                chip.dataset.offerId = offer.id;
                chip.dataset.offerTitle = offer.title;
                chip.dataset.offerCompany = offer.company_id ? `شريك رقم ${offer.company_id}` : "شريك ELITE";
                chip.dataset.offerDiscount = Math.round(offer.discount_percent || offer.base_discount || 0);
                chip.dataset.offerLevel = membershipLevel;
                chip.dataset.offerValid = offer.valid_until ? offer.valid_until.split("T")[0] : "مستمر";
                chip.innerHTML = `
                    <div class="offer-chip__level">${membershipLevel}</div>
                    <h3 class="offer-chip__title">${offer.title}</h3>
                    <p class="offer-chip__company">${chip.dataset.offerCompany}</p>
                    <span class="offer-chip__discount">${chip.dataset.offerDiscount}%</span>
                `;
                chip.addEventListener("click", () => openOfferModal(chip));
                track.appendChild(chip);
            });
        } catch (error) {
            console.error("Failed to hydrate featured carousel", error);
        }
    }

    /** Open the shared modal with details derived from the dataset. */
    function openOfferModal(source) {
        if (!modal || !modalBody || !modalTitle || !source) {
            return;
        }
        modalTitle.textContent = source.dataset.offerTitle || "Offer";
        const level = source.dataset.offerLevel || "Basic";
        const discount = source.dataset.offerDiscount || "0";
        const company = source.dataset.offerCompany || "ELITE Partner";
        const valid = source.dataset.offerValid || "مستمر";
        modalBody.innerHTML = `
            <p><strong>الشركة:</strong> ${company}</p>
            <p><strong>مستوى العضوية:</strong> ${level}</p>
            <p><strong>نسبة الخصم:</strong> ${discount}%</p>
            <p><strong>صالح حتى:</strong> ${valid}</p>
            <p>للاستفادة من العرض، قم بعرض بطاقة عضويتك لممثل الشركة.</p>
        `;
        modal.removeAttribute("hidden");
        document.body.style.overflow = "hidden";
    }

    /** Close the shared modal. */
    function closeModal() {
        if (!modal) {
            return;
        }
        modal.setAttribute("hidden", "hidden");
        document.body.style.overflow = "";
    }

    /** Wire offer cards inside the offers view. */
    function bindOfferCards() {
        viewContainer.querySelectorAll(".offer-card").forEach((card) => {
            card.addEventListener("click", () => openOfferModal(card));
            card.addEventListener("keydown", (event) => {
                if (event.key === "Enter") {
                    openOfferModal(card);
                }
            });
        });
        viewContainer.querySelectorAll("[data-offer-action]").forEach((button) => {
            button.addEventListener("click", (event) => {
                event.stopPropagation();
                const card = button.closest(".offer-card") || button.closest(".offer-chip");
                openOfferModal(card);
            });
        });
        viewContainer.querySelectorAll(".offer-chip").forEach((chip) => {
            chip.addEventListener("click", () => openOfferModal(chip));
        });
    }

    /** Bind handlers for modal dismissal. */
    function bindModalEvents() {
        if (!modal) {
            return;
        }
        modal.querySelectorAll("[data-modal-dismiss]").forEach((element) => {
            element.addEventListener("click", closeModal);
        });
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && !modal.hasAttribute("hidden")) {
                closeModal();
            }
        });
    }

    /** Enable pull-to-refresh interactions on the scroll container. */
    function bindPullToRefresh() {
        if (!viewContainer || !pullIndicator) {
            return;
        }
        const scrollContainer = document.getElementById("portal-main");
        if (!scrollContainer) {
            return;
        }
        scrollContainer.addEventListener("touchstart", (event) => {
            if (scrollContainer.scrollTop <= 0) {
                pullStartY = event.touches[0].clientY;
                isPulling = true;
            }
        });
        scrollContainer.addEventListener("touchmove", (event) => {
            if (!isPulling || pullStartY === null) {
                return;
            }
            const currentY = event.touches[0].clientY;
            const delta = currentY - pullStartY;
            if (delta > 20) {
                pullIndicator.removeAttribute("hidden");
                pullIndicator.style.transform = `translateY(${Math.min(delta - 20, 80)}px)`;
                if (delta > 80) {
                    pullIndicator.classList.add("is-ready");
                } else {
                    pullIndicator.classList.remove("is-ready");
                }
            }
        });
        const finishPull = () => {
            if (!isPulling) {
                return;
            }
            if (pullIndicator.classList.contains("is-ready")) {
                pullIndicator.classList.remove("is-ready");
                showToast("Refreshing", "success", 1600);
                refreshCurrentView(false);
            }
            pullIndicator.setAttribute("hidden", "hidden");
            pullIndicator.style.transform = "translateY(0)";
            pullStartY = null;
            isPulling = false;
        };
        scrollContainer.addEventListener("touchend", finishPull);
        scrollContainer.addEventListener("touchcancel", finishPull);
    }

    /** Trigger smooth scrolling to the upgrade panel when requested. */
    function bindProfileActions() {
        const entry = viewContainer.querySelector("#upgrade-entry");
        const panel = viewContainer.querySelector("#upgrade-panel");
        if (entry && panel) {
            entry.addEventListener("click", () => {
                panel.scrollIntoView({ behavior: "smooth" });
            });
        }
        const downloadButton = viewContainer.querySelector("#download-card");
        if (downloadButton) {
            downloadButton.addEventListener("click", downloadMembershipCard);
        }
    }

    /** Render a downloadable membership card image on demand. */
    async function downloadMembershipCard() {
        const card = document.getElementById("membership-card");
        if (!card) {
            return;
        }
        const name = card.dataset.memberName || "ELITE Member";
        const level = card.dataset.memberLevel || "Basic";
        const code = card.dataset.memberCode || "000000";
        const joined = card.dataset.memberJoined || "—";

        const canvas = document.createElement("canvas");
        canvas.width = 960;
        canvas.height = 540;
        const ctx = canvas.getContext("2d");
        if (!ctx) {
            showToast("Unable to export card right now.", "error");
            return;
        }

        // Draw gradient background matching the visual card.
        const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
        gradient.addColorStop(0, "#0b1f3a");
        gradient.addColorStop(1, "#7c3aed");
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 48px Poppins";
        ctx.fillText("ELITE MEMBERSHIP", 60, 100);

        ctx.font = "600 28px Inter";
        ctx.fillText(`Level: ${level}`, 60, 180);
        ctx.fillText(`Member: ${name}`, 60, 240);
        ctx.fillText(`ID: ${code}`, 60, 300);
        ctx.fillText(`Joined: ${joined}`, 60, 360);

        const stampGradient = ctx.createLinearGradient(60, 380, 360, 480);
        stampGradient.addColorStop(0, "rgba(242, 193, 78, 0.9)");
        stampGradient.addColorStop(1, "rgba(124, 58, 237, 0.9)");
        ctx.fillStyle = stampGradient;
        drawRoundedRectangle(ctx, 60, 380, 280, 90, 28);
        ctx.fillStyle = "#0f172a";
        ctx.font = "600 26px Inter";
        ctx.fillText("Elite Discount Program", 80, 435);

        const link = document.createElement("a");
        link.href = canvas.toDataURL("image/png");
        link.download = "elite-membership-card.png";
        link.click();
        showToast("Membership card downloaded.");
    }

    /** Draw a rounded rectangle compatible with older browsers. */
    function drawRoundedRectangle(ctx, x, y, width, height, radius) {
        if (typeof ctx.roundRect === "function") {
            ctx.beginPath();
            ctx.roundRect(x, y, width, height, radius);
            ctx.fill();
            return;
        }
        const r = Math.min(radius, width / 2, height / 2);
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + width - r, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + r);
        ctx.lineTo(x + width, y + height - r);
        ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
        ctx.lineTo(x + r, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - r);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.closePath();
        ctx.fill();
    }

    /** Handle membership upgrade submissions via API. */
    async function upgradeMembership(event) {
        event.preventDefault();
        const form = event.target;
        const select = form.querySelector("select[name='new_level']");
        if (!select || !select.value) {
            showToast("يرجى اختيار مستوى للترقية.", "error");
            return;
        }
        showSpinner();
        try {
            const response = await fetch("/portal/upgrade", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "include",
                body: JSON.stringify({ new_level: select.value }),
            });
            const payload = await response.json().catch(() => ({ error: "Unexpected response" }));
            if (!response.ok) {
                showToast(payload.error || payload.message || "تعذر إتمام الترقية.", "error", 3200);
                return;
            }
            showToast(payload.message || "تمت ترقية العضوية بنجاح.");
            if (payload.new_level) {
                refreshCurrentView(false);
            }
        } catch (error) {
            console.error("Upgrade failed", error);
            showToast("حدث خطأ غير متوقع.", "error");
        } finally {
            hideSpinner();
        }
    }

    /** Apply read state styles for notification items. */
    function markNotificationAsReadLocally(element) {
        if (!element) {
            return;
        }
        element.dataset.isRead = "true";
        element.classList.remove("notification-thread__item--unread");
        const status = element.querySelector("[data-role='notification-status']");
        if (status) {
            status.textContent = "Read";
        }
        const button = element.querySelector("[data-action='mark-read']");
        if (button) {
            button.disabled = true;
        }
    }

    /** Reduce the global notification badge count by a delta. */
    function decrementNotificationBadge(delta) {
        const badge = document.getElementById("notification-count");
        const current = badge ? Number.parseInt(badge.dataset.count || "0", 10) || 0 : 0;
        setNotificationBadge(Math.max(0, current - Math.max(delta, 0)));
    }

    /** Mark a single notification as read using the API. */
    async function markNotificationRead(notificationId) {
        const row = document.querySelector(`[data-notification-id='${notificationId}']`);
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
                throw new Error("Failed to update notification");
            }
            markNotificationAsReadLocally(row);
            decrementNotificationBadge(1);
            showToast("تم تحديث الإشعار.", "success", 1800);
        } catch (error) {
            console.error("Notification update failed", error);
            showToast("تعذر تحديث حالة الإشعار.", "error");
        }
    }

    /** Mark all notifications as read. */
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
                throw new Error("Failed to mark all as read");
            }
            document.querySelectorAll("[data-notification-id]").forEach((row) => {
                markNotificationAsReadLocally(row);
            });
            setNotificationBadge(0);
            const center = document.getElementById("notification-center");
            if (center) {
                center.dataset.unreadCount = "0";
            }
            const button = document.getElementById("mark-all-read");
            if (button) {
                button.disabled = true;
            }
            showToast("تمت قراءة جميع الإشعارات.");
        } catch (error) {
            console.error("Bulk notification update failed", error);
            showToast("تعذر إكمال العملية.", "error");
        }
    }

    /** Bind event listeners for notification buttons. */
    function bindNotificationActions() {
        viewContainer.querySelectorAll("[data-action='mark-read']").forEach((button) => {
            button.addEventListener("click", (event) => {
                event.preventDefault();
                const parent = button.closest("[data-notification-id]");
                if (!parent) {
                    return;
                }
                markNotificationRead(parent.dataset.notificationId);
            });
        });
    }

    /** Attach listeners for inline navigation links. */
    function bindInlineNavigation() {
        viewContainer.querySelectorAll("[data-nav-link]").forEach((link) => {
            link.addEventListener("click", handleNavTap);
        });
    }

    /** Initialise behaviours every time the view changes. */
    function initializeView() {
        bindInlineNavigation();
        bindOfferCards();
        bindProfileActions();
        bindNotificationActions();
        hydrateFeaturedCarousel();
    }

    /** Initial bindings when the script loads. */
    function boot() {
        document.addEventListener("click", handleNavTap);
        bindModalEvents();
        bindPullToRefresh();
        initializeView();
        window.addEventListener("popstate", (event) => {
            if (event.state && event.state.url) {
                fetchAndRender(event.state.url, event.state.navTarget || "", false);
            } else {
                refreshCurrentView(false);
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }

    // Expose API functions globally for inline template usage.
    window.upgradeMembership = upgradeMembership;
    window.markNotificationRead = markNotificationRead;
    window.markAllNotificationsRead = markAllNotificationsRead;
})();
