/**
 * Green-Code FX Form Handler
 * Handles form interactions, validation, and submission
 */

/**
 * Form Management
 */
const FormManager = {
    init() {
        // Check browser support first
        if (!this.checkBrowserSupport()) {
            console.warn('Some features may not work properly in this browser');
        }

        this.bindEvents();
        this.initializeFormState();
        this.setupRealTimeValidation();
        this.setupDownloadInterface();
        this.requestNotificationPermission();
    },

    requestNotificationPermission() {
        // Request notification permission for completion alerts
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    console.log('Notification permission granted');
                }
            });
        }
    },

    bindEvents() {
        // Text input method selection
        const methodRadios = document.querySelectorAll('input[name="textInputMethod"]');
        methodRadios.forEach(radio => {
            radio.addEventListener('change', this.handleTextInputMethodChange.bind(this));
        });

        // Font size slider
        const fontSizeSlider = document.getElementById('fontSize');
        if (fontSizeSlider) {
            fontSizeSlider.addEventListener('input', this.updateFontSizeDisplay.bind(this));
        }

        // Character counter for custom text
        const customTextArea = document.getElementById('customText');
        if (customTextArea) {
            customTextArea.addEventListener('input', this.updateCharacterCount.bind(this));
        }

        // File upload handling
        this.initFileUpload();

        // Form submission
        const form = document.getElementById('videoGenerationForm');
        if (form) {
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
        }

        // Preview button
        const previewBtn = document.getElementById('previewBtn');
        if (previewBtn) {
            previewBtn.addEventListener('click', this.handlePreview.bind(this));
        }
    },

    initializeFormState() {
        // Set initial character count
        this.updateCharacterCount();
        
        // Set initial font size display
        this.updateFontSizeDisplay();
        
        // Set initial text input method
        this.handleTextInputMethodChange();
    },

    handleTextInputMethodChange() {
        const selectedMethod = document.querySelector('input[name="textInputMethod"]:checked')?.value;
        const customSection = document.getElementById('customTextSection');
        const fileSection = document.getElementById('fileUploadSection');

        // Hide all sections first
        if (customSection) customSection.style.display = 'none';
        if (fileSection) fileSection.style.display = 'none';

        // Show appropriate section
        switch (selectedMethod) {
            case 'custom':
                if (customSection) customSection.style.display = 'block';
                break;
            case 'file':
                if (fileSection) fileSection.style.display = 'block';
                break;
            case 'default':
                // No additional UI needed for default
                break;
        }

        // Clear form data when switching methods
        this.clearFormData();
    },

    clearFormData() {
        const customText = document.getElementById('customText');
        const fileInput = document.getElementById('textFile');
        
        if (customText) {
            customText.value = '';
            this.updateCharacterCount();
        }
        
        if (fileInput) {
            fileInput.value = '';
            this.clearFileUpload();
        }
    },

    updateFontSizeDisplay() {
        const slider = document.getElementById('fontSize');
        const display = document.getElementById('fontSizeValue');
        
        if (slider && display) {
            display.textContent = slider.value;
        }
    },

    updateCharacterCount() {
        const textArea = document.getElementById('customText');
        const counter = document.getElementById('charCount');
        
        if (textArea && counter) {
            const count = textArea.value.length;
            counter.textContent = count.toLocaleString();
            
            // Update color based on usage
            const maxLength = parseInt(textArea.getAttribute('maxlength')) || 50000;
            const percentage = (count / maxLength) * 100;
            
            if (percentage > 90) {
                counter.className = 'text-danger';
            } else if (percentage > 75) {
                counter.className = 'text-warning';
            } else {
                counter.className = 'text-muted';
            }
        }
    },

    initFileUpload() {
        const fileInput = document.getElementById('textFile');
        const uploadArea = document.querySelector('.file-upload-area');
        
        if (!fileInput || !uploadArea) return;

        // File input change handler
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));

        // Drag and drop handlers
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadArea.addEventListener('drop', this.handleFileDrop.bind(this));
        
        // Click to upload
        uploadArea.addEventListener('click', (e) => {
            if (e.target.tagName !== 'BUTTON') {
                fileInput.click();
            }
        });
    },

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    },

    handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
    },

    handleFileDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    },

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFile(file);
        }
    },

    processFile(file) {
        // Validate file
        const validation = this.validateFile(file);
        if (!validation.valid) {
            GreenCodeFX.Utils.showToast(validation.error, 'error');
            return;
        }

        // Update UI
        this.showFileUploadSuccess(file);
    },

    validateFile(file) {
        // Check file type
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        if (!GreenCodeFX.CONFIG.ALLOWED_EXTENSIONS.includes(extension)) {
            return {
                valid: false,
                error: 'Only .txt files are allowed'
            };
        }

        // Check file size
        if (file.size > GreenCodeFX.CONFIG.MAX_FILE_SIZE) {
            return {
                valid: false,
                error: `File size must be less than ${GreenCodeFX.Utils.formatFileSize(GreenCodeFX.CONFIG.MAX_FILE_SIZE)}`
            };
        }

        return { valid: true };
    },

    showFileUploadSuccess(file) {
        const placeholder = document.querySelector('.upload-placeholder');
        const success = document.querySelector('.upload-success');
        const fileName = document.getElementById('uploadedFileName');
        
        if (placeholder) placeholder.classList.add('d-none');
        if (success) success.classList.remove('d-none');
        if (fileName) fileName.textContent = `${file.name} (${GreenCodeFX.Utils.formatFileSize(file.size)})`;
    },

    clearFileUpload() {
        const fileInput = document.getElementById('textFile');
        const placeholder = document.querySelector('.upload-placeholder');
        const success = document.querySelector('.upload-success');
        
        if (fileInput) fileInput.value = '';
        if (placeholder) placeholder.classList.remove('d-none');
        if (success) success.classList.add('d-none');
    },

    async handlePreview() {
        const formData = this.collectFormData();
        if (!formData) return;

        try {
            // Validate form data first
            const validation = this.validateFormData(formData);
            if (!validation.valid) {
                GreenCodeFX.Utils.showToast(validation.error, 'warning');
                return;
            }

            // Show preview in the preview area
            await this.updatePreview(formData);
            GreenCodeFX.Utils.showToast('Preview updated', 'success');
        } catch (error) {
            console.error('Preview failed:', error);
            GreenCodeFX.Utils.showToast('Failed to generate preview', 'error');
        }
    },

    async updatePreview(formData) {
        const previewArea = document.getElementById('previewArea');
        if (!previewArea) return;

        // Show loading state
        previewArea.innerHTML = `
            <div class="preview-loading text-center">
                <div class="loading-spinner mb-2"></div>
                <p class="text-muted">Generating preview...</p>
            </div>
        `;

        try {
            // Get text content
            let previewText = await this.getPreviewText(formData);

            // Limit preview length for performance
            if (previewText.length > 1000) {
                previewText = previewText.substring(0, 1000) + '\n\n... (preview truncated)';
            }

            // Create preview HTML with typing animation
            this.renderTypingPreview(previewArea, previewText, formData);

        } catch (error) {
            console.error('Preview generation failed:', error);
            previewArea.innerHTML = `
                <div class="preview-error text-center">
                    <i class="fas fa-exclamation-triangle text-warning fa-2x mb-2"></i>
                    <p class="text-muted">Failed to generate preview</p>
                </div>
            `;
        }
    },

    async getPreviewText(formData) {
        try {
            // Use the preview API endpoint for server-side preview generation
            const previewData = new FormData();
            previewData.append('font_family', formData.font_family);
            previewData.append('font_size', formData.font_size);
            previewData.append('text_color', formData.text_color);
            previewData.append('textInputMethod', formData.textInputMethod);

            if (formData.textInputMethod === 'custom' && formData.custom_text) {
                previewData.append('custom_text', formData.custom_text);
            } else if (formData.textInputMethod === 'file') {
                const fileInput = document.getElementById('textFile');
                if (fileInput && fileInput.files && fileInput.files[0]) {
                    previewData.append('text_file', fileInput.files[0]);
                }
            }

            const response = await fetch('/api/preview', {
                method: 'POST',
                body: previewData
            });

            if (!response.ok) {
                throw new Error('Preview generation failed');
            }

            const result = await response.json();
            return result.preview_text;

        } catch (error) {
            console.warn('Server preview failed, using client-side fallback:', error);

            // Fallback to client-side preview
            if (formData.textInputMethod === 'custom' && formData.custom_text) {
                return formData.custom_text;
            } else if (formData.textInputMethod === 'file') {
                const fileInput = document.getElementById('textFile');
                if (fileInput && fileInput.files && fileInput.files[0]) {
                    return await this.readFileContent(fileInput.files[0]);
                }
                return '// Please select a text file to preview';
            } else {
                // Default snake game code
                return `// Default Snake Game Code
class Snake {
    constructor() {
        this.body = [{x: 10, y: 10}];
        this.direction = {x: 0, y: 0};
        this.score = 0;
    }

    update() {
        const head = {
            x: this.body[0].x + this.direction.x,
            y: this.body[0].y + this.direction.y
        };
        this.body.unshift(head);

        if (!this.hasEatenFood()) {
            this.body.pop();
        }
    }

    hasEatenFood() {
        return this.body[0].x === food.x && this.body[0].y === food.y;
    }

    draw(ctx) {
        ctx.fillStyle = '#00FF00';
        this.body.forEach(segment => {
            ctx.fillRect(segment.x * 20, segment.y * 20, 20, 20);
        });
    }
}`;
            }
        }
    },

    async readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    },

    renderTypingPreview(container, text, formData) {
        const fontSize = Math.max(12, Math.min(24, formData.font_size * 0.6));
        const fontFamily = this.getFontFamilyCSS(formData.font_family);

        container.innerHTML = `
            <div class="preview-text text-monospace"
                 style="color: ${formData.text_color};
                        font-size: ${fontSize}px;
                        font-family: ${fontFamily};
                        line-height: 1.4;">
                <span id="previewTypedText"></span><span class="preview-cursor">|</span>
            </div>
        `;

        // Start typing animation
        this.startTypingAnimation(text);
    },

    getFontFamilyCSS(fontFamily) {
        const fontMap = {
            'jetbrains': '"JetBrains Mono", "Courier New", monospace',
            'courier': '"Courier New", monospace',
            'consolas': 'Consolas, "Courier New", monospace',
            'monaco': 'Monaco, "Courier New", monospace'
        };
        return fontMap[fontFamily] || '"JetBrains Mono", "Courier New", monospace';
    },

    startTypingAnimation(text) {
        const typedTextElement = document.getElementById('previewTypedText');
        if (!typedTextElement) return;

        // Clear any existing animation
        if (this.typingTimer) {
            clearInterval(this.typingTimer);
        }

        let currentIndex = 0;
        const typingSpeed = 50; // milliseconds per character

        this.typingTimer = setInterval(() => {
            if (currentIndex < text.length) {
                const char = text[currentIndex];
                if (char === '\n') {
                    typedTextElement.innerHTML += '<br>';
                } else {
                    typedTextElement.innerHTML += this.escapeHtml(char);
                }
                currentIndex++;
            } else {
                clearInterval(this.typingTimer);
                this.typingTimer = null;
            }
        }, typingSpeed);
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    async handleFormSubmit(e) {
        e.preventDefault();

        if (GreenCodeFX.APP_STATE.isGenerating) {
            GreenCodeFX.Utils.showToast('Video generation already in progress', 'warning');
            return;
        }

        const formData = this.collectFormData();
        if (!formData) return;

        try {
            await this.retryOperation(
                () => this.submitVideoGeneration(formData),
                2, // Max 2 retries
                2000 // 2 second delay
            );
        } catch (error) {
            this.handleError(error, 'Video Generation');
        }
    },

    collectFormData() {
        const form = document.getElementById('videoGenerationForm');
        if (!form) return null;

        const formData = new FormData(form);
        const data = {};

        // Collect basic form data
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }

        // Add text input method
        data.textInputMethod = document.querySelector('input[name="textInputMethod"]:checked')?.value || 'default';

        // Validate required fields
        const validation = this.validateFormData(data);
        if (!validation.valid) {
            GreenCodeFX.Utils.showToast(validation.error, 'error');
            return null;
        }

        return data;
    },

    validateFormData(data) {
        const errors = [];

        // Validate duration
        const duration = parseInt(data.duration);
        if (isNaN(duration) || duration < 10 || duration > 600) {
            errors.push('Duration must be between 10 and 600 seconds');
        }

        // Validate font size
        const fontSize = parseInt(data.font_size);
        if (isNaN(fontSize) || fontSize < 12 || fontSize > 72) {
            errors.push('Font size must be between 12 and 72 pixels');
        }

        // Validate color
        if (!GreenCodeFX.Utils.isValidHexColor(data.text_color)) {
            errors.push('Please enter a valid hex color code (e.g., #00FF00)');
        }

        // Validate font family
        if (!data.font_family || data.font_family.trim().length === 0) {
            errors.push('Font family is required');
        }

        // Validate text input based on method
        if (data.textInputMethod === 'custom') {
            if (!data.custom_text || data.custom_text.trim().length === 0) {
                errors.push('Please enter some text for the typing effect');
            } else if (data.custom_text.length > 50000) {
                errors.push('Custom text is too long (maximum 50,000 characters)');
            }
        } else if (data.textInputMethod === 'file') {
            const fileInput = document.getElementById('textFile');
            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                errors.push('Please select a text file');
            } else {
                const file = fileInput.files[0];
                if (!file.name.toLowerCase().endsWith('.txt')) {
                    errors.push('Only .txt files are allowed');
                }
                if (file.size > 10 * 1024 * 1024) { // 10MB limit
                    errors.push('File size must be less than 10MB');
                }
            }
        }

        // Return validation result
        if (errors.length > 0) {
            return {
                valid: false,
                error: errors.length === 1 ? errors[0] : `Multiple validation errors:\n• ${errors.join('\n• ')}`,
                errors: errors
            };
        }

        return { valid: true };
    },

    /**
     * Setup real-time validation for form fields
     */
    setupRealTimeValidation() {
        // Duration validation
        const durationInput = document.getElementById('duration');
        if (durationInput) {
            durationInput.addEventListener('input', this.validateDurationField.bind(this));
            durationInput.addEventListener('blur', this.validateDurationField.bind(this));
        }

        // Font size validation
        const fontSizeInput = document.getElementById('fontSize');
        if (fontSizeInput) {
            fontSizeInput.addEventListener('input', this.validateFontSizeField.bind(this));
        }

        // Color validation
        const colorInput = document.getElementById('textColor');
        if (colorInput) {
            colorInput.addEventListener('input', this.validateColorField.bind(this));
            colorInput.addEventListener('blur', this.validateColorField.bind(this));
        }

        // Custom text validation
        const customTextArea = document.getElementById('customText');
        if (customTextArea) {
            customTextArea.addEventListener('input', this.validateCustomTextField.bind(this));
        }
    },

    validateDurationField(event) {
        const input = event.target;
        const value = parseInt(input.value);
        const isValid = !isNaN(value) && value >= 10 && value <= 600;

        this.setFieldValidation(input, isValid, isValid ? '' : 'Duration must be between 10 and 600 seconds');
    },

    validateFontSizeField(event) {
        const input = event.target;
        const value = parseInt(input.value);
        const isValid = !isNaN(value) && value >= 12 && value <= 72;

        this.setFieldValidation(input, isValid, isValid ? '' : 'Font size must be between 12 and 72 pixels');
    },

    validateColorField(event) {
        const input = event.target;
        const isValid = GreenCodeFX.Utils.isValidHexColor(input.value);

        this.setFieldValidation(input, isValid, isValid ? '' : 'Please enter a valid hex color (e.g., #00FF00)');
    },

    validateCustomTextField(event) {
        const input = event.target;
        const length = input.value.length;
        const isValid = length > 0 && length <= 50000;

        let message = '';
        if (length === 0) {
            message = 'Custom text is required';
        } else if (length > 50000) {
            message = 'Text is too long (maximum 50,000 characters)';
        }

        this.setFieldValidation(input, isValid, message);
    },

    setFieldValidation(input, isValid, message) {
        const feedbackElement = input.parentNode.querySelector('.invalid-feedback') ||
                               input.parentNode.querySelector('.form-text');

        if (isValid) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            if (feedbackElement && feedbackElement.classList.contains('text-danger')) {
                feedbackElement.textContent = feedbackElement.dataset.originalText || '';
                feedbackElement.classList.remove('text-danger');
                feedbackElement.classList.add('text-muted');
            }
        } else {
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
            if (feedbackElement) {
                if (!feedbackElement.dataset.originalText) {
                    feedbackElement.dataset.originalText = feedbackElement.textContent;
                }
                feedbackElement.textContent = message;
                feedbackElement.classList.remove('text-muted');
                feedbackElement.classList.add('text-danger');
            }
        }
    },

    async submitVideoGeneration(formData) {
        // Prepare submission data
        const submitData = new FormData();

        // Add form fields
        submitData.append('duration', formData.duration);
        submitData.append('font_family', formData.font_family);
        submitData.append('font_size', formData.font_size);
        submitData.append('text_color', formData.text_color);
        submitData.append('output_format', 'mp4');

        // Handle text input based on method
        if (formData.textInputMethod === 'custom') {
            submitData.append('custom_text', formData.custom_text);
        } else if (formData.textInputMethod === 'file') {
            const fileInput = document.getElementById('textFile');
            if (fileInput.files[0]) {
                submitData.append('text_file', fileInput.files[0]);
            }
        }
        // For 'default', don't add custom_text or text_file

        // Update UI state
        this.setGeneratingState(true);
        this.resetProgressTracking();

        try {
            // Submit to API with progress tracking for file uploads
            let result;
            if (formData.textInputMethod === 'file') {
                result = await GreenCodeFX.Utils.apiRequestWithProgress(
                    '/generate/typing',
                    submitData,
                    (progress) => this.updateUploadProgress(progress)
                );
            } else {
                const response = await fetch('/api/generate/typing', {
                    method: 'POST',
                    body: submitData
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
                }

                result = await response.json();
            }

            // Store job information
            GreenCodeFX.APP_STATE.currentJobId = result.job_id;
            GreenCodeFX.APP_STATE.jobStartTime = Date.now();
            GreenCodeFX.APP_STATE.estimatedDuration = this.parseEstimatedDuration(result.estimated_duration);

            // Start polling for job status
            this.startJobPolling();

            GreenCodeFX.Utils.showToast('Video generation started successfully', 'success');

        } catch (error) {
            this.setGeneratingState(false);
            this.showErrorState(error.message);
            throw error;
        }
    },

    parseEstimatedDuration(durationStr) {
        // Parse duration string like "45s" or "2m30s"
        if (!durationStr) return 60; // Default 1 minute

        const match = durationStr.match(/(\d+)s/);
        return match ? parseInt(match[1]) : 60;
    },

    resetProgressTracking() {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const timeRemaining = document.getElementById('timeRemaining');

        if (progressBar) {
            progressBar.style.width = '0%';
            progressBar.setAttribute('aria-valuenow', 0);
        }
        if (progressText) {
            progressText.textContent = 'Initializing...';
        }
        if (timeRemaining) {
            timeRemaining.textContent = '';
        }
    },

    updateUploadProgress(progress) {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');

        if (progressBar) {
            progressBar.style.width = `${Math.min(progress, 100)}%`;
            progressBar.setAttribute('aria-valuenow', Math.min(progress, 100));
        }
        if (progressText) {
            progressText.textContent = `Uploading file: ${Math.round(progress)}%`;
        }
    },

    showErrorState(errorMessage) {
        const statusArea = document.getElementById('statusArea');
        const progressContainer = document.getElementById('progressContainer');

        if (statusArea) {
            statusArea.innerHTML = `
                <div class="status-error">
                    <i class="fas fa-exclamation-triangle text-danger me-2"></i>
                    <span class="text-danger">Error: ${this.escapeHtml(errorMessage)}</span>
                </div>
            `;
        }
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
    },

    setGeneratingState(isGenerating) {
        GreenCodeFX.APP_STATE.isGenerating = isGenerating;

        const generateBtn = document.getElementById('generateBtn');
        const statusArea = document.getElementById('statusArea');
        const progressContainer = document.getElementById('progressContainer');

        if (generateBtn) {
            generateBtn.disabled = isGenerating;
            generateBtn.innerHTML = isGenerating
                ? '<span class="loading-spinner me-1"></span>Generating...'
                : '<i class="fas fa-play me-1"></i>Generate Video';
        }

        if (isGenerating) {
            if (statusArea) {
                statusArea.innerHTML = '<div class="status-processing"><i class="fas fa-cog fa-spin text-success me-2"></i><span class="text-success">Starting generation...</span></div>';
            }
            if (progressContainer) {
                progressContainer.style.display = 'block';
            }
        } else {
            if (statusArea) {
                statusArea.innerHTML = '<div class="status-idle"><i class="fas fa-clock text-muted me-2"></i><span class="text-muted">Ready to generate</span></div>';
            }
            if (progressContainer) {
                progressContainer.style.display = 'none';
            }
        }
    },

    startJobPolling() {
        if (GreenCodeFX.APP_STATE.pollTimer) {
            clearInterval(GreenCodeFX.APP_STATE.pollTimer);
        }

        GreenCodeFX.APP_STATE.pollTimer = setInterval(async () => {
            try {
                await this.checkJobStatus();
            } catch (error) {
                console.error('Job polling failed:', error);
                this.stopJobPolling();
                GreenCodeFX.Utils.showToast('Failed to check job status', 'error');
            }
        }, GreenCodeFX.CONFIG.POLL_INTERVAL);
    },

    stopJobPolling() {
        if (GreenCodeFX.APP_STATE.pollTimer) {
            clearInterval(GreenCodeFX.APP_STATE.pollTimer);
            GreenCodeFX.APP_STATE.pollTimer = null;
        }
    },

    async checkJobStatus() {
        if (!GreenCodeFX.APP_STATE.currentJobId) return;

        try {
            const response = await GreenCodeFX.Utils.apiRequest(`/jobs/${GreenCodeFX.APP_STATE.currentJobId}`);
            this.updateJobStatus(response);

            // Stop polling if job is complete or failed
            if (response.status === 'completed' || response.status === 'failed') {
                this.stopJobPolling();
                this.setGeneratingState(false);
            }
        } catch (error) {
            console.error('Status check failed:', error);
        }
    },

    updateJobStatus(jobData) {
        const statusArea = document.getElementById('statusArea');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const timeRemaining = document.getElementById('timeRemaining');
        const downloadSection = document.getElementById('downloadSection');
        const downloadBtn = document.getElementById('downloadBtn');
        const fileSize = document.getElementById('fileSize');
        const videoDuration = document.getElementById('videoDuration');

        // Update progress bar
        if (progressBar && typeof jobData.progress === 'number') {
            progressBar.style.width = `${jobData.progress}%`;
            progressBar.setAttribute('aria-valuenow', jobData.progress);
        }

        // Calculate time remaining
        const timeRemainingText = this.calculateTimeRemaining(jobData);

        // Update status text
        let statusHTML = '';
        let progressTextContent = '';

        switch (jobData.status) {
            case 'queued':
                statusHTML = '<div class="status-processing"><i class="fas fa-clock text-warning me-2"></i><span class="text-warning">Queued for processing...</span></div>';
                progressTextContent = 'Waiting in queue...';
                break;
            case 'running':
                statusHTML = '<div class="status-processing"><i class="fas fa-cog fa-spin text-success me-2"></i><span class="text-success">Generating video...</span></div>';
                progressTextContent = `Progress: ${jobData.progress || 0}%`;
                break;
            case 'completed':
                statusHTML = '<div class="status-complete"><i class="fas fa-check-circle text-success me-2"></i><span class="text-success">Generation complete!</span></div>';
                progressTextContent = 'Video ready for download';

                // Show download section
                if (downloadSection) {
                    downloadSection.style.display = 'block';
                }

                // Update download button
                if (downloadBtn && jobData.download_url) {
                    downloadBtn.href = jobData.download_url;
                    downloadBtn.download = jobData.download_url.split('/').pop();
                    downloadBtn.style.display = 'inline-block';
                }

                // Update file info
                if (fileSize && jobData.file_size) {
                    fileSize.textContent = jobData.file_size;
                }
                if (videoDuration && jobData.parameters && jobData.parameters.duration) {
                    videoDuration.textContent = `${jobData.parameters.duration}s`;
                }

                // Show completion notification
                this.showCompletionNotification(jobData);
                break;
            case 'failed':
                statusHTML = '<div class="status-error"><i class="fas fa-exclamation-triangle text-danger me-2"></i><span class="text-danger">Generation failed</span></div>';
                progressTextContent = jobData.error || 'Unknown error occurred';
                GreenCodeFX.Utils.showToast(`Generation failed: ${jobData.error || 'Unknown error'}`, 'error');
                break;
            default:
                statusHTML = '<div class="status-idle"><i class="fas fa-question text-muted me-2"></i><span class="text-muted">Unknown status</span></div>';
                progressTextContent = 'Status unknown';
        }

        if (statusArea) {
            statusArea.innerHTML = statusHTML;
        }
        if (progressText) {
            progressText.textContent = progressTextContent;
        }
        if (timeRemaining) {
            timeRemaining.textContent = timeRemainingText;
        }
    },

    calculateTimeRemaining(jobData) {
        if (jobData.status === 'completed' || jobData.status === 'failed') {
            return '';
        }

        if (!GreenCodeFX.APP_STATE.jobStartTime || !GreenCodeFX.APP_STATE.estimatedDuration) {
            return '';
        }

        const elapsed = (Date.now() - GreenCodeFX.APP_STATE.jobStartTime) / 1000;
        const progress = jobData.progress || 0;

        if (progress > 0) {
            const estimatedTotal = (elapsed / progress) * 100;
            const remaining = Math.max(0, estimatedTotal - elapsed);

            if (remaining > 60) {
                const minutes = Math.floor(remaining / 60);
                const seconds = Math.floor(remaining % 60);
                return `~${minutes}m ${seconds}s remaining`;
            } else {
                return `~${Math.floor(remaining)}s remaining`;
            }
        } else {
            return `~${GreenCodeFX.APP_STATE.estimatedDuration}s estimated`;
        }
    },

    showCompletionNotification(jobData) {
        // Show browser notification if supported and permission granted
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Video Generation Complete', {
                body: `Your typing effect video is ready for download (${jobData.file_size || 'Unknown size'})`,
                icon: '/static/favicon.ico',
                tag: 'video-complete'
            });
        }

        GreenCodeFX.Utils.showToast('Video generation completed successfully!', 'success');
    },

    /**
     * Enhanced download functionality
     */
    setupDownloadInterface() {
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', this.handleDownload.bind(this));
        }
    },

    async handleDownload(event) {
        const downloadBtn = event.target.closest('#downloadBtn');
        if (!downloadBtn || !downloadBtn.href) return;

        try {
            // Show download progress
            const originalText = downloadBtn.innerHTML;
            downloadBtn.innerHTML = '<span class="loading-spinner me-1"></span>Downloading...';
            downloadBtn.disabled = true;

            // Track download analytics
            this.trackDownload(downloadBtn.href);

            // Reset button after a delay
            setTimeout(() => {
                downloadBtn.innerHTML = originalText;
                downloadBtn.disabled = false;
            }, 2000);

        } catch (error) {
            console.error('Download failed:', error);
            GreenCodeFX.Utils.showToast('Download failed. Please try again.', 'error');
        }
    },

    trackDownload(downloadUrl) {
        // Track download for analytics (if needed)
        console.log('Download started:', downloadUrl);

        // Could send analytics to server here
        // fetch('/api/analytics/download', { method: 'POST', ... });
    },

    /**
     * Copy download link to clipboard
     */
    async copyDownloadLink() {
        const downloadBtn = document.getElementById('downloadBtn');
        if (!downloadBtn || !downloadBtn.href) return;

        try {
            await navigator.clipboard.writeText(downloadBtn.href);
            GreenCodeFX.Utils.showToast('Download link copied to clipboard', 'success');
        } catch (error) {
            console.error('Failed to copy link:', error);
            GreenCodeFX.Utils.showToast('Failed to copy link', 'error');
        }
    },

    /**
     * Enhanced error handling and recovery
     */
    handleError(error, context = 'Unknown') {
        console.error(`Error in ${context}:`, error);

        let userMessage = 'An unexpected error occurred';
        let errorType = 'error';

        // Categorize errors for better user feedback
        if (error.name === 'NetworkError' || error.message.includes('fetch')) {
            userMessage = 'Network error. Please check your connection and try again.';
            errorType = 'warning';
        } else if (error.status === 400) {
            userMessage = error.message || 'Invalid request. Please check your input.';
            errorType = 'warning';
        } else if (error.status === 413) {
            userMessage = 'File too large. Please select a smaller file.';
            errorType = 'warning';
        } else if (error.status === 429) {
            userMessage = 'Too many requests. Please wait a moment and try again.';
            errorType = 'warning';
        } else if (error.status >= 500) {
            userMessage = 'Server error. Please try again later.';
            errorType = 'error';
        } else if (error.message) {
            userMessage = error.message;
        }

        // Show user-friendly error message
        GreenCodeFX.Utils.showToast(userMessage, errorType);

        // Reset UI state if needed
        if (context === 'Video Generation') {
            this.setGeneratingState(false);
            this.showErrorState(userMessage);
        }

        // Log error for debugging (could send to analytics service)
        this.logError(error, context);
    },

    logError(error, context) {
        const errorLog = {
            timestamp: new Date().toISOString(),
            context: context,
            message: error.message,
            stack: error.stack,
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        // Store in localStorage for debugging
        try {
            const existingLogs = JSON.parse(localStorage.getItem('errorLogs') || '[]');
            existingLogs.push(errorLog);

            // Keep only last 10 errors
            if (existingLogs.length > 10) {
                existingLogs.splice(0, existingLogs.length - 10);
            }

            localStorage.setItem('errorLogs', JSON.stringify(existingLogs));
        } catch (e) {
            console.warn('Failed to store error log:', e);
        }

        // Could send to server for monitoring
        // this.sendErrorToServer(errorLog);
    },

    /**
     * Retry mechanism for failed operations
     */
    async retryOperation(operation, maxRetries = 3, delay = 1000) {
        let lastError;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return await operation();
            } catch (error) {
                lastError = error;

                if (attempt === maxRetries) {
                    throw error;
                }

                // Show retry notification
                GreenCodeFX.Utils.showToast(
                    `Attempt ${attempt} failed. Retrying in ${delay/1000}s...`,
                    'warning'
                );

                // Wait before retrying
                await new Promise(resolve => setTimeout(resolve, delay));

                // Exponential backoff
                delay *= 2;
            }
        }

        throw lastError;
    },

    /**
     * Graceful degradation for unsupported features
     */
    checkBrowserSupport() {
        const warnings = [];

        // Check for required features
        if (!window.fetch) {
            warnings.push('Your browser does not support modern networking features. Please update your browser.');
        }

        if (!window.FormData) {
            warnings.push('File upload may not work properly in your browser.');
        }

        if (!('Notification' in window)) {
            console.info('Browser notifications not supported');
        }

        if (!navigator.clipboard) {
            console.info('Clipboard API not supported');
        }

        // Show warnings to user
        warnings.forEach(warning => {
            GreenCodeFX.Utils.showToast(warning, 'warning');
        });

        return warnings.length === 0;
    },
};

// Global functions for template use
window.clearFileUpload = function() {
    FormManager.clearFileUpload();
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    FormManager.init();
});

// Export for use in other modules
window.GreenCodeFX = window.GreenCodeFX || {};
window.GreenCodeFX.FormManager = FormManager;
