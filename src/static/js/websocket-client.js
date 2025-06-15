/**
 * Green-Code FX WebSocket Client
 * Handles real-time preview streaming and live updates
 */

/**
 * WebSocket Client Manager
 */
const WebSocketClient = {
    socket: null,
    connected: false,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    reconnectDelay: 1000,
    previewSession: null,
    previewContainer: null,
    
    init() {
        this.createPreviewInterface();
        this.bindEvents();
        this.connect();
        
        console.log('WebSocket Client initialized');
    },
    
    createPreviewInterface() {
        // Create real-time preview section
        const previewSection = document.createElement('div');
        previewSection.className = 'realtime-preview-section mt-4';
        previewSection.innerHTML = `
            <div class="card bg-dark border-success">
                <div class="card-header bg-success text-dark">
                    <h5 class="mb-0">
                        <i class="fas fa-eye me-2"></i>Real-time Preview
                        <span class="badge bg-secondary ms-2" id="wsConnectionStatus">Disconnected</span>
                        <button class="btn btn-sm btn-outline-dark float-end" id="togglePreviewSection">
                            <i class="fas fa-chevron-down"></i>
                        </button>
                    </h5>
                </div>
                <div class="card-body" id="previewSectionBody" style="display: none;">
                    <div class="row">
                        <div class="col-md-8">
                            <div class="preview-stream-container">
                                <div id="previewStream" class="preview-stream bg-darker border rounded p-3 text-center">
                                    <div class="preview-placeholder">
                                        <i class="fas fa-video fa-3x text-muted mb-3"></i>
                                        <p class="text-muted">Real-time preview will appear here</p>
                                        <p class="small text-muted">Adjust settings and click "Start Preview" to begin</p>
                                    </div>
                                </div>
                                <div class="preview-controls mt-3">
                                    <button class="btn btn-success" id="startPreviewBtn" disabled>
                                        <i class="fas fa-play me-2"></i>Start Preview
                                    </button>
                                    <button class="btn btn-warning" id="stopPreviewBtn" disabled>
                                        <i class="fas fa-stop me-2"></i>Stop Preview
                                    </button>
                                    <div class="float-end">
                                        <span class="badge bg-info" id="previewFPS">0 FPS</span>
                                        <span class="badge bg-secondary ms-1" id="previewFrameCount">0 frames</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <h6 class="text-success mb-3">Preview Settings</h6>
                            <div class="preview-settings">
                                <div class="mb-3">
                                    <label class="form-label small">Quality</label>
                                    <select class="form-select form-select-sm" id="previewQuality">
                                        <option value="low">Low (Fast)</option>
                                        <option value="medium" selected>Medium</option>
                                        <option value="high">High (Slow)</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label small">Frame Rate</label>
                                    <select class="form-select form-select-sm" id="previewFrameRate">
                                        <option value="15">15 FPS</option>
                                        <option value="30" selected>30 FPS</option>
                                        <option value="60">60 FPS</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label small">Preview Length</label>
                                    <select class="form-select form-select-sm" id="previewLength">
                                        <option value="5">5 seconds</option>
                                        <option value="10" selected>10 seconds</option>
                                        <option value="15">15 seconds</option>
                                        <option value="30">30 seconds</option>
                                    </select>
                                </div>
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="autoUpdatePreview" checked>
                                    <label class="form-check-label small" for="autoUpdatePreview">
                                        Auto-update on settings change
                                    </label>
                                </div>
                            </div>
                            
                            <div class="preview-stats mt-4">
                                <h6 class="text-success mb-3">Connection Stats</h6>
                                <div class="small">
                                    <div class="d-flex justify-content-between">
                                        <span>Status:</span>
                                        <span id="wsStatus" class="text-muted">Disconnected</span>
                                    </div>
                                    <div class="d-flex justify-content-between">
                                        <span>Latency:</span>
                                        <span id="wsLatency" class="text-muted">-</span>
                                    </div>
                                    <div class="d-flex justify-content-between">
                                        <span>Data Received:</span>
                                        <span id="wsDataReceived" class="text-muted">0 KB</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Insert after batch management section or main form
        const batchSection = document.querySelector('.batch-management-section');
        const mainForm = document.querySelector('.card');
        const insertAfter = batchSection || mainForm;
        
        if (insertAfter && insertAfter.parentNode) {
            insertAfter.parentNode.insertBefore(previewSection, insertAfter.nextSibling);
        }
        
        this.previewContainer = previewSection;
    },
    
    bindEvents() {
        // Toggle preview section
        document.getElementById('togglePreviewSection')?.addEventListener('click', () => {
            const body = document.getElementById('previewSectionBody');
            const icon = document.querySelector('#togglePreviewSection i');
            
            if (body.style.display === 'none') {
                body.style.display = 'block';
                icon.className = 'fas fa-chevron-up';
            } else {
                body.style.display = 'none';
                icon.className = 'fas fa-chevron-down';
            }
        });
        
        // Preview controls
        document.getElementById('startPreviewBtn')?.addEventListener('click', () => {
            this.startPreview();
        });
        
        document.getElementById('stopPreviewBtn')?.addEventListener('click', () => {
            this.stopPreview();
        });
        
        // Auto-update preview on settings change
        const settingsInputs = ['previewQuality', 'previewFrameRate', 'previewLength'];
        settingsInputs.forEach(inputId => {
            document.getElementById(inputId)?.addEventListener('change', () => {
                if (document.getElementById('autoUpdatePreview').checked && this.previewSession) {
                    this.updatePreviewSettings();
                }
            });
        });
        
        // Monitor main form changes for auto-preview
        const mainFormInputs = document.querySelectorAll('#videoGenerationForm input, #videoGenerationForm select, #videoGenerationForm textarea');
        mainFormInputs.forEach(input => {
            input.addEventListener('change', () => {
                if (document.getElementById('autoUpdatePreview').checked && this.previewSession) {
                    this.updatePreviewSettings();
                }
            });
        });
    },
    
    connect() {
        try {
            // Use secure WebSocket if page is HTTPS
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.hostname;
            const port = window.location.port ? parseInt(window.location.port) + 1 : 8083; // WebSocket server port

            this.socket = new WebSocket(`${protocol}//${host}:${port}`);
            
            this.socket.onopen = () => {
                this.connected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('Connected', 'success');
                console.log('WebSocket connected');
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };
            
            this.socket.onclose = () => {
                this.connected = false;
                this.updateConnectionStatus('Disconnected', 'danger');
                console.log('WebSocket disconnected');
                
                // Attempt to reconnect
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        this.updateConnectionStatus(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`, 'warning');
                        this.connect();
                    }, this.reconnectDelay * this.reconnectAttempts);
                } else {
                    this.updateConnectionStatus('Connection Failed', 'danger');
                }
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('Error', 'danger');
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus('Connection Failed', 'danger');
        }
    },
    
    updateConnectionStatus(status, type) {
        const statusBadge = document.getElementById('wsConnectionStatus');
        const statusText = document.getElementById('wsStatus');
        const startBtn = document.getElementById('startPreviewBtn');
        
        if (statusBadge) {
            statusBadge.textContent = status;
            statusBadge.className = `badge bg-${type} ms-2`;
        }
        
        if (statusText) {
            statusText.textContent = status;
            statusText.className = `text-${type}`;
        }
        
        if (startBtn) {
            startBtn.disabled = !this.connected;
        }
    },
    
    handleMessage(data) {
        switch (data.type) {
            case 'connection':
                console.log('WebSocket connection established:', data);
                break;
                
            case 'preview_started':
                this.handlePreviewStarted(data);
                break;
                
            case 'preview_stopped':
                this.handlePreviewStopped(data);
                break;
                
            case 'preview_frame':
                this.handlePreviewFrame(data);
                break;
                
            case 'preview_settings_updated':
                console.log('Preview settings updated:', data);
                break;
                
            case 'error':
                console.error('WebSocket error:', data.message);
                Utils.showToast(`Preview error: ${data.message}`, 'error');
                break;
                
            case 'pong':
                this.updateLatency(data.timestamp);
                break;
                
            default:
                console.log('Unknown WebSocket message:', data);
        }
    },
    
    handlePreviewStarted(data) {
        this.previewSession = data.session_id;
        
        document.getElementById('startPreviewBtn').disabled = true;
        document.getElementById('stopPreviewBtn').disabled = false;
        
        // Clear preview area
        const previewStream = document.getElementById('previewStream');
        previewStream.innerHTML = `
            <div class="preview-active">
                <div class="text-center mb-3">
                    <div class="spinner-border text-success" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2 text-success">Starting preview stream...</p>
                </div>
            </div>
        `;
        
        Utils.showToast('Preview stream started', 'success');
    },
    
    handlePreviewStopped(data) {
        this.previewSession = null;
        
        document.getElementById('startPreviewBtn').disabled = false;
        document.getElementById('stopPreviewBtn').disabled = true;
        
        // Reset preview area
        const previewStream = document.getElementById('previewStream');
        previewStream.innerHTML = `
            <div class="preview-placeholder">
                <i class="fas fa-video fa-3x text-muted mb-3"></i>
                <p class="text-muted">Real-time preview will appear here</p>
                <p class="small text-muted">Adjust settings and click "Start Preview" to begin</p>
            </div>
        `;
        
        // Reset counters
        document.getElementById('previewFPS').textContent = '0 FPS';
        document.getElementById('previewFrameCount').textContent = '0 frames';
        
        Utils.showToast('Preview stream stopped', 'info');
    },
    
    handlePreviewFrame(data) {
        // Update frame display (simplified - would show actual video frame)
        const previewStream = document.getElementById('previewStream');
        previewStream.innerHTML = `
            <div class="preview-frame">
                <div class="text-center">
                    <div class="bg-success text-dark p-3 rounded mb-2">
                        <h6>Frame ${data.frame_number}</h6>
                        <small>Timestamp: ${new Date(data.timestamp * 1000).toLocaleTimeString()}</small>
                    </div>
                    <div class="small text-muted">
                        Preview data: ${data.frame_data.substring(0, 50)}...
                    </div>
                </div>
            </div>
        `;
        
        // Update counters
        document.getElementById('previewFrameCount').textContent = `${data.frame_number} frames`;
        
        // Calculate FPS (simplified)
        const fps = Math.min(30, data.frame_number % 30 + 1);
        document.getElementById('previewFPS').textContent = `${fps} FPS`;
    },
    
    updateLatency(serverTimestamp) {
        const latency = Date.now() - (serverTimestamp * 1000);
        document.getElementById('wsLatency').textContent = `${latency}ms`;
    },

    startPreview() {
        if (!this.connected) {
            Utils.showToast('WebSocket not connected', 'error');
            return;
        }

        // Collect current form settings
        const parameters = this.collectPreviewParameters();

        const message = {
            type: 'start_preview',
            session_id: `preview_${Date.now()}`,
            parameters: parameters
        };

        this.sendMessage(message);
    },

    stopPreview() {
        if (!this.connected || !this.previewSession) {
            return;
        }

        const message = {
            type: 'stop_preview',
            session_id: this.previewSession
        };

        this.sendMessage(message);
    },

    updatePreviewSettings() {
        if (!this.connected || !this.previewSession) {
            return;
        }

        const parameters = this.collectPreviewParameters();

        const message = {
            type: 'update_preview_settings',
            session_id: this.previewSession,
            parameters: parameters
        };

        this.sendMessage(message);
    },

    collectPreviewParameters() {
        // Get main form parameters
        const mainFormData = {
            duration: parseInt(document.getElementById('duration')?.value || 10),
            font_size: parseInt(document.getElementById('fontSize')?.value || 32),
            typing_speed: parseInt(document.getElementById('typingSpeed')?.value || 150),
            text_color: document.getElementById('textColor')?.value || '#00FF00',
            font_family: document.getElementById('fontFamily')?.value || 'jetbrains',
            custom_text: document.getElementById('customText')?.value || 'Sample preview text'
        };

        // Get preview-specific settings
        const previewSettings = {
            quality: document.getElementById('previewQuality')?.value || 'medium',
            frame_rate: parseInt(document.getElementById('previewFrameRate')?.value || 30),
            preview_length: parseInt(document.getElementById('previewLength')?.value || 10)
        };

        return {
            ...mainFormData,
            ...previewSettings,
            effect_type: 'typing',
            output_format: 'preview' // Special format for preview
        };
    },

    sendMessage(message) {
        if (this.connected && this.socket) {
            try {
                this.socket.send(JSON.stringify(message));
            } catch (error) {
                console.error('Failed to send WebSocket message:', error);
                Utils.showToast('Failed to send message to preview server', 'error');
            }
        }
    },

    // Ping server to measure latency
    ping() {
        if (this.connected) {
            this.sendMessage({
                type: 'ping',
                timestamp: Date.now()
            });
        }
    },

    // Start periodic ping
    startPing() {
        setInterval(() => {
            this.ping();
        }, 5000); // Ping every 5 seconds
    },

    // Get connection status
    getStatus() {
        return {
            connected: this.connected,
            previewActive: !!this.previewSession,
            reconnectAttempts: this.reconnectAttempts
        };
    },

    // Disconnect WebSocket
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.connected = false;
        this.previewSession = null;
    }
};

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.WebSocketClient = WebSocketClient;
}
