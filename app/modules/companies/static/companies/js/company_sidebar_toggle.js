// Toggles company sidebar visibility on smaller viewports.
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('companySidebar');
    if (!sidebar) {
        return;
    }

    const toggles = document.querySelectorAll('[data-bs-target="#companySidebar"]');
    toggles.forEach((toggle) => {
        toggle.addEventListener('click', () => {
            const isShown = sidebar.classList.contains('show');
            sidebar.classList.toggle('show');
            toggle.setAttribute('aria-expanded', String(!isShown));
        });
    });
});
