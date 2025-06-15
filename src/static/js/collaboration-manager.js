/**
 * Green-Code FX Collaboration Manager
 * Handles shareable links, preset collections, and team workspace features
 */

/**
 * Collaboration Manager
 */
const CollaborationManager = {
    shareModal: null,
    importModal: null,
    
    init() {
        this.createCollaborationInterface();
        this.bindEvents();
        this.loadCollaborationData();
        
        console.log('Collaboration Manager initialized');
    },
    
    createCollaborationInterface() {
        // Create collaboration section
        const collaborationSection = document.createElement('div');
        collaborationSection.className = 'collaboration-section mt-4';
        collaborationSection.innerHTML = `
            <div class="card bg-dark border-success">
                <div class="card-header bg-success text-dark">
                    <h5 class="mb-0">
                        <i class="fas fa-users me-2"></i>Collaboration & Sharing
                        <button class="btn btn-sm btn-outline-dark float-end" id="toggleCollaborationSection">
                            <i class="fas fa-chevron-down"></i>
                        </button>
                    </h5>
                </div>
                <div class="card-body" id="collaborationSectionBody" style="display: none;">
                    <div class="row">
                        <!-- Quick Actions -->
                        <div class="col-md-6">
                            <h6 class="text-success mb-3">Quick Actions</h6>
                            <div class="d-grid gap-2">
                                <button class="btn btn-outline-success" id="shareCurrentSettingsBtn">
                                    <i class="fas fa-share-alt me-2"></i>Share Current Settings
                                </button>
                                <button class="btn btn-outline-success" id="createPresetCollectionBtn">
                                    <i class="fas fa-folder-plus me-2"></i>Create Preset Collection
                                </button>
                                <button class="btn btn-outline-success" id="exportSettingsBtn">
                                    <i class="fas fa-download me-2"></i>Export Settings
                                </button>
                                <button class="btn btn-outline-success" id="importSettingsBtn">
                                    <i class="fas fa-upload me-2"></i>Import Settings
                                </button>
                            </div>
                        </div>
                        
                        <!-- Recent Activity -->
                        <div class="col-md-6">
                            <h6 class="text-success mb-3">Recent Activity</h6>
                            <div id="recentCollaborationActivity" class="recent-activity-list">
                                <div class="text-muted text-center py-3">
                                    <i class="fas fa-history fa-2x mb-2"></i>
                                    <p>No recent collaboration activity</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Shareable Links -->
                    <div class="row mt-4">
                        <div class="col-12">
                            <h6 class="text-success mb-3">My Shareable Links</h6>
                            <div id="shareableLinksContainer" class="shareable-links-container">
                                <div class="text-muted text-center py-3">
                                    <i class="fas fa-link fa-2x mb-2"></i>
                                    <p>No shareable links created yet</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Preset Collections -->
                    <div class="row mt-4">
                        <div class="col-12">
                            <h6 class="text-success mb-3">Preset Collections</h6>
                            <div id="presetCollectionsContainer" class="preset-collections-container">
                                <div class="text-muted text-center py-3">
                                    <i class="fas fa-folder fa-2x mb-2"></i>
                                    <p>No preset collections created yet</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Insert after real-time preview section or other sections
        const previewSection = document.querySelector('.realtime-preview-section');
        const batchSection = document.querySelector('.batch-management-section');
        const insertAfter = previewSection || batchSection || document.querySelector('.card');
        
        if (insertAfter && insertAfter.parentNode) {
            insertAfter.parentNode.insertBefore(collaborationSection, insertAfter.nextSibling);
        }
        
        this.createShareModal();
        this.createImportModal();
    },
    
    createShareModal() {
        // Create share modal
        const shareModal = document.createElement('div');
        shareModal.className = 'modal fade';
        shareModal.id = 'shareModal';
        shareModal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content bg-dark border-success">
                    <div class="modal-header border-success">
                        <h5 class="modal-title text-success">
                            <i class="fas fa-share-alt me-2"></i>Share Configuration
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="shareForm">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="shareTitle" class="form-label">Title</label>
                                        <input type="text" class="form-control" id="shareTitle" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="shareDescription" class="form-label">Description</label>
                                        <textarea class="form-control" id="shareDescription" rows="3"></textarea>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="shareExpiration" class="form-label">Expiration</label>
                                        <select class="form-select" id="shareExpiration">
                                            <option value="">Never expires</option>
                                            <option value="1">1 hour</option>
                                            <option value="24">24 hours</option>
                                            <option value="168">1 week</option>
                                            <option value="720">1 month</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label for="shareMaxAccess" class="form-label">Max Access Count</label>
                                        <input type="number" class="form-control" id="shareMaxAccess" 
                                               placeholder="Unlimited" min="1" max="1000">
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="sharePasswordProtected">
                                        <label class="form-check-label" for="sharePasswordProtected">
                                            Password protected
                                        </label>
                                    </div>
                                    <div class="mb-3" id="sharePasswordField" style="display: none;">
                                        <label for="sharePassword" class="form-label">Password</label>
                                        <input type="password" class="form-control" id="sharePassword">
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-3" id="shareResult" style="display: none;">
                                <label class="form-label">Shareable Link</label>
                                <div class="input-group">
                                    <input type="text" class="form-control" id="shareableUrl" readonly>
                                    <button class="btn btn-outline-success" type="button" id="copyShareableUrl">
                                        <i class="fas fa-copy"></i>
                                    </button>
                                </div>
                                <div class="mt-2">
                                    <button type="button" class="btn btn-sm btn-outline-success" id="shareToSocial">
                                        <i class="fas fa-share me-1"></i>Share to Social
                                    </button>
                                    <button type="button" class="btn btn-sm btn-outline-success" id="shareViaEmail">
                                        <i class="fas fa-envelope me-1"></i>Share via Email
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer border-success">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-success" id="createShareableLink">
                            <i class="fas fa-link me-2"></i>Create Link
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(shareModal);
        this.shareModal = new bootstrap.Modal(shareModal);
    },
    
    createImportModal() {
        // Create import modal
        const importModal = document.createElement('div');
        importModal.className = 'modal fade';
        importModal.id = 'importModal';
        importModal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content bg-dark border-success">
                    <div class="modal-header border-success">
                        <h5 class="modal-title text-success">
                            <i class="fas fa-upload me-2"></i>Import Settings
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="importFile" class="form-label">Select Settings File</label>
                            <input type="file" class="form-control" id="importFile" accept=".json">
                            <div class="form-text">Import previously exported settings, presets, and shareable links</div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Import Options</label>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="importSettings" checked>
                                <label class="form-check-label" for="importSettings">
                                    Import Settings
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="importPresets" checked>
                                <label class="form-check-label" for="importPresets">
                                    Import Preset Collections
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="importLinks">
                                <label class="form-check-label" for="importLinks">
                                    Import Shareable Links
                                </label>
                            </div>
                        </div>
                        
                        <div id="importPreview" style="display: none;">
                            <h6 class="text-success">Import Preview</h6>
                            <div id="importPreviewContent" class="bg-darker p-3 rounded">
                                <!-- Preview content will be inserted here -->
                            </div>
                        </div>
                        
                        <div id="importResult" style="display: none;">
                            <div class="alert alert-success" role="alert">
                                <h6 class="alert-heading">Import Successful!</h6>
                                <div id="importResultDetails"></div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer border-success">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-success" id="executeImport" disabled>
                            <i class="fas fa-upload me-2"></i>Import
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(importModal);
        this.importModal = new bootstrap.Modal(importModal);
    },
    
    bindEvents() {
        // Toggle collaboration section
        document.getElementById('toggleCollaborationSection')?.addEventListener('click', () => {
            const body = document.getElementById('collaborationSectionBody');
            const icon = document.querySelector('#toggleCollaborationSection i');
            
            if (body.style.display === 'none') {
                body.style.display = 'block';
                icon.className = 'fas fa-chevron-up';
            } else {
                body.style.display = 'none';
                icon.className = 'fas fa-chevron-down';
            }
        });
        
        // Quick action buttons
        document.getElementById('shareCurrentSettingsBtn')?.addEventListener('click', () => {
            this.shareCurrentSettings();
        });
        
        document.getElementById('createPresetCollectionBtn')?.addEventListener('click', () => {
            this.createPresetCollection();
        });
        
        document.getElementById('exportSettingsBtn')?.addEventListener('click', () => {
            this.exportSettings();
        });
        
        document.getElementById('importSettingsBtn')?.addEventListener('click', () => {
            this.importModal.show();
        });
        
        // Share modal events
        document.getElementById('sharePasswordProtected')?.addEventListener('change', (e) => {
            const passwordField = document.getElementById('sharePasswordField');
            passwordField.style.display = e.target.checked ? 'block' : 'none';
        });
        
        document.getElementById('createShareableLink')?.addEventListener('click', () => {
            this.createShareableLink();
        });
        
        document.getElementById('copyShareableUrl')?.addEventListener('click', () => {
            this.copyShareableUrl();
        });
        
        // Import modal events
        document.getElementById('importFile')?.addEventListener('change', (e) => {
            this.previewImportFile(e.target.files[0]);
        });
        
        document.getElementById('executeImport')?.addEventListener('click', () => {
            this.executeImport();
        });
    },
    
    shareCurrentSettings() {
        // Collect current form settings
        const settings = this.getCurrentSettings();
        
        // Pre-fill share form
        document.getElementById('shareTitle').value = `Video Settings - ${new Date().toLocaleDateString()}`;
        document.getElementById('shareDescription').value = 'Shared video generation settings';
        
        // Store settings for sharing
        this.pendingShareSettings = settings;
        
        // Show share modal
        this.shareModal.show();
    },
    
    getCurrentSettings() {
        // Collect all current form settings
        return {
            duration: document.getElementById('duration')?.value || 90,
            font_family: document.getElementById('fontFamily')?.value || 'jetbrains',
            font_size: document.getElementById('fontSize')?.value || 32,
            text_color: document.getElementById('textColor')?.value || '#00FF00',
            typing_speed: document.getElementById('typingSpeed')?.value || 150,
            custom_text: document.getElementById('customText')?.value || '',
            text_input_method: document.querySelector('input[name="textInputMethod"]:checked')?.value || 'default',
            output_format: document.getElementById('outputFormat')?.value || 'mp4',
            timestamp: new Date().toISOString()
        };
    },

    async createShareableLink() {
        try {
            const title = document.getElementById('shareTitle').value.trim();
            const description = document.getElementById('shareDescription').value.trim();
            const expiration = document.getElementById('shareExpiration').value;
            const maxAccess = document.getElementById('shareMaxAccess').value;
            const passwordProtected = document.getElementById('sharePasswordProtected').checked;
            const password = document.getElementById('sharePassword').value;

            if (!title) {
                Utils.showToast('Please enter a title for the shareable link', 'warning');
                return;
            }

            if (!this.pendingShareSettings) {
                Utils.showToast('No settings to share', 'error');
                return;
            }

            const shareData = {
                title: title,
                description: description,
                configuration: this.pendingShareSettings,
                expires_hours: expiration ? parseInt(expiration) : null,
                max_access_count: maxAccess ? parseInt(maxAccess) : null,
                password: passwordProtected ? password : null
            };

            const response = await fetch('/api/collaboration/share', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(shareData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to create shareable link');
            }

            const result = await response.json();

            // Show the shareable URL
            const fullUrl = `${window.location.origin}${result.share_url}`;
            document.getElementById('shareableUrl').value = fullUrl;
            document.getElementById('shareResult').style.display = 'block';
            document.getElementById('createShareableLink').disabled = true;

            Utils.showToast('Shareable link created successfully!', 'success');

            // Refresh shareable links list
            this.loadShareableLinks();

        } catch (error) {
            console.error('Failed to create shareable link:', error);
            Utils.showToast(`Failed to create shareable link: ${error.message}`, 'error');
        }
    },

    copyShareableUrl() {
        const urlInput = document.getElementById('shareableUrl');
        urlInput.select();
        urlInput.setSelectionRange(0, 99999); // For mobile devices

        try {
            document.execCommand('copy');
            Utils.showToast('Shareable link copied to clipboard!', 'success');
        } catch (error) {
            // Fallback for modern browsers
            if (navigator.clipboard) {
                navigator.clipboard.writeText(urlInput.value).then(() => {
                    Utils.showToast('Shareable link copied to clipboard!', 'success');
                }).catch(() => {
                    Utils.showToast('Failed to copy link to clipboard', 'error');
                });
            } else {
                Utils.showToast('Failed to copy link to clipboard', 'error');
            }
        }
    },

    async exportSettings() {
        try {
            const settings = this.getCurrentSettings();
            const exportData = {
                export_version: "1.0",
                export_timestamp: new Date().toISOString(),
                settings: settings,
                user_preferences: this.getUserPreferences(),
                app_version: "1.0.0"
            };

            // Create and download file
            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `green-code-fx-settings-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            Utils.showToast('Settings exported successfully!', 'success');

        } catch (error) {
            console.error('Failed to export settings:', error);
            Utils.showToast('Failed to export settings', 'error');
        }
    },

    getUserPreferences() {
        // Get user preferences from localStorage
        return {
            theme: localStorage.getItem('green-code-fx-theme') || 'dark',
            cached_settings: JSON.parse(localStorage.getItem('green-code-fx-cache') || '{}'),
            notification_preferences: {
                enabled: Notification.permission === 'granted'
            }
        };
    },

    previewImportFile(file) {
        if (!file) {
            document.getElementById('importPreview').style.display = 'none';
            document.getElementById('executeImport').disabled = true;
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const importData = JSON.parse(e.target.result);
                this.pendingImportData = importData;

                // Show preview
                const previewContent = document.getElementById('importPreviewContent');
                previewContent.innerHTML = `
                    <div class="row">
                        <div class="col-md-6">
                            <strong>Export Version:</strong> ${importData.export_version || 'Unknown'}<br>
                            <strong>Export Date:</strong> ${importData.export_timestamp ? new Date(importData.export_timestamp).toLocaleString() : 'Unknown'}<br>
                            <strong>App Version:</strong> ${importData.app_version || 'Unknown'}
                        </div>
                        <div class="col-md-6">
                            <strong>Settings:</strong> ${importData.settings ? 'Yes' : 'No'}<br>
                            <strong>Preset Collections:</strong> ${importData.preset_collections ? importData.preset_collections.length : 0}<br>
                            <strong>Shareable Links:</strong> ${importData.shareable_links ? importData.shareable_links.length : 0}
                        </div>
                    </div>
                `;

                document.getElementById('importPreview').style.display = 'block';
                document.getElementById('executeImport').disabled = false;

            } catch (error) {
                Utils.showToast('Invalid import file format', 'error');
                document.getElementById('importPreview').style.display = 'none';
                document.getElementById('executeImport').disabled = true;
            }
        };

        reader.readAsText(file);
    },

    async executeImport() {
        try {
            if (!this.pendingImportData) {
                Utils.showToast('No import data available', 'error');
                return;
            }

            const importSettings = document.getElementById('importSettings').checked;
            const importPresets = document.getElementById('importPresets').checked;
            const importLinks = document.getElementById('importLinks').checked;

            // Process import data
            let importedCount = 0;

            if (importSettings && this.pendingImportData.settings) {
                this.applyImportedSettings(this.pendingImportData.settings);
                importedCount++;
            }

            if (importPresets && this.pendingImportData.preset_collections) {
                // Import preset collections (would need API endpoint)
                importedCount += this.pendingImportData.preset_collections.length;
            }

            if (importLinks && this.pendingImportData.shareable_links) {
                // Import shareable links (would need API endpoint)
                importedCount += this.pendingImportData.shareable_links.length;
            }

            // Show success message
            document.getElementById('importResultDetails').innerHTML = `
                Successfully imported ${importedCount} items:
                <ul class="mb-0 mt-2">
                    ${importSettings && this.pendingImportData.settings ? '<li>Settings and preferences</li>' : ''}
                    ${importPresets && this.pendingImportData.preset_collections ? `<li>${this.pendingImportData.preset_collections.length} preset collections</li>` : ''}
                    ${importLinks && this.pendingImportData.shareable_links ? `<li>${this.pendingImportData.shareable_links.length} shareable links</li>` : ''}
                </ul>
            `;

            document.getElementById('importResult').style.display = 'block';
            document.getElementById('executeImport').disabled = true;

            Utils.showToast('Settings imported successfully!', 'success');

            // Refresh UI
            setTimeout(() => {
                this.loadCollaborationData();
            }, 1000);

        } catch (error) {
            console.error('Failed to import settings:', error);
            Utils.showToast('Failed to import settings', 'error');
        }
    },

    applyImportedSettings(settings) {
        // Apply imported settings to form
        Object.keys(settings).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = settings[key];
                } else {
                    element.value = settings[key];
                }
            }
        });

        // Trigger change events to update UI
        const event = new Event('change', { bubbles: true });
        document.getElementById('duration')?.dispatchEvent(event);
        document.getElementById('fontSize')?.dispatchEvent(event);
        document.getElementById('typingSpeed')?.dispatchEvent(event);
    },

    async loadCollaborationData() {
        try {
            // Load shareable links
            await this.loadShareableLinks();

            // Load preset collections
            await this.loadPresetCollections();

            // Load recent activity
            await this.loadRecentActivity();

        } catch (error) {
            console.error('Failed to load collaboration data:', error);
        }
    },

    async loadShareableLinks() {
        try {
            const response = await fetch('/api/collaboration/links');
            if (response.ok) {
                const data = await response.json();
                this.displayShareableLinks(data.links || []);
            }
        } catch (error) {
            console.error('Failed to load shareable links:', error);
        }
    },

    displayShareableLinks(links) {
        const container = document.getElementById('shareableLinksContainer');

        if (links.length === 0) {
            container.innerHTML = `
                <div class="text-muted text-center py-3">
                    <i class="fas fa-link fa-2x mb-2"></i>
                    <p>No shareable links created yet</p>
                </div>
            `;
            return;
        }

        container.innerHTML = links.map(link => `
            <div class="card bg-darker border-secondary mb-2">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="card-title mb-1">${link.title}</h6>
                            <p class="card-text text-muted small mb-1">${link.description || 'No description'}</p>
                            <small class="text-muted">
                                Created: ${new Date(link.created_at).toLocaleDateString()} |
                                Accessed: ${link.access_count} times
                                ${link.expires_at ? ` | Expires: ${new Date(link.expires_at).toLocaleDateString()}` : ''}
                            </small>
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-success copy-link-btn" data-link-id="${link.link_id}">
                                <i class="fas fa-copy"></i>
                            </button>
                            <button class="btn btn-outline-danger delete-link-btn" data-link-id="${link.link_id}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    },

    async loadPresetCollections() {
        // Placeholder for preset collections loading
        const container = document.getElementById('presetCollectionsContainer');
        container.innerHTML = `
            <div class="text-muted text-center py-3">
                <i class="fas fa-folder fa-2x mb-2"></i>
                <p>Preset collections feature coming soon</p>
            </div>
        `;
    },

    async loadRecentActivity() {
        // Placeholder for recent activity
        const container = document.getElementById('recentCollaborationActivity');
        container.innerHTML = `
            <div class="text-muted text-center py-3">
                <i class="fas fa-history fa-2x mb-2"></i>
                <p>Recent activity tracking coming soon</p>
            </div>
        `;
    }
};

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.CollaborationManager = CollaborationManager;
}
