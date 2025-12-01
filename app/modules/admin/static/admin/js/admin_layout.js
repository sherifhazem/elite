// Bootstrap tooltip initialization for admin layout.
document.addEventListener('DOMContentLoaded', () => {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach((tooltipTriggerEl) => {
        if (typeof bootstrap !== 'undefined') {
            new bootstrap.Tooltip(tooltipTriggerEl);
        }
    });
});
