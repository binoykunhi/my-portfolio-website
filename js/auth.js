// Auth Service handling Firebase Authentication

class AuthService {
    constructor() {
        this.auth = null;
        this.provider = null;
        this.user = null;
        this.init();
    }

    init() {
        // Check if Firebase is loaded
        if (!window.firebase) {
            console.error("Firebase SDK not loaded");
            alert("Firebase SDK not loaded. Please check your internet connection.");
            return;
        }

        // Initialize Firebase
        if (!firebase.apps.length) {
            firebase.initializeApp(window.firebaseConfig);
        }

        this.auth = firebase.auth();
        this.provider = new firebase.auth.GoogleAuthProvider();

        // Listen for auth state changes
        this.auth.onAuthStateChanged((user) => {
            this.user = user;
            this.handleAuthStateChange(user);
        });
    }

    async signInWithGoogle() {
        try {
            const result = await this.auth.signInWithPopup(this.provider);
            // The signed-in user info.
            this.user = result.user;
            return this.user;
        } catch (error) {
            console.error("Error signing in:", error);
            alert("Login Failed: " + error.message);
            throw error;
        }
    }

    async signOut() {
        try {
            await this.auth.signOut();
            this.user = null;
        } catch (error) {
            console.error("Error signing out:", error);
            throw error;
        }
    }

    handleAuthStateChange(user) {
        const currentPath = window.location.pathname;
        const isProtected = currentPath.includes('experiments.html') || currentPath.includes('profile.html') || currentPath.includes('dashboard.html');

        // UI Elements
        const loginBtn = document.getElementById('google-login-btn');
        const userMenu = document.getElementById('user-menu-container');
        const userAvatar = document.getElementById('nav-user-avatar');
        const userName = document.getElementById('nav-user-name');
        const experimentsLink = document.getElementById('nav-experiments');

        // Modal Elements (if present)
        const modalAvatar = document.getElementById('modal-avatar');
        const modalName = document.getElementById('modal-name');
        const modalEmail = document.getElementById('modal-email');

        if (user) {
            // User is signed in
            console.log("User is signed in:", user.displayName);

            // Update Nav UI
            if (loginBtn) loginBtn.style.display = 'none';
            if (userMenu) {
                userMenu.style.display = 'flex';
                if (userAvatar) userAvatar.src = user.photoURL || `https://ui-avatars.com/api/?name=${user.displayName}`;
                if (userName) userName.textContent = user.displayName;
            }
            if (experimentsLink) experimentsLink.style.display = 'block';

            // Update Modal Data
            if (modalAvatar) modalAvatar.src = user.photoURL || `https://ui-avatars.com/api/?name=${user.displayName}`;
            if (modalName) modalName.textContent = user.displayName;
            if (modalEmail) modalEmail.textContent = user.email;

            // If on a protected page, stay there.
            // No automatic redirection from index.

        } else {
            // User is signed out
            console.log("User is signed out");

            // Update Nav UI
            if (loginBtn) loginBtn.style.display = 'flex';
            if (userMenu) userMenu.style.display = 'none';
            if (experimentsLink) experimentsLink.style.display = 'none';

            // Redirect to home if on protected page
            if (isProtected) {
                window.location.href = 'index.html';
            }
        }
    }
}

// Initialize Auth Service
window.authService = new AuthService();
