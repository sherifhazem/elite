// Controls the one-time splash screen visibility on auth pages.
document.addEventListener('DOMContentLoaded', () => {
    const splash = document.getElementById('splash-screen');
    if (!splash) return;

    const splashShown = sessionStorage.getItem('elite_splash_shown');
    if (splashShown) {
        splash.remove();
        return;
    }

    sessionStorage.setItem('elite_splash_shown', 'true');
    setTimeout(() => {
        splash.classList.add('fade-out');
        setTimeout(() => splash.remove(), 700);
    }, 1800);
});
