/**
 * Green-Code FX Main JavaScript
 * Handles global functionality and utilities
 */

// Global configuration
const CONFIG = {
    API_BASE: '/api',
    POLL_INTERVAL: 2000, // 2 seconds
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    ALLOWED_EXTENSIONS: ['.txt'],
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
 * Font Management
 */
const FontManager = {
    async loadAvailableFonts() {
        try {
            const response = await Utils.apiRequest('/fonts');
            const fontSelect = document.getElementById('fontFamily');
            
            if (fontSelect && response.fonts) {
                // Clear existing options except the first one
                fontSelect.innerHTML = '<option value="jetbrains" selected>JetBrains Mono (Recommended)</option>';
                
                // Add available fonts
                response.fonts.forEach(font => {
                    if (font.id !== 'jetbrains') {
                        const option = document.createElement('option');
                        option.value = font.id;
                        option.textContent = font.name;
                        fontSelect.appendChild(option);
                    }
                });
            }
        } catch (error) {
            console.warn('Failed to load fonts:', error);
            Utils.showToast('Failed to load available fonts', 'error');
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
    
    // Initialize components
    FontManager.loadAvailableFonts();
    ColorPickerManager.init();
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Export for use in other modules
window.GreenCodeFX = {
    CONFIG,
    APP_STATE,
    Utils,
    FontManager,
    ColorPickerManager
};
