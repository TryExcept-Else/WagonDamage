/*
 * Main JavaScript entry point for legacy/compatibility purposes
 * This file imports functionality from modular JS files
 */

// The functionality previously in this file has been moved to:
// - base.js (for logout modal and basic UI functionality)
// - common.js (for shared functionality across pages)
// - page-specific JS files (index.js, login.js, etc.)

// Simple wrapper to load scripts dynamically if needed
function loadScript(src) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// Optionally, add any legacy code here that hasn't been properly migrated
// to the modular JS files yet. 