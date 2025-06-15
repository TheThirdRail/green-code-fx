/**
 * Green-Code FX Main JavaScript
 * Handles global functionality and utilities
 */

// Global configuration
const CONFIG = {
    API_BASE: '/api',
    POLL_INTERVAL: 2000, // 2 seconds
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    ALLOWED_EXTENSIONS: [
        '.txt', '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp',
        '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
        '.html', '.htm', '.css', '.scss', '.sass', '.less', '.json',
        '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
        '.md', '.markdown', '.rst', '.sql', '.sh', '.bash', '.zsh',
        '.fish', '.ps1', '.bat', '.cmd'
    ],
    COLOR_REGEX: /^#[0-9A-Fa-f]{6}$/
};

// Global state
const APP_STATE = {
    currentJobId: null,
    isGenerating: false,
    pollTimer: null,
    colorPicker: null
};

/**
 * Utility Functions
 */
const Utils = {
    /**
     * Format file size in human readable format
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Format duration in human readable format
     */
    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
    },

    /**
     * Validate hex color
     */
    isValidHexColor(color) {
        return CONFIG.COLOR_REGEX.test(color);
    },

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        // Add to toast container or create one
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1055';
            document.body.appendChild(container);
        }

        container.appendChild(toast);

        // Initialize and show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Make API request with enhanced error handling and retry logic
     */
    async apiRequest(endpoint, options = {}) {
        const maxRetries = options.retries || 0;
        let lastError;

        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                const requestOptions = {
                    headers: {
                        ...options.headers
                    },
                    ...options
                };

                // Only add Content-Type for JSON requests
                if (!options.body || typeof options.body === 'string') {
                    requestOptions.headers['Content-Type'] = 'application/json';
                }

                const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, requestOptions);

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    const error = new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
                    error.status = response.status;
                    error.response = response;
                    throw error;
                }

                return await response.json();
            } catch (error) {
                lastError = error;

                // Don't retry on client errors (4xx) or if it's the last attempt
                if (error.status >= 400 && error.status < 500 || attempt === maxRetries) {
                    break;
                }

                // Wait before retrying (exponential backoff)
                if (attempt < maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
                }
            }
        }

        console.error('API Request failed after retries:', lastError);
        throw lastError;
    },

    /**
     * Make API request for file uploads with progress tracking
     */
    async apiRequestWithProgress(endpoint, formData, onProgress = null) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            // Track upload progress
            if (onProgress && xhr.upload) {
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        onProgress(percentComplete);
                    }
                });
            }

            xhr.addEventListener('load', () => {
                try {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } else {
                        const errorData = JSON.parse(xhr.responseText || '{}');
                        const error = new Error(errorData.error || `HTTP ${xhr.status}: ${xhr.statusText}`);
                        error.status = xhr.status;
                        reject(error);
                    }
                } catch (e) {
                    reject(new Error('Failed to parse response'));
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('Network error occurred'));
            });

            xhr.addEventListener('timeout', () => {
                reject(new Error('Request timeout'));
            });

            xhr.open('POST', `${CONFIG.API_BASE}${endpoint}`);
            xhr.timeout = 300000; // 5 minutes timeout for file uploads
            xhr.send(formData);
        });
    }
};

/**
 * Advanced Font Management with Google Fonts
 */
const FontManager = {
    googleFonts: [
        { family: 'Fira Code', category: 'monospace', variants: ['400', '500', '600', '700'] },
        { family: 'Source Code Pro', category: 'monospace', variants: ['400', '500', '600', '700'] },
        { family: 'Roboto Mono', category: 'monospace', variants: ['400', '500', '700'] },
        { family: 'Ubuntu Mono', category: 'monospace', variants: ['400', '700'] },
        { family: 'Inconsolata', category: 'monospace', variants: ['400', '700'] },
        { family: 'Space Mono', category: 'monospace', variants: ['400', '700'] },
        { family: 'Courier Prime', category: 'monospace', variants: ['400', '700'] },
        { family: 'Anonymous Pro', category: 'monospace', variants: ['400', '700'] }
    ],

    loadedGoogleFonts: new Set(),

    async loadAvailableFonts() {
        try {
            const response = await Utils.apiRequest('/fonts');
            const fontSelect = document.getElementById('fontFamily');

            if (fontSelect && response.fonts) {
                // Clear existing options
                fontSelect.innerHTML = '';

                // Add system fonts first
                const systemGroup = document.createElement('optgroup');
                systemGroup.label = 'System Fonts';

                const jetbrainsOption = document.createElement('option');
                jetbrainsOption.value = 'jetbrains';
                jetbrainsOption.textContent = 'JetBrains Mono (Recommended)';
                jetbrainsOption.selected = true;
                systemGroup.appendChild(jetbrainsOption);

                response.fonts.forEach(font => {
                    if (font.id !== 'jetbrains') {
                        const option = document.createElement('option');
                        option.value = font.id;
                        option.textContent = font.name;
                        systemGroup.appendChild(option);
                    }
                });

                fontSelect.appendChild(systemGroup);

                // Add Google Fonts group
                const googleGroup = document.createElement('optgroup');
                googleGroup.label = 'Google Fonts (Monospace)';

                this.googleFonts.forEach(font => {
                    const option = document.createElement('option');
                    option.value = `google-${font.family.toLowerCase().replace(/\s+/g, '-')}`;
                    option.textContent = `${font.family} (Google)`;
                    option.dataset.googleFont = font.family;
                    googleGroup.appendChild(option);
                });

                fontSelect.appendChild(googleGroup);

                // Add font change handler
                fontSelect.addEventListener('change', this.handleFontChange.bind(this));
            }
        } catch (error) {
            console.warn('Failed to load fonts:', error);
            Utils.showToast('Failed to load available fonts', 'error');
        }
    },

    async handleFontChange(event) {
        const selectedValue = event.target.value;
        const selectedOption = event.target.selectedOptions[0];

        if (selectedOption && selectedOption.dataset.googleFont) {
            await this.loadGoogleFont(selectedOption.dataset.googleFont);
            this.applyFontPreview(selectedOption.dataset.googleFont);
        } else {
            this.applyFontPreview(null);
        }
    },

    async loadGoogleFont(fontFamily) {
        if (this.loadedGoogleFonts.has(fontFamily)) {
            return; // Already loaded
        }

        try {
            // Create link element for Google Fonts
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = `https://fonts.googleapis.com/css2?family=${fontFamily.replace(/\s+/g, '+')}:wght@400;500;600;700&display=swap`;

            // Add to document head
            document.head.appendChild(link);

            // Wait for font to load
            await this.waitForFontLoad(fontFamily);

            this.loadedGoogleFonts.add(fontFamily);

            Utils.showToast(`Loaded ${fontFamily} font`, 'success');
        } catch (error) {
            console.warn(`Failed to load Google Font: ${fontFamily}`, error);
            Utils.showToast(`Failed to load ${fontFamily} font`, 'error');
        }
    },

    waitForFontLoad(fontFamily, timeout = 5000) {
        return new Promise((resolve, reject) => {
            if (!('FontFace' in window)) {
                // Fallback for older browsers
                setTimeout(resolve, 1000);
                return;
            }

            const timeoutId = setTimeout(() => {
                reject(new Error(`Font load timeout: ${fontFamily}`));
            }, timeout);

            // Check if font is loaded
            const checkFont = () => {
                if (document.fonts.check(`16px "${fontFamily}"`)) {
                    clearTimeout(timeoutId);
                    resolve();
                } else {
                    setTimeout(checkFont, 100);
                }
            };

            checkFont();
        });
    },

    applyFontPreview(googleFontFamily) {
        const previewArea = document.getElementById('previewArea');
        if (!previewArea) return;

        const previewText = previewArea.querySelector('.preview-text');
        if (previewText) {
            if (googleFontFamily) {
                previewText.style.fontFamily = `"${googleFontFamily}", monospace`;
            } else {
                // Reset to default or system font
                previewText.style.fontFamily = '';
            }
        }
    },

    getFontFamilyCSS(fontId) {
        // Handle Google Fonts
        if (fontId.startsWith('google-')) {
            const fontName = fontId.replace('google-', '').replace(/-/g, ' ');
            const googleFont = this.googleFonts.find(f =>
                f.family.toLowerCase().replace(/\s+/g, '-') === fontId.replace('google-', '')
            );

            if (googleFont) {
                return `"${googleFont.family}", monospace`;
            }
        }

        // Handle system fonts
        switch (fontId) {
            case 'jetbrains':
                return '"JetBrains Mono", "Courier New", monospace';
            case 'courier':
                return '"Courier New", monospace';
            case 'consolas':
                return 'Consolas, "Courier New", monospace';
            default:
                return '"JetBrains Mono", "Courier New", monospace';
        }
    },

    addFontSearchFilter() {
        const fontSelect = document.getElementById('fontFamily');
        if (!fontSelect) return;

        // Create search input
        const searchContainer = document.createElement('div');
        searchContainer.className = 'font-search-container mb-2';
        searchContainer.innerHTML = `
            <input type="text" class="form-control form-control-sm bg-dark text-light border-secondary"
                   id="fontSearch" placeholder="Search fonts..." autocomplete="off">
        `;

        // Insert before font select
        fontSelect.parentNode.insertBefore(searchContainer, fontSelect);

        // Add search functionality
        const searchInput = document.getElementById('fontSearch');
        searchInput.addEventListener('input', (e) => {
            this.filterFonts(e.target.value);
        });
    },

    filterFonts(searchTerm) {
        const fontSelect = document.getElementById('fontFamily');
        if (!fontSelect) return;

        const options = fontSelect.querySelectorAll('option');
        const optgroups = fontSelect.querySelectorAll('optgroup');

        options.forEach(option => {
            const text = option.textContent.toLowerCase();
            const matches = text.includes(searchTerm.toLowerCase());
            option.style.display = matches ? '' : 'none';
        });

        // Hide empty optgroups
        optgroups.forEach(group => {
            const visibleOptions = group.querySelectorAll('option:not([style*="display: none"])');
            group.style.display = visibleOptions.length > 0 ? '' : 'none';
        });
    }
};

/**
 * Theme Management
 */
const ThemeManager = {
    init() {
        this.loadTheme();
        this.setupThemeToggle();
    },

    loadTheme() {
        const savedTheme = localStorage.getItem('green-code-fx-theme') || 'dark';
        this.setTheme(savedTheme);
    },

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('green-code-fx-theme', theme);
        this.updateThemeIcon(theme);
    },

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);

        // Show feedback
        Utils.showToast(`Switched to ${newTheme} theme`, 'success');
    },

    updateThemeIcon(theme) {
        const themeIcon = document.getElementById('themeIcon');
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    },

    setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }
};

/**
 * Keyboard Shortcuts Manager
 */
const KeyboardManager = {
    init() {
        this.setupGlobalShortcuts();
        this.showShortcutsHelp();
    },

    setupGlobalShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Don't trigger shortcuts when typing in form fields
            if (this.isTypingInForm(e.target)) return;

            // Ctrl+Enter: Generate video
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.triggerVideoGeneration();
            }

            // Ctrl+P: Toggle preview
            if (e.ctrlKey && e.key === 'p') {
                e.preventDefault();
                this.togglePreview();
            }

            // Ctrl+T: Toggle theme
            if (e.ctrlKey && e.key === 't') {
                e.preventDefault();
                ThemeManager.toggleTheme();
            }

            // Escape: Cancel generation or close modals
            if (e.key === 'Escape') {
                this.handleEscape();
            }
        });
    },

    isTypingInForm(element) {
        const formElements = ['INPUT', 'TEXTAREA', 'SELECT'];
        return formElements.includes(element.tagName) || element.contentEditable === 'true';
    },

    triggerVideoGeneration() {
        const generateBtn = document.getElementById('generateBtn');
        if (generateBtn && !generateBtn.disabled) {
            generateBtn.click();
            Utils.showToast('Video generation started (Ctrl+Enter)', 'info');
        }
    },

    togglePreview() {
        const previewArea = document.getElementById('previewArea');
        if (previewArea) {
            previewArea.scrollIntoView({ behavior: 'smooth' });
            Utils.showToast('Preview focused (Ctrl+P)', 'info');
        }
    },

    handleEscape() {
        // Close any open modals or cancel operations
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) bsModal.hide();
        });
    },

    showShortcutsHelp() {
        // Add keyboard shortcuts info to tooltips
        const generateBtn = document.getElementById('generateBtn');
        if (generateBtn) {
            generateBtn.setAttribute('title', generateBtn.getAttribute('title') + ' (Ctrl+Enter)');
        }
    }
};

/**
 * Browser Notifications Manager
 */
const NotificationManager = {
    init() {
        this.requestPermission();
    },

    async requestPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            try {
                await Notification.requestPermission();
            } catch (error) {
                console.warn('Notification permission request failed:', error);
            }
        }
    },

    showVideoCompleteNotification(jobId, fileName) {
        // Only show notification if tab is not active
        if (document.hidden && this.isNotificationSupported()) {
            try {
                const notification = new Notification('Video Generation Complete!', {
                    body: `Your typing effect video is ready for download.`,
                    icon: '/static/favicon.ico',
                    tag: `video-complete-${jobId}`,
                    requireInteraction: true
                });

                notification.onclick = () => {
                    window.focus();
                    notification.close();

                    // Scroll to download section
                    const downloadSection = document.getElementById('downloadSection');
                    if (downloadSection) {
                        downloadSection.scrollIntoView({ behavior: 'smooth' });
                    }
                };

                // Auto-close after 10 seconds
                setTimeout(() => notification.close(), 10000);
            } catch (error) {
                console.warn('Failed to show notification:', error);
            }
        }
    },

    isNotificationSupported() {
        return 'Notification' in window && Notification.permission === 'granted';
    },

    showPermissionPrompt() {
        if ('Notification' in window && Notification.permission === 'default') {
            Utils.showToast('Enable notifications to get alerts when videos are ready!', 'info');
        }
    }
};

/**
 * Smart Caching System Manager
 */
const CacheManager = {
    CACHE_KEYS: {
        USER_SETTINGS: 'green-code-fx-settings',
        PREVIEW_CACHE: 'green-code-fx-previews',
        FONT_CACHE: 'green-code-fx-fonts',
        CACHE_METADATA: 'green-code-fx-cache-meta'
    },

    CACHE_EXPIRY: {
        SETTINGS: 30 * 24 * 60 * 60 * 1000, // 30 days
        PREVIEWS: 24 * 60 * 60 * 1000,      // 24 hours
        FONTS: 7 * 24 * 60 * 60 * 1000      // 7 days
    },

    init() {
        this.cleanExpiredCache();
        this.loadUserSettings();
        this.setupCacheIndicators();
    },

    // Settings Cache Management
    saveUserSettings(settings) {
        try {
            const cacheData = {
                data: settings,
                timestamp: Date.now(),
                version: '1.0'
            };
            localStorage.setItem(this.CACHE_KEYS.USER_SETTINGS, JSON.stringify(cacheData));
            this.updateCacheIndicator('settings', true);
        } catch (error) {
            console.warn('Failed to save user settings to cache:', error);
        }
    },

    loadUserSettings() {
        try {
            const cached = localStorage.getItem(this.CACHE_KEYS.USER_SETTINGS);
            if (!cached) return null;

            const cacheData = JSON.parse(cached);
            if (this.isCacheExpired(cacheData.timestamp, this.CACHE_EXPIRY.SETTINGS)) {
                localStorage.removeItem(this.CACHE_KEYS.USER_SETTINGS);
                return null;
            }

            this.applyUserSettings(cacheData.data);
            this.updateCacheIndicator('settings', true);
            return cacheData.data;
        } catch (error) {
            console.warn('Failed to load user settings from cache:', error);
            return null;
        }
    },

    applyUserSettings(settings) {
        // Apply cached settings to form elements
        Object.keys(settings).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                if (element.type === 'checkbox' || element.type === 'radio') {
                    element.checked = settings[key];
                } else {
                    element.value = settings[key];
                }

                // Trigger change events for dependent updates
                element.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    },

    // Preview Cache Management
    savePreviewCache(settingsHash, previewData) {
        try {
            const cached = this.getPreviewCache();
            cached[settingsHash] = {
                data: previewData,
                timestamp: Date.now(),
                accessCount: 1
            };

            // Limit cache size (keep only 50 most recent)
            const entries = Object.entries(cached);
            if (entries.length > 50) {
                entries.sort((a, b) => b[1].timestamp - a[1].timestamp);
                const limitedCache = {};
                entries.slice(0, 50).forEach(([key, value]) => {
                    limitedCache[key] = value;
                });
                localStorage.setItem(this.CACHE_KEYS.PREVIEW_CACHE, JSON.stringify(limitedCache));
            } else {
                localStorage.setItem(this.CACHE_KEYS.PREVIEW_CACHE, JSON.stringify(cached));
            }

            this.updateCacheIndicator('previews', true);
        } catch (error) {
            console.warn('Failed to save preview to cache:', error);
        }
    },

    getPreviewCache() {
        try {
            const cached = localStorage.getItem(this.CACHE_KEYS.PREVIEW_CACHE);
            return cached ? JSON.parse(cached) : {};
        } catch (error) {
            console.warn('Failed to load preview cache:', error);
            return {};
        }
    },

    getCachedPreview(settingsHash) {
        try {
            const cached = this.getPreviewCache();
            const preview = cached[settingsHash];

            if (!preview) return null;

            if (this.isCacheExpired(preview.timestamp, this.CACHE_EXPIRY.PREVIEWS)) {
                delete cached[settingsHash];
                localStorage.setItem(this.CACHE_KEYS.PREVIEW_CACHE, JSON.stringify(cached));
                return null;
            }

            // Update access count and timestamp
            preview.accessCount++;
            preview.lastAccessed = Date.now();
            cached[settingsHash] = preview;
            localStorage.setItem(this.CACHE_KEYS.PREVIEW_CACHE, JSON.stringify(cached));

            return preview.data;
        } catch (error) {
            console.warn('Failed to get cached preview:', error);
            return null;
        }
    },

    // Utility Methods
    generateSettingsHash(settings) {
        // Create a hash of settings for cache key
        const settingsString = JSON.stringify(settings, Object.keys(settings).sort());
        return this.simpleHash(settingsString);
    },

    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash).toString(36);
    },

    isCacheExpired(timestamp, expiry) {
        return Date.now() - timestamp > expiry;
    },

    cleanExpiredCache() {
        // Clean expired preview cache
        const previewCache = this.getPreviewCache();
        let cleaned = false;

        Object.keys(previewCache).forEach(key => {
            if (this.isCacheExpired(previewCache[key].timestamp, this.CACHE_EXPIRY.PREVIEWS)) {
                delete previewCache[key];
                cleaned = true;
            }
        });

        if (cleaned) {
            localStorage.setItem(this.CACHE_KEYS.PREVIEW_CACHE, JSON.stringify(previewCache));
        }
    },

    setupCacheIndicators() {
        // Add cache status indicators to UI
        const statusArea = document.querySelector('.navbar-nav');
        if (statusArea && !document.getElementById('cacheStatus')) {
            const cacheIndicator = document.createElement('li');
            cacheIndicator.className = 'nav-item';
            cacheIndicator.innerHTML = `
                <span class="nav-link" id="cacheStatus" title="Cache Status">
                    <i class="fas fa-database me-1"></i>
                    <small id="cacheIndicator" class="text-muted">Cache</small>
                </span>
            `;
            statusArea.appendChild(cacheIndicator);
        }
    },

    updateCacheIndicator(type, hasData) {
        const indicator = document.getElementById('cacheIndicator');
        if (indicator) {
            const cacheStats = this.getCacheStats();
            indicator.textContent = `Cache (${cacheStats.settings}S/${cacheStats.previews}P)`;
            indicator.className = cacheStats.total > 0 ? 'text-success' : 'text-muted';
        }
    },

    getCacheStats() {
        const settings = localStorage.getItem(this.CACHE_KEYS.USER_SETTINGS) ? 1 : 0;
        const previews = Object.keys(this.getPreviewCache()).length;
        return {
            settings,
            previews,
            total: settings + previews
        };
    },

    clearCache(type = 'all') {
        try {
            if (type === 'all' || type === 'settings') {
                localStorage.removeItem(this.CACHE_KEYS.USER_SETTINGS);
            }
            if (type === 'all' || type === 'previews') {
                localStorage.removeItem(this.CACHE_KEYS.PREVIEW_CACHE);
            }
            if (type === 'all' || type === 'fonts') {
                localStorage.removeItem(this.CACHE_KEYS.FONT_CACHE);
            }

            this.updateCacheIndicator();
            Utils.showToast(`Cache cleared: ${type}`, 'success');
        } catch (error) {
            console.warn('Failed to clear cache:', error);
        }
    }
};

/**
 * Preset Templates Manager
 */
const PresetManager = {
    presets: {
        python: {
            name: 'Python',
            icon: 'fab fa-python',
            settings: {
                fontFamily: 'jetbrains',
                fontSize: 32,
                textColor: '#00FF00',
                typingSpeed: 120,
                duration: 90
            },
            sampleCode: `# Python Snake Game
import pygame
import random

class Snake:
    def __init__(self):
        self.body = [(10, 10)]
        self.direction = (0, 1)
        self.score = 0

    def move(self):
        head = self.body[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])
        self.body.insert(0, new_head)
        self.body.pop()

    def grow(self):
        self.body.append(self.body[-1])
        self.score += 1

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    snake = Snake()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        snake.move()
        screen.fill((0, 0, 0))
        # Draw snake logic here
        pygame.display.flip()
        clock.tick(10)

if __name__ == "__main__":
    main()`
        },
        javascript: {
            name: 'JavaScript',
            icon: 'fab fa-js-square',
            settings: {
                fontFamily: 'jetbrains',
                fontSize: 28,
                textColor: '#F7DF1E',
                typingSpeed: 140,
                duration: 75
            },
            sampleCode: `// JavaScript Snake Game
class Snake {
    constructor() {
        this.body = [{x: 10, y: 10}];
        this.direction = {x: 0, y: 1};
        this.score = 0;
    }

    move() {
        const head = {...this.body[0]};
        head.x += this.direction.x;
        head.y += this.direction.y;
        this.body.unshift(head);
        this.body.pop();
    }

    grow() {
        this.body.push({...this.body[this.body.length - 1]});
        this.score++;
    }

    draw(ctx) {
        ctx.fillStyle = '#00FF00';
        this.body.forEach(segment => {
            ctx.fillRect(segment.x * 20, segment.y * 20, 20, 20);
        });
    }
}

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const snake = new Snake();

function gameLoop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    snake.move();
    snake.draw(ctx);
    requestAnimationFrame(gameLoop);
}

gameLoop();`
        },
        java: {
            name: 'Java',
            icon: 'fab fa-java',
            settings: {
                fontFamily: 'jetbrains',
                fontSize: 30,
                textColor: '#ED8B00',
                typingSpeed: 100,
                duration: 120
            },
            sampleCode: `// Java Snake Game
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import java.util.ArrayList;

public class SnakeGame extends JPanel implements ActionListener, KeyListener {
    private ArrayList<Point> snake;
    private Point food;
    private int direction = 1; // 0=up, 1=right, 2=down, 3=left
    private Timer timer;
    private int score = 0;

    public SnakeGame() {
        this.setPreferredSize(new Dimension(800, 600));
        this.setBackground(Color.BLACK);
        this.setFocusable(true);
        this.addKeyListener(this);

        snake = new ArrayList<>();
        snake.add(new Point(10, 10));

        generateFood();
        timer = new Timer(100, this);
        timer.start();
    }

    public void generateFood() {
        int x = (int) (Math.random() * 40);
        int y = (int) (Math.random() * 30);
        food = new Point(x, y);
    }

    @Override
    public void paintComponent(Graphics g) {
        super.paintComponent(g);

        // Draw snake
        g.setColor(Color.GREEN);
        for (Point p : snake) {
            g.fillRect(p.x * 20, p.y * 20, 20, 20);
        }

        // Draw food
        g.setColor(Color.RED);
        g.fillRect(food.x * 20, food.y * 20, 20, 20);
    }

    @Override
    public void actionPerformed(ActionEvent e) {
        move();
        repaint();
    }

    public void move() {
        Point head = new Point(snake.get(0));

        switch (direction) {
            case 0: head.y--; break; // up
            case 1: head.x++; break; // right
            case 2: head.y++; break; // down
            case 3: head.x--; break; // left
        }

        snake.add(0, head);

        if (head.equals(food)) {
            score++;
            generateFood();
        } else {
            snake.remove(snake.size() - 1);
        }
    }

    @Override
    public void keyPressed(KeyEvent e) {
        switch (e.getKeyCode()) {
            case KeyEvent.VK_UP: direction = 0; break;
            case KeyEvent.VK_RIGHT: direction = 1; break;
            case KeyEvent.VK_DOWN: direction = 2; break;
            case KeyEvent.VK_LEFT: direction = 3; break;
        }
    }

    @Override
    public void keyTyped(KeyEvent e) {}

    @Override
    public void keyReleased(KeyEvent e) {}

    public static void main(String[] args) {
        JFrame frame = new JFrame("Snake Game");
        SnakeGame game = new SnakeGame();

        frame.add(game);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setResizable(false);
        frame.pack();
        frame.setVisible(true);
    }
}`
        },
        cpp: {
            name: 'C++',
            icon: 'fas fa-code',
            settings: {
                fontFamily: 'jetbrains',
                fontSize: 28,
                textColor: '#00599C',
                typingSpeed: 90,
                duration: 100
            },
            sampleCode: `// C++ Snake Game
#include <iostream>
#include <vector>
#include <conio.h>
#include <windows.h>

class Snake {
private:
    std::vector<std::pair<int, int>> body;
    int dirX, dirY;
    int score;

public:
    Snake() : dirX(0), dirY(1), score(0) {
        body.push_back({10, 10});
    }

    void move() {
        auto head = body.front();
        head.first += dirX;
        head.second += dirY;
        body.insert(body.begin(), head);
        body.pop_back();
    }

    void grow() {
        auto tail = body.back();
        body.push_back(tail);
        score++;
    }

    void setDirection(int x, int y) {
        dirX = x;
        dirY = y;
    }

    bool checkCollision(int width, int height) {
        auto head = body.front();

        // Wall collision
        if (head.first < 0 || head.first >= width ||
            head.second < 0 || head.second >= height) {
            return true;
        }

        // Self collision
        for (size_t i = 1; i < body.size(); i++) {
            if (body[i] == head) {
                return true;
            }
        }

        return false;
    }

    void draw() {
        system("cls");
        for (const auto& segment : body) {
            std::cout << "Snake segment at (" << segment.first
                     << ", " << segment.second << ")" << std::endl;
        }
        std::cout << "Score: " << score << std::endl;
    }

    int getScore() const { return score; }
    std::vector<std::pair<int, int>> getBody() const { return body; }
};

int main() {
    Snake snake;
    bool gameRunning = true;

    while (gameRunning) {
        snake.draw();

        if (_kbhit()) {
            char key = _getch();
            switch (key) {
                case 'w': snake.setDirection(0, -1); break;
                case 's': snake.setDirection(0, 1); break;
                case 'a': snake.setDirection(-1, 0); break;
                case 'd': snake.setDirection(1, 0); break;
                case 'q': gameRunning = false; break;
            }
        }

        snake.move();

        if (snake.checkCollision(20, 20)) {
            std::cout << "Game Over! Final Score: " << snake.getScore() << std::endl;
            gameRunning = false;
        }

        Sleep(200);
    }

    return 0;
}`
        }
    },

    init() {
        this.createPresetSelector();
        this.bindEvents();
    },

    createPresetSelector() {
        // Find the customization section by looking for the palette icon
        const customizationHeader = document.querySelector('h5 .fa-palette');
        if (!customizationHeader) return;

        const customizationSection = customizationHeader.closest('.row');
        if (!customizationSection) return;

        const presetContainer = document.createElement('div');
        presetContainer.className = 'col-12 mb-3';
        presetContainer.innerHTML = `
            <label class="form-label">Language Presets:</label>
            <div class="preset-buttons d-flex flex-wrap gap-2">
                ${Object.entries(this.presets).map(([key, preset]) => `
                    <button type="button" class="btn btn-outline-success btn-sm preset-btn"
                            data-preset="${key}" title="Apply ${preset.name} preset">
                        <i class="${preset.icon} me-1"></i>${preset.name}
                    </button>
                `).join('')}
                <button type="button" class="btn btn-outline-secondary btn-sm"
                        id="clearPreset" title="Clear preset and use custom settings">
                    <i class="fas fa-times me-1"></i>Custom
                </button>
            </div>
            <div class="form-text text-muted">Quick presets for common programming languages</div>
        `;

        // Insert at the beginning of the customization section
        const firstCol = customizationSection.querySelector('.col-12');
        if (firstCol) {
            customizationSection.insertBefore(presetContainer, firstCol.nextSibling);
        }
    },

    bindEvents() {
        // Preset button clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.preset-btn')) {
                const presetKey = e.target.closest('.preset-btn').dataset.preset;
                this.applyPreset(presetKey);
            } else if (e.target.closest('#clearPreset')) {
                this.clearPreset();
            }
        });
    },

    applyPreset(presetKey) {
        const preset = this.presets[presetKey];
        if (!preset) return;

        // Apply settings
        Object.entries(preset.settings).forEach(([key, value]) => {
            const element = document.getElementById(key);
            if (element) {
                element.value = value;
                element.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        // Apply sample code if using custom text
        const customTextRadio = document.querySelector('input[name="textInputMethod"][value="custom"]');
        const customTextArea = document.getElementById('customText');

        if (customTextRadio && customTextArea) {
            customTextRadio.checked = true;
            customTextArea.value = preset.sampleCode;
            customTextRadio.dispatchEvent(new Event('change', { bubbles: true }));
        }

        // Update UI feedback
        this.updatePresetSelection(presetKey);
        GreenCodeFX.Utils.showToast(`Applied ${preset.name} preset`, 'success');
    },

    clearPreset() {
        // Reset to default values
        const defaults = {
            fontFamily: 'jetbrains',
            fontSize: 32,
            textColor: '#00FF00',
            typingSpeed: 150,
            duration: 90
        };

        Object.entries(defaults).forEach(([key, value]) => {
            const element = document.getElementById(key);
            if (element) {
                element.value = value;
                element.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        // Clear custom text
        const defaultRadio = document.querySelector('input[name="textInputMethod"][value="default"]');
        if (defaultRadio) {
            defaultRadio.checked = true;
            defaultRadio.dispatchEvent(new Event('change', { bubbles: true }));
        }

        this.updatePresetSelection(null);
        GreenCodeFX.Utils.showToast('Preset cleared, using custom settings', 'info');
    },

    updatePresetSelection(activePreset) {
        // Update button states
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        document.getElementById('clearPreset')?.classList.remove('active');

        if (activePreset) {
            const activeBtn = document.querySelector(`[data-preset="${activePreset}"]`);
            if (activeBtn) {
                activeBtn.classList.add('active');
            }
        } else {
            document.getElementById('clearPreset')?.classList.add('active');
        }
    }
};

/**
 * Video Preview Manager
 */
const VideoPreviewManager = {
    init() {
        this.createPreviewContainer();
    },

    createPreviewContainer() {
        // Add video preview container to download section
        const downloadSection = document.getElementById('downloadSection');
        if (downloadSection && !document.getElementById('videoPreviewContainer')) {
            const previewContainer = document.createElement('div');
            previewContainer.id = 'videoPreviewContainer';
            previewContainer.className = 'mt-3';
            previewContainer.style.display = 'none';
            previewContainer.innerHTML = `
                <div class="text-center">
                    <h6 class="text-success mb-2">
                        <i class="fas fa-play me-1"></i>Video Preview
                    </h6>
                    <video id="videoPreview" controls class="w-100" style="max-height: 300px; border-radius: 0.375rem;">
                        Your browser does not support the video tag.
                    </video>
                </div>
            `;
            downloadSection.insertBefore(previewContainer, downloadSection.firstChild);
        }
    },

    showVideoPreview(videoUrl) {
        const previewContainer = document.getElementById('videoPreviewContainer');
        const videoElement = document.getElementById('videoPreview');

        if (previewContainer && videoElement) {
            videoElement.src = videoUrl;
            previewContainer.style.display = 'block';

            // Scroll to preview
            setTimeout(() => {
                previewContainer.scrollIntoView({ behavior: 'smooth' });
            }, 100);
        }
    },

    hideVideoPreview() {
        const previewContainer = document.getElementById('videoPreviewContainer');
        if (previewContainer) {
            previewContainer.style.display = 'none';
        }
    }
};

/**
 * Color Picker Management
 */
const ColorPickerManager = {
    init() {
        const colorInput = document.getElementById('textColor');
        const colorButton = document.getElementById('colorPickerButton');
        
        if (!colorInput || !colorButton) return;

        // Initialize Pickr color picker
        APP_STATE.colorPicker = Pickr.create({
            el: colorButton,
            theme: 'classic',
            default: colorInput.value,
            swatches: [
                '#00FF00', // Default green
                '#FF0000', // Red
                '#0000FF', // Blue
                '#FFFF00', // Yellow
                '#FF00FF', // Magenta
                '#00FFFF', // Cyan
                '#FFFFFF', // White
                '#FFA500'  // Orange
            ],
            components: {
                preview: true,
                opacity: false,
                hue: true,
                interaction: {
                    hex: true,
                    rgba: false,
                    hsla: false,
                    hsva: false,
                    cmyk: false,
                    input: true,
                    clear: false,
                    save: true
                }
            }
        });

        // Handle color changes
        APP_STATE.colorPicker.on('change', (color) => {
            const hexColor = color.toHEXA().toString();
            colorInput.value = hexColor;
            this.updatePreviewColor(hexColor);
        });

        // Handle manual input changes
        colorInput.addEventListener('input', (e) => {
            const color = e.target.value;
            if (Utils.isValidHexColor(color)) {
                APP_STATE.colorPicker.setColor(color);
                this.updatePreviewColor(color);
                e.target.classList.remove('is-invalid');
            } else {
                e.target.classList.add('is-invalid');
            }
        });
    },

    updatePreviewColor(color) {
        const previewArea = document.getElementById('previewArea');
        if (previewArea) {
            const previewText = previewArea.querySelector('.preview-text');
            if (previewText) {
                previewText.style.color = color;
            }
        }
    }
};

/**
 * Initialize application
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Green-Code FX UI Initialized');

    // Initialize core components
    CacheManager.init();
    ThemeManager.init();
    KeyboardManager.init();
    NotificationManager.init();
    VideoPreviewManager.init();
    PresetManager.init();
    FontManager.loadAvailableFonts();
    ColorPickerManager.init();
    ProgressEstimationManager.init();

    // Initialize mobile optimization if available
    if (typeof MobileOptimizationManager !== 'undefined') {
        MobileOptimizationManager.init();
        MobileOptimizationManager.optimizeForMobile();
    }

    // Initialize batch manager if available
    if (typeof BatchManager !== 'undefined') {
        BatchManager.init();
        BatchManager.startAutoRefresh();
    }

    // Initialize WebSocket client if available
    if (typeof WebSocketClient !== 'undefined') {
        WebSocketClient.init();
        WebSocketClient.startPing();
    }

    // Initialize collaboration manager if available
    if (typeof CollaborationManager !== 'undefined') {
        CollaborationManager.init();
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Show notification permission prompt after a delay
    setTimeout(() => {
        NotificationManager.showPermissionPrompt();
    }, 3000);
});

/**
 * Progress Estimation Manager
 * Handles intelligent progress estimation features and statistics
 */
const ProgressEstimationManager = {
    init() {
        this.addEstimationIndicators();
        this.loadEstimationStatistics();
    },

    addEstimationIndicators() {
        // Add estimation quality indicator to the progress section
        const progressContainer = document.getElementById('progressContainer');
        if (progressContainer && !document.getElementById('estimationIndicator')) {
            const indicator = document.createElement('div');
            indicator.id = 'estimationIndicator';
            indicator.className = 'mt-2 text-center';
            indicator.innerHTML = `
                <small class="text-muted">
                    <i class="fas fa-brain me-1"></i>
                    <span id="estimationQuality">Smart estimation active</span>
                </small>
            `;
            progressContainer.appendChild(indicator);
        }
    },

    async loadEstimationStatistics() {
        try {
            const response = await fetch('/api/estimation/statistics');
            if (response.ok) {
                const data = await response.json();
                this.updateEstimationQuality(data.statistics);
            }
        } catch (error) {
            console.warn('Failed to load estimation statistics:', error);
        }
    },

    updateEstimationQuality(stats) {
        const qualityElement = document.getElementById('estimationQuality');
        if (!qualityElement || !stats) return;

        const totalGenerations = stats.total_generations || 0;
        const successfulGenerations = stats.successful_generations || 0;

        if (totalGenerations === 0) {
            qualityElement.textContent = 'Building estimation data...';
            qualityElement.className = 'text-warning';
        } else if (successfulGenerations < 5) {
            qualityElement.textContent = `Learning from ${successfulGenerations} generations`;
            qualityElement.className = 'text-info';
        } else if (successfulGenerations < 20) {
            qualityElement.textContent = `Smart estimates (${successfulGenerations} samples)`;
            qualityElement.className = 'text-success';
        } else {
            qualityElement.textContent = `Intelligent estimates (${successfulGenerations}+ samples)`;
            qualityElement.className = 'text-success';
        }
    },

    showEstimationTooltip(confidence, samples) {
        // Show tooltip with estimation details
        const indicator = document.getElementById('estimationIndicator');
        if (indicator) {
            const confidencePercent = Math.round(confidence * 100);
            const tooltip = `Confidence: ${confidencePercent}% | Based on ${samples} similar generations`;
            indicator.title = tooltip;
        }
    }
};

// Export for use in other modules
window.GreenCodeFX = {
    CONFIG,
    APP_STATE,
    Utils,
    CacheManager,
    ThemeManager,
    KeyboardManager,
    NotificationManager,
    VideoPreviewManager,
    PresetManager,
    FontManager,
    ColorPickerManager,
    ProgressEstimationManager
};
