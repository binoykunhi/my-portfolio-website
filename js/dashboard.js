// Dashboard Logic

// Dashboard Logic

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Icons
    lucide.createIcons();

    // User Menu & Dropdown Logic
    const userMenuContainer = document.getElementById('user-menu-container');
    const userDropdown = document.getElementById('user-dropdown');

    if (userMenuContainer && userDropdown) {
        userMenuContainer.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('active');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!userMenuContainer.contains(e.target)) {
                userDropdown.classList.remove('active');
            }
        });
    }

    // Modal Logic
    const profileAction = document.getElementById('nav-profile-action');
    const profileModal = document.getElementById('profile-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');

    if (profileAction && profileModal) {
        profileAction.addEventListener('click', (e) => {
            e.stopPropagation();
            profileModal.classList.add('active');
            userDropdown.classList.remove('active');
        });

        if (modalCloseBtn) {
            modalCloseBtn.addEventListener('click', () => {
                profileModal.classList.remove('active');
            });
        }

        profileModal.addEventListener('click', (e) => {
            if (e.target === profileModal) {
                profileModal.classList.remove('active');
            }
        });
    }

    // Logout Logic
    const logoutBtn = document.getElementById('nav-logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            if (window.authService) {
                window.authService.signOut();
            }
        });
    }
});
