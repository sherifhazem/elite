// Main JavaScript file for the ELITE member portal experience.
(function () {
    "use strict";

    const badgeElements = document.querySelectorAll(".portal-badge");
    badgeElements.forEach((badge) => {
        badge.setAttribute("title", badge.textContent.trim() + " member tier");
    });
})();