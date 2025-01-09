document.addEventListener('DOMContentLoaded', () => {
    const installPrompt = document.getElementById('install-prompt');
    const installButton = document.getElementById('install-button');
    const closeButton = document.getElementById('install-prompt-close');

    // Check if the app is running as a standalone PWA or if the prompt has been shown
    if (navigator.standalone || window.matchMedia('(display-mode: standalone)').matches || sessionStorage.getItem('pwaInstallPromptShown')) {
        return;
    }

    // Show the install prompt
    installPrompt.style.display = 'block';
    sessionStorage.setItem('pwaInstallPromptShown', 'true');

    installButton.addEventListener('click', async () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            console.log(`User response to the install prompt: ${outcome}`);
            deferredPrompt = null;
            installPrompt.style.display = 'none';
        }
    });

    closeButton.addEventListener('click', () => {
        installPrompt.style.display = 'none';
    });

    // Close the prompt if the user clicks outside the banner
    window.addEventListener('click', (event) => {
        if (event.target === installPrompt) {
            installPrompt.style.display = 'none';
        }
    });
});

let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    // Stash the event so it can be triggered later.
    deferredPrompt = e;
    // Optionally, send analytics event that PWA is available
    console.log('PWA install prompt available');
});
