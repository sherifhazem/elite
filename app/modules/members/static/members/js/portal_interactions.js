// LINKED: Shared Offers & Redemptions Integration (no schema changes)
// Mobile-first interactions for the ELITE portal experience.
(function () {
    "use strict";

    // Cache DOM references used across interactions.
    const shell = document.getElementById("app-shell");
    const headerTitle = document.getElementById("portal-page-text");
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

    /** Format a datetime string in a localized human-readable way. */
    function formatDateTime(value) {
        if (!value) {
            return "—";
        }
        try {
            const date = value instanceof Date ? value : new Date(value);
            if (Number.isNaN(date.getTime())) {
                return typeof value === "string" ? value : "—";
            }
            return date.toLocaleString("ar-SA", { hour12: false });
        } catch (error) {
            console.error("Failed to format date", error);
            return typeof value === "string" ? value : "—";
        }
    }

    /** Copy text to the clipboard with graceful fallbacks. */
    async function copyToClipboard(text, successMessage = "تم نسخ الكود") {
        if (!text) {
            showToast("لا يوجد كود لنسخه.", "error");
            return;
        }
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(text);
            } else {
                const textarea = document.createElement("textarea");
                textarea.value = text;
                textarea.setAttribute("readonly", "readonly");
                textarea.style.position = "absolute";
                textarea.style.left = "-9999px";
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand("copy");
                textarea.remove();
            }
            showToast(successMessage, "success", 2400);
        } catch (error) {
            console.error("Clipboard copy failed", error);
            showToast("تعذر نسخ الكود.", "error");
        }
    }

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

        const nextHeader = sourceDocument.getElementById("portal-page-text");
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
            offers.slice(0, 6).forEach((offer) => {
                const card = document.createElement("article");
                card.className = "offer-card";
                card.dataset.offerId = offer.id;
                card.dataset.offerTitle = offer.title;
                card.dataset.offerCompany = offer.company || (offer.company_id ? `شريك رقم ${offer.company_id}` : "شريك ELITE");
                card.dataset.offerCompanyId = offer.company_id || "";
                card.dataset.offerCompanySummary = offer.company_summary || "";
                card.dataset.offerCompanyDescription = offer.company_description || "";
                card.dataset.offerDescription = offer.description || "";
                card.dataset.offerDiscount = Math.round(offer.discount_percent || offer.base_discount || 0);
                card.dataset.offerValid = offer.valid_until ? offer.valid_until.split("T")[0] : "مستمر";
                const industryIcon = offer.industry_icon || 'fix.png';

                // Match the structure of offer_card_macro.html
                card.innerHTML = `
                    <div class="offer-card__header">
                         <div class="offer-tags">
                            ${(offer.classification_values && offer.classification_values.length > 0) ? (function () {
                        const type = offer.classification_values[0];
                        const labels = {
                            'first_time_offer': 'اول مره',
                            'loyalty_offer': 'عرض الولاء',
                            'mid_week': 'منتصف الاسبوع',
                            'happy_hour': 'ساعة السعادة',
                            'active_members_only': 'للأعضاء النشطين'
                        };
                        return `<span class="offer-tag offer-tag--${type}">${labels[type] || type}</span>`;
                    })() : '<div></div>'}
                         </div>
                        <div class="offer-card__icon-frame">
                            <img src="/static/shared/icons/${industryIcon}" alt=""
                                class="offer-card__industry-icon" aria-hidden="true"
                                onerror="this.style.display='none'">
                        </div>
                    </div>

                    <h3 class="offer-card__title">${offer.title}</h3>
                    
                    <div class="offer-card__discount-wrapper">
                        <span class="offer-card__discount">${card.dataset.offerDiscount}%</span>
                        <span class="offer-card__discount-label">خصم</span>
                    </div>

                    <div class="offer-card__company-wrapper">
                         <div class="offer-card__company-logo-placeholder">
                            ${card.dataset.offerCompany.charAt(0)}
                        </div>
                        <p class="offer-card__company">${card.dataset.offerCompany}</p>
                    </div>
                `;
                card.addEventListener("click", () => openOfferModal(card));
                track.appendChild(card);
            });
        } catch (error) {
            console.error("Failed to hydrate featured carousel", error);
        }
    }

    /** Display a company information modal using cached data or live fetch. */
    async function openCompanyDetails(companyId, fallbackName, fallbackSummary, fallbackDescription) {
        if (!modal || !modalBody || !modalTitle) {
            return;
        }
        const name = fallbackName || "الشركة الشريكة";
        const summary = fallbackSummary || "";
        const description = fallbackDescription || "";
        modalTitle.textContent = name;
        modalBody.innerHTML = `
            <article class="company-modal">
                ${summary ? `<p class="text-muted">${summary}</p>` : ""}
                <p>${description || "لا تتوفر تفاصيل إضافية لهذه الشركة حالياً."}</p>
            </article>
        `;
        modal.removeAttribute("hidden");
        document.body.style.overflow = "hidden";
        if (!companyId) {
            return;
        }
        try {
            const response = await fetch(`/portal/companies/${companyId}`, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                credentials: "include",
            });
            if (!response.ok) {
                return;
            }
            const payload = await response.json();
            modalTitle.textContent = payload.name || name;
            const modalSummary = payload.summary || summary;
            const modalDescription = payload.description || description;
            modalBody.innerHTML = `
                <article class="company-modal">
                    ${modalSummary ? `<p class="text-muted">${modalSummary}</p>` : ""}
                    <p>${modalDescription || "لا تتوفر تفاصيل إضافية لهذه الشركة."}</p>
                </article>
            `;
        } catch (error) {
            console.error("Failed to load company details", error);
        }
    }

    /** Open the shared modal with details derived from the dataset. */
    function openOfferModal(source) {
        if (!modal || !modalBody || !modalTitle || !source) {
            return;
        }
        modalTitle.textContent = source.dataset.offerTitle || "Offer";
        const discount = source.dataset.offerDiscount || "0";
        const company = source.dataset.offerCompany || "ELITE Partner";
        const companyId = source.dataset.offerCompanyId || "";
        const summary = source.dataset.offerCompanySummary || "";
        const description = source.dataset.offerDescription || "";
        const valid = source.dataset.offerValid || "مستمر";
        modalBody.innerHTML = `
            <article class="offer-modal">
                <p><strong>الشركة:</strong> ${company}</p>
                <p><strong>نسبة الخصم:</strong> ${discount}%</p>
                <p><strong>صالح حتى:</strong> ${valid}</p>
                ${description ? `<p>${description}</p>` : ""}
                ${summary ? `<p class="text-muted">${summary}</p>` : ""}
                ${companyId
                ? `<button class="ghost-button" type="button" data-modal-company data-company-id="${companyId}" data-company-name="${company}" data-company-summary="${summary}" data-company-description="${source.dataset.offerCompanyDescription || ""}">عن الشركة</button>`
                : ""
            }
                <div class="usage-code-entry">
                    <h4>توثيق الاستخدام</h4>
                    <p class="text-muted">أدخل رمز الاستخدام الذي يقدمه الشريك لإتمام التحقق.</p>
                    <form class="usage-code-form" data-usage-code-form>
                        <label class="form-label" for="usage-code-input">رمز الاستخدام</label>
                        <div class="usage-code-input-group">
                            <input
                                class="form-control"
                                id="usage-code-input"
                                name="usage_code"
                                type="text"
                                inputmode="numeric"
                                maxlength="5"
                                autocomplete="one-time-code"
                                placeholder="أدخل الرمز"
                                data-usage-code-input
                            >
                            <button class="cta-button" type="submit">تحقق</button>
                        </div>
                    </form>
                </div>
            </article>
        `;
        const companyButton = modalBody.querySelector("[data-modal-company]");
        if (companyButton) {
            companyButton.addEventListener("click", () => {
                openCompanyDetails(
                    companyButton.dataset.companyId,
                    companyButton.dataset.companyName,
                    companyButton.dataset.companySummary,
                    companyButton.dataset.companyDescription
                );
            });
        }
        const usageForm = modalBody.querySelector("[data-usage-code-form]");
        const usageInput = modalBody.querySelector("[data-usage-code-input]");
        if (usageForm && usageInput) {
            usageForm.addEventListener("submit", async (event) => {
                event.preventDefault();
                const offerId = source.dataset.offerId;
                const code = usageInput.value.trim();
                if (!offerId) {
                    showToast("تعذر تحديد العرض المحدد.", "error");
                    return;
                }
                if (!code) {
                    showToast("يرجى إدخال رمز الاستخدام.", "error");
                    return;
                }
                const submitButton = usageForm.querySelector("button[type=\"submit\"]");
                if (submitButton) {
                    submitButton.disabled = true;
                }
                try {
                    const response = await fetch("/api/usage-codes/verify", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-Requested-With": "XMLHttpRequest",
                        },
                        credentials: "include",
                        body: JSON.stringify({
                            offer_id: Number.parseInt(offerId, 10) || offerId,
                            code,
                        }),
                    });
                    const payload = await response.json().catch(() => ({}));
                    if (!response.ok || payload.ok === false) {
                        throw new Error(
                            payload.message || payload.error || "تعذر التحقق من الرمز."
                        );
                    }
                    showToast("تم توثيق الاستخدام بنجاح.");
                    usageInput.value = "";
                } catch (error) {
                    console.error("Usage code verification failed", error);
                    showToast(error.message || "تعذر التحقق من الرمز.", "error");
                } finally {
                    if (submitButton) {
                        submitButton.disabled = false;
                    }
                }
            });
        }
        modal.removeAttribute("hidden");
        document.body.style.overflow = "hidden";
    }

    /** Present a redemption code modal with QR support. */
    function showRedemptionModal(payload) {
        if (!modal || !modalBody || !modalTitle) {
            return;
        }
        const status = (payload.status || "pending").toLowerCase();
        const statusMap = {
            pending: "قيد التفعيل",
            redeemed: "تم الاستخدام",
            expired: "منتهي",
        };
        const code = payload.code || payload.redemption_code || "";
        const qrUrl = payload.qr_url || payload.qrUrl || "";
        const expiresLabel = formatDateTime(payload.expires_at || payload.expiresAt);
        const redeemedLabel = formatDateTime(payload.redeemed_at || payload.redeemedAt);
        const offerTitle = payload.offer_title || payload.offerTitle || "تم إنشاء رمز التفعيل";

        modalTitle.textContent = offerTitle;
        modalBody.innerHTML = `
            <div class="redemption-modal">
                <p class="redemption-modal__status redemption-modal__status--${status}">
                    ${statusMap[status] || status}
                </p>
                <div class="redemption-modal__code-block">
                    <span class="redemption-modal__code-label">رمز التفعيل</span>
                    <span class="redemption-modal__code-value" data-modal-code="${code}">${code}</span>
                </div>
                <dl class="redemption-modal__details">
                    <div>
                        <dt>الصلاحية</dt>
                        <dd>${expiresLabel}</dd>
                    </div>
                    <div>
                        <dt>تاريخ الاستخدام</dt>
                        <dd>${redeemedLabel}</dd>
                    </div>
                </dl>
                ${qrUrl
                ? `<img class="redemption-modal__qr" src="${qrUrl}?t=${Date.now()}" alt="Offer QR Code" loading="lazy">`
                : ""
            }
                <div class="redemption-modal__actions">
                    <button class="cta-button" type="button" data-copy-code>Copy Code</button>
                    ${qrUrl
                ? `<button class="ghost-button" type="button" data-download-qr>Download QR</button>`
                : ""
            }
                    ${qrUrl
                ? `<a class="ghost-button" href="${qrUrl}" target="_blank" rel="noopener" data-open-qr>Open QR</a>`
                : ""
            }
                </div>
            </div>
        `;

        const copyButton = modalBody.querySelector("[data-copy-code]");
        if (copyButton) {
            copyButton.addEventListener("click", () => copyToClipboard(code));
        }
        const downloadButton = modalBody.querySelector("[data-download-qr]");
        if (downloadButton && qrUrl) {
            downloadButton.addEventListener("click", (event) => {
                event.preventDefault();
                downloadQrImage(qrUrl, code || "elite-redemption");
            });
        }

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

    function showRedemptionDetails(button) {
        if (!modal || !modalBody || !modalTitle) {
            return;
        }
        const card = button.closest(".activation-card");
        if (!card) {
            return;
        }
        const offerTitle = card.dataset.offerTitle || "تفاصيل العرض";
        const offerDescription = card.dataset.offerDescription || "لا تتوفر تفاصيل إضافية لهذا العرض.";
        const companyName = card.dataset.companyName || "شريك ELITE";
        const companySummary = card.dataset.companySummary || "";
        modalTitle.textContent = offerTitle;
        modalBody.innerHTML = `
            <article class="activation-details">
                <p><strong>الشركة:</strong> ${companyName}</p>
                <p>${offerDescription}</p>
                ${companySummary ? `<p class="text-muted">${companySummary}</p>` : ""}
                <div class="activation-details__actions">
                    <button class="ghost-button" type="button" data-company-details>عن الشركة</button>
                </div>
            </article>
        `;
        const companyButton = modalBody.querySelector("[data-company-details]");
        if (companyButton) {
            companyButton.addEventListener("click", () => openCompanyDetailsFromElement(card));
        }
        modal.removeAttribute("hidden");
        document.body.style.overflow = "hidden";
    }

    /** Wire offer cards inside the offers view. */
    function openCompanyDetailsFromElement(element) {
        if (!element) {
            return;
        }
        const host = element.closest(".offer-card") || element.closest(".activation-card");
        if (!host) {
            return;
        }
        const companyId = host.dataset.offerCompanyId || host.dataset.companyId || "";
        const companyName = host.dataset.offerCompany || host.dataset.companyName || element.dataset.companyName || "الشركة الشريكة";
        const companySummary = host.dataset.offerCompanySummary || host.dataset.companySummary || element.dataset.companySummary || "";
        const companyDescription = host.dataset.offerCompanyDescription || element.dataset.companyDescription || "";
        openCompanyDetails(companyId, companyName, companySummary, companyDescription);
    }

    async function submitOfferFeedback(button) {
        const card = button.closest(".offer-card");
        if (!card) {
            showToast("تعذر تحديد العرض المحدد.", "error");
            return;
        }
        const offerId = card.dataset.offerId;
        if (!offerId) {
            showToast("تعذر تحديد العرض المحدد.", "error");
            return;
        }
        const action = button.dataset.feedbackAction || "like";
        const note = button.dataset.feedbackNote || "";
        button.disabled = true;
        try {
            const response = await fetch(`/portal/offers/${offerId}/feedback`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "include",
                body: JSON.stringify({ action, note }),
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok || payload.ok === false) {
                throw new Error(payload.error || payload.message || "تعذر إرسال التفاعل.");
            }
            showToast("تم إرسال تفاعلك إلى الشركة.");
        } catch (error) {
            console.error("Feedback submission failed", error);
            showToast(error.message || "تعذر إرسال التفاعل.", "error");
        } finally {
            button.disabled = false;
        }
    }

    function bindOfferCards() {
        viewContainer.querySelectorAll(".offer-card").forEach((card) => {
            if (card.dataset.enhanced === "true") {
                return;
            }
            card.dataset.enhanced = "true";
            card.addEventListener("click", () => openOfferModal(card));
            card.addEventListener("keydown", (event) => {
                if (event.key === "Enter") {
                    openOfferModal(card);
                }
            });
        });
        viewContainer.querySelectorAll("[data-offer-action]").forEach((button) => {
            if (button.dataset.enhanced === "true") {
                return;
            }
            button.dataset.enhanced = "true";
            button.addEventListener("click", (event) => {
                event.stopPropagation();
                const card = button.closest(".offer-card");
                openOfferModal(card);
            });
        });

        viewContainer.querySelectorAll("[data-offer-company]").forEach((button) => {
            if (button.dataset.enhanced === "true") {
                return;
            }
            button.dataset.enhanced = "true";
            button.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                openCompanyDetailsFromElement(button);
            });
        });
        viewContainer.querySelectorAll("[data-offer-feedback]").forEach((button) => {
            if (button.dataset.enhanced === "true") {
                return;
            }
            button.dataset.enhanced = "true";
            button.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                submitOfferFeedback(button);
            });
        });
    }

    /** Bind actions for activating offers and managing redemption utilities. */
    function bindActivationButtons() {
        viewContainer.querySelectorAll("[data-offer-activate]").forEach((button) => {
            if (button.dataset.enhanced === "true") {
                return;
            }
            button.dataset.enhanced = "true";
            button.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                requestOfferActivation(button);
            });
        });

        viewContainer.querySelectorAll("[data-open-redemption]").forEach((button) => {
            if (button.dataset.enhanced === "true") {
                return;
            }
            button.dataset.enhanced = "true";
            button.addEventListener("click", async (event) => {
                event.preventDefault();
                const code = button.dataset.redemptionCode;
                if (!code) {
                    showToast("لا يمكن تحميل هذا التفعيل الآن.", "error");
                    return;
                }
                showSpinner();
                try {
                    const payload = await fetchRedemptionStatus(code);
                    showRedemptionModal(payload);
                } catch (error) {
                    console.error("Failed to load redemption", error);
                    showToast(error.message || "تعذر تحميل بيانات التفعيل.", "error");
                } finally {
                    hideSpinner();
                }
            });
        });

        viewContainer.querySelectorAll("[data-redemption-details]").forEach((button) => {
            if (button.dataset.enhanced === "true") {
                return;
            }
            button.dataset.enhanced = "true";
            button.addEventListener("click", (event) => {
                event.preventDefault();
                showRedemptionDetails(button);
            });
        });

        viewContainer.querySelectorAll("[data-copy-redemption]").forEach((button) => {
            if (button.dataset.enhanced === "true") {
                return;
            }
            button.dataset.enhanced = "true";
            button.addEventListener("click", (event) => {
                event.preventDefault();
                const code = button.dataset.redemptionCode;
                copyToClipboard(code);
            });
        });
    }

    /** Download the QR image by triggering a hidden anchor element. */
    function downloadQrImage(url, code) {
        if (!url) {
            showToast("لا يوجد رمز QR متاح.", "error");
            return;
        }
        const anchor = document.createElement("a");
        anchor.href = `${url}?t=${Date.now()}`;
        anchor.download = `${code || "elite-qr"}.png`;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        showToast("تم تحميل رمز QR.");
    }

    /** Call the redemption API to create a new activation. */
    async function requestOfferActivation(button) {
        const card = button.closest(".offer-card") || button.closest("[data-offer-id]");
        const offerId = (card && card.dataset.offerId) || button.dataset.offerId;
        if (!offerId) {
            showToast("تعذر تحديد العرض المحدد.", "error");
            return;
        }
        showSpinner();
        try {
            const response = await fetch("/api/redemptions/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "include",
                body: JSON.stringify({ offer_id: Number.parseInt(offerId, 10) || offerId }),
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) {
                showToast(payload.error || payload.message || "تعذر إنشاء كود التفعيل.", "error", 3600);
                return;
            }
            showRedemptionModal(payload);
            if (viewContainer && viewContainer.dataset.currentView === "profile") {
                refreshCurrentView(false);
            }
        } catch (error) {
            console.error("Activation request failed", error);
            showToast("حدث خطأ أثناء إنشاء الكود.", "error");
        } finally {
            hideSpinner();
        }
    }

    /** Fetch redemption status details for a given code. */
    async function fetchRedemptionStatus(code) {
        const response = await fetch(`/api/redemptions/${encodeURIComponent(code)}`, {
            headers: { "X-Requested-With": "XMLHttpRequest" },
            credentials: "include",
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            const message = error.error || error.message || "تعذر تحميل بيانات التفعيل.";
            throw new Error(message);
        }
        return response.json();
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

    function bindOffersFilter() {
        if (!viewContainer) {
            return;
        }
        const searchInput = viewContainer.querySelector("#offers-search-input");
        const filterTrigger = viewContainer.querySelector("[data-filter-trigger]");
        const cards = viewContainer.querySelectorAll(".offers-grid .offer-card");

        let selectedCategories = [];

        function applyFilters() {
            const query = searchInput ? searchInput.value.toLowerCase().trim() : "";

            cards.forEach((card) => {
                const title = (card.dataset.offerTitle || "").toLowerCase();
                const company = (card.dataset.companyName || "").toLowerCase();
                const cardCategory = card.dataset.category || "";

                const matchesSearch = !query || title.includes(query) || company.includes(query);
                const matchesCategory = selectedCategories.length === 0 || selectedCategories.includes(cardCategory);

                if (matchesSearch && matchesCategory) {
                    card.style.display = "";
                    card.style.animation = "fade-in 0.3s ease-out forwards";
                } else {
                    card.style.display = "none";
                }
            });

            // Handle empty state
            const grid = viewContainer.querySelector(".offers-grid");
            const emptyState = viewContainer.querySelector(".empty-state") || (function () {
                if (!grid) return null;
                const es = document.createElement("div");
                es.className = "empty-state";
                es.innerHTML = "<p>لا توجد نتائج تطابق بحثك.</p>";
                es.style.display = "none";
                grid.parentNode.insertBefore(es, grid.nextSibling);
                return es;
            })();

            const visibleCards = Array.from(cards).filter((c) => c.style.display !== "none");

            if (visibleCards.length === 0) {
                if (grid) grid.style.display = "none";
                if (emptyState) emptyState.style.display = "block";
            } else {
                if (grid) grid.style.display = "grid";
                if (emptyState) emptyState.style.display = "none";
            }
        }

        if (searchInput) {
            searchInput.addEventListener("input", applyFilters);
        }

        if (filterTrigger) {
            filterTrigger.addEventListener("click", () => {
                if (!modal || !modalBody || !modalTitle) return;

                const categories = JSON.parse(filterTrigger.dataset.categories || "[]");
                modalTitle.textContent = "تصفية العروض";

                let html = '<div class="filter-category-list">';
                categories.forEach(cat => {
                    const isChecked = selectedCategories.includes(cat);
                    html += `
                        <div class="filter-category-item" data-category-row>
                            <label for="cat-${cat}">${cat}</label>
                            <input type="checkbox" id="cat-${cat}" value="${cat}" ${isChecked ? 'checked' : ''} data-filter-checkbox>
                        </div>
                    `;
                });
                html += '</div>';
                html += `
                    <div class="filter-modal-actions">
                        <button class="cta-button" type="button" data-apply-filter>تم</button>
                    </div>
                `;

                modalBody.innerHTML = html;

                // Event delegation for row clicks
                modalBody.querySelectorAll("[data-category-row]").forEach(row => {
                    row.addEventListener("click", (e) => {
                        if (e.target.tagName !== 'INPUT') {
                            const cb = row.querySelector('input');
                            cb.checked = !cb.checked;
                        }
                    });
                });

                modalBody.querySelector("[data-apply-filter]").addEventListener("click", () => {
                    selectedCategories = Array.from(modalBody.querySelectorAll("[data-filter-checkbox]:checked"))
                        .map(cb => cb.value);
                    applyFilters();
                    closeModal();
                });

                modal.removeAttribute("hidden");
                document.body.style.overflow = "hidden";
            });
        }
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
        bindActivationButtons();
        bindProfileActions();
        bindNotificationActions();
        bindOffersFilter();
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
