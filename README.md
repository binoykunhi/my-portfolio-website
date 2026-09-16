# Binoy Chemmagate - AI Product Manager Portfolio

A professional portfolio website showcasing expertise in AI product management, generative AI APIs, and communication technologies.

## 🚀 Features

- **Responsive Design**: Optimized for all devices and screen sizes
- **Professional Sections**: Hero, About, Experience, Skills, Projects, Blog, and Contact
- **Blog Integration**: Authentic articles from Medium profile
- **Clean UI**: Modern design with smooth animations and transitions
- **Fast Loading**: Optimized static HTML, CSS, and JavaScript
- **SEO Optimized**: Meta tags and semantic HTML structure

## 📁 Project Structure

```
├── index.html          # Main HTML file
├── styles.css          # All styling and responsive design
├── script.js           # Interactive functionality and animations
└── README.md          # Project documentation
```

## 🛠️ Technologies Used

- **HTML5**: Semantic markup and accessibility
- **CSS3**: Modern styling with CSS Grid, Flexbox, and animations
- **Vanilla JavaScript**: Interactive features and smooth scrolling
- **Lucide Icons**: Clean, consistent iconography
- **Google Fonts**: Inter font family for professional typography

## 🌟 Sections

### Hero Section
Professional introduction with gradient text and compelling headline

### About Section
Personal background, education, and key patents with quick facts sidebar

### Experience Section
Timeline view of professional experience at Vonage, callstats.io, and Nokia Bell Labs

### Skills Section
Organized competencies in Product Leadership, AI & Technology, Communication Technologies, and Protocol & Standards

### Projects Section
Featured projects showcasing AI API platforms, conversational AI, video communication, WebRTC analytics, protocol standards, and IoT solutions

### Blog Section
Authentic articles from Medium profile covering:
- CPaaS and AI technologies
- Product management insights
- WebRTC development tutorials
- Industry thought leadership

### Contact Section
Professional connection via LinkedIn with clear call-to-action

## Local Development

To test the Google Login feature locally, you must run the site on a local web server. Firebase Auth will not work if you open `index.html` directly (file:// protocol).

1.  **Start the local server**:
    ```bash
    ./start_server.sh
    ```
    This will start a server at `http://localhost:8000` and open it in your browser.

2.  **Firebase Configuration**:
    - Ensure `http://localhost` is added to your **Authorized Domains** in the Firebase Console (Authentication > Settings > Authorized Domains).
    - Ensure **Google** is enabled as a Sign-in provider.

## Deployment

### GitHub Pages
1. Upload all files to your GitHub repository
2. Go to repository Settings > Pages
3. Select "Deploy from a branch" and choose "main"
4. Your site will be available at `https://yourusername.github.io/repository-name`

### Other Hosting Options
The static files can be deployed to any web hosting service:
- Netlify: Drag and drop the files
- Vercel: Connect your GitHub repository
- Traditional web hosting: Upload via FTP

## 📱 Responsive Design

The website is fully responsive with breakpoints for:
- Mobile devices (< 768px)
- Tablets (768px - 1023px)
- Desktop (1024px+)

## ⚡ Performance Features

- Optimized images and assets
- Efficient CSS with minimal unused styles
- Debounced scroll events for smooth performance
- Lazy loading animations
- Clean, semantic HTML structure

## 🎨 Customization

### Colors
Update CSS custom properties in `:root` to change the color scheme:

```css
:root {
    --primary: #1e40af;
    --accent: #3b82f6;
    --background: #ffffff;
    --foreground: #0f172a;
    /* ... other colors */
}
```

### Content
- Update `index.html` to modify content
- Replace LinkedIn URLs with your profile
- Update Medium article links in the blog section
- Modify project details and achievements

### Styling
- Edit `styles.css` for visual changes
- Modify animations and transitions
- Adjust responsive breakpoints


## 🔐 Authentication Setup

This project uses **Firebase Authentication** (Google Sign-In) integrated via CDN to maintain the static nature of the site.

### 1. Firebase Configuration

1.  Create a project in the [Firebase Console](https://console.firebase.google.com/).
2.  Enable **Authentication** and set up the **Google** sign-in provider.
3.  Go to **Project Settings** -> **General** -> **Your apps** -> **SDK setup and configuration**.
4.  Copy the `firebaseConfig` object.
5.  Open `js/config.example.js`, paste your config, and rename the file to `js/config.js` (or create `js/config.js` with the content).

**Example `js/config.js`:**

```javascript
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_PROJECT_ID.appspot.com",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID"
};
window.firebaseConfig = firebaseConfig;
```

### 2. Local Development

Since this is a static site, you can serve it using any static file server.

```bash
# Using Python
python3 -m http.server 8000

# Using npm (if you have a package.json, otherwise npx)
npx serve .
```

**Important**: Ensure your `localhost` (e.g., `http://localhost:8000`) is added to the **Authorized Domains** in your Firebase Console Authentication settings.

### 3. Deployment

1.  Ensure `js/config.js` is created with your production Firebase credentials.
2.  Deploy all files (including `js/config.js`, `dashboard.html`, etc.) to your static hosting provider (GitHub Pages, Netlify, Vercel).
3.  Add your production domain to the **Authorized Domains** in Firebase Console.

## 📧 Contact

Connect with Binoy Chemmagate on [LinkedIn](https://linkedin.com/in/binoychemmagate)

## 📄 License

This project is open source and available under the [MIT License](LICENSE).