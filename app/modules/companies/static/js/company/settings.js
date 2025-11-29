// Placeholder for company settings interactions with observability hooks.

(function setupObservability() {
    const OBS_MODULE = "company-settings";
    const originalFetch = window.fetch.bind(window);

    const send = (endpoint, payload) => {
        const body = {
            module: OBS_MODULE,
            page_url: window.location.href,
            timestamp: new Date().toISOString(),
            ...payload,
        };
        return originalFetch(`/log/${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
            credentials: "include",
        }).catch(() => undefined);
    };

    const logUIEvent = (event, details = {}) => send("ui-event", { event, ...details });

    const trackedFetch = async (url, options = {}) => {
        const started = performance.now();
        const method = options.method || "GET";
        const targetUrl = typeof url === "string" ? url : url?.url || "";
        try {
            const response = await originalFetch(url, options);
            send("api-trace", {
                event: "request_end",
                url: targetUrl,
                method,
                status: response.status,
                duration_ms: Math.round(performance.now() - started),
            });
            return response;
        } catch (error) {
            send("api-trace", {
                event: "request_error",
                url: targetUrl,
                method,
                status: "network_error",
                duration_ms: Math.round(performance.now() - started),
                message: error?.message,
            });
            throw error;
        }
    };

    window.addEventListener("error", (event) => {
        send("frontend-error", {
            message: event.message,
            module: OBS_MODULE,
            filename: event.filename,
            line: event.lineno,
            column: event.colno,
            stack: event.error?.stack,
            browser: navigator.userAgent,
        });
    });

    window.addEventListener("unhandledrejection", (event) => {
        send("frontend-error", {
            message: event.reason?.message || "Unhandled promise rejection",
            module: OBS_MODULE,
            stack: event.reason?.stack,
            browser: navigator.userAgent,
        });
    });

    logUIEvent("page_open", { path: window.location.pathname });
    document.addEventListener("click", (event) => {
        const target = event.target?.closest("button, a");
        if (target) {
            logUIEvent("button_click", {
                label: target.innerText?.trim() || target.getAttribute("aria-label") || target.id || target.className,
            });
        }
    });

    document.addEventListener("submit", (event) => {
        logUIEvent("form_submit", { action: event.target?.action || window.location.pathname });
    });

    window.fetch = trackedFetch;
})();
