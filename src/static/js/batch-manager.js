/**
 * Green-Code FX Batch Processing Manager
 * Handles batch video generation with queue management and progress tracking
 */

/**
 * Batch Processing Manager
 */
const BatchManager = {
    activeBatches: new Map(),
    batchContainer: null,
    
    init() {
        this.createBatchInterface();
        this.bindEvents();
        this.loadExistingBatches();
        
        console.log('Batch Manager initialized');
    },
    
    createBatchInterface() {
        // Create batch management interface
        const batchSection = document.createElement('div');
        batchSection.className = 'batch-management-section mt-4';
        batchSection.innerHTML = `
            <div class="card bg-dark border-success">
                <div class="card-header bg-success text-dark">
                    <h5 class="mb-0">
                        <i class="fas fa-layer-group me-2"></i>Batch Processing
                        <button class="btn btn-sm btn-outline-dark float-end" id="toggleBatchSection">
                            <i class="fas fa-chevron-down"></i>
                        </button>
                    </h5>
                </div>
                <div class="card-body" id="batchSectionBody" style="display: none;">
                    <!-- Batch Creation Form -->
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <h6 class="text-success mb-3">Create New Batch</h6>
                            <form id="batchCreationForm">
                                <div class="mb-3">
                                    <label for="batchName" class="form-label">Batch Name</label>
                                    <input type="text" class="form-control" id="batchName" required>
                                </div>
                                <div class="mb-3">
                                    <label for="batchDescription" class="form-label">Description</label>
                                    <textarea class="form-control" id="batchDescription" rows="2"></textarea>
                                </div>
                                <div class="row">
                                    <div class="col-md-6">
                                        <label for="batchPriority" class="form-label">Priority</label>
                                        <select class="form-select" id="batchPriority">
                                            <option value="low">Low</option>
                                            <option value="normal" selected>Normal</option>
                                            <option value="high">High</option>
                                        </select>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="batchConcurrentLimit" class="form-label">Concurrent Limit</label>
                                        <select class="form-select" id="batchConcurrentLimit">
                                            <option value="1">1</option>
                                            <option value="2" selected>2</option>
                                            <option value="3">3</option>
                                            <option value="4">4</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="mt-3">
                                    <button type="button" class="btn btn-success" id="addBatchItem">
                                        <i class="fas fa-plus me-2"></i>Add Item
                                    </button>
                                    <button type="submit" class="btn btn-outline-success ms-2" disabled id="createBatchBtn">
                                        <i class="fas fa-layer-group me-2"></i>Create Batch
                                    </button>
                                </div>
                            </form>
                        </div>
                        <div class="col-md-6">
                            <h6 class="text-success mb-3">Batch Items</h6>
                            <div id="batchItemsList" class="batch-items-list">
                                <div class="text-muted text-center py-3">
                                    <i class="fas fa-inbox fa-2x mb-2"></i>
                                    <p>No items added yet. Click "Add Item" to start building your batch.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Active Batches -->
                    <div class="row">
                        <div class="col-12">
                            <h6 class="text-success mb-3">Active Batches</h6>
                            <div id="activeBatchesList" class="active-batches-list">
                                <div class="text-muted text-center py-3">
                                    <i class="fas fa-tasks fa-2x mb-2"></i>
                                    <p>No active batches. Create a batch to get started.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Insert after the main form
        const mainForm = document.querySelector('.card');
        if (mainForm && mainForm.parentNode) {
            mainForm.parentNode.insertBefore(batchSection, mainForm.nextSibling);
        }
        
        this.batchContainer = batchSection;
    },
    
    bindEvents() {
        // Toggle batch section
        document.getElementById('toggleBatchSection')?.addEventListener('click', () => {
            const body = document.getElementById('batchSectionBody');
            const icon = document.querySelector('#toggleBatchSection i');
            
            if (body.style.display === 'none') {
                body.style.display = 'block';
                icon.className = 'fas fa-chevron-up';
            } else {
                body.style.display = 'none';
                icon.className = 'fas fa-chevron-down';
            }
        });
        
        // Add batch item
        document.getElementById('addBatchItem')?.addEventListener('click', () => {
            this.addBatchItem();
        });
        
        // Create batch form submission
        document.getElementById('batchCreationForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createBatch();
        });
        
        // Batch item management
        document.addEventListener('click', (e) => {
            if (e.target.closest('.remove-batch-item')) {
                this.removeBatchItem(e.target.closest('.batch-item'));
            } else if (e.target.closest('.start-batch-btn')) {
                const batchId = e.target.closest('.batch-card').dataset.batchId;
                this.startBatch(batchId);
            } else if (e.target.closest('.pause-batch-btn')) {
                const batchId = e.target.closest('.batch-card').dataset.batchId;
                this.pauseBatch(batchId);
            } else if (e.target.closest('.resume-batch-btn')) {
                const batchId = e.target.closest('.batch-card').dataset.batchId;
                this.resumeBatch(batchId);
            } else if (e.target.closest('.cancel-batch-btn')) {
                const batchId = e.target.closest('.batch-card').dataset.batchId;
                this.cancelBatch(batchId);
            } else if (e.target.closest('.delete-batch-btn')) {
                const batchId = e.target.closest('.batch-card').dataset.batchId;
                this.deleteBatch(batchId);
            }
        });
    },
    
    addBatchItem() {
        const itemsList = document.getElementById('batchItemsList');
        const itemCount = itemsList.querySelectorAll('.batch-item').length;
        
        // Get current form values to use as defaults
        const currentFormData = this.getCurrentFormData();
        
        const itemElement = document.createElement('div');
        itemElement.className = 'batch-item card bg-darker border-secondary mb-2';
        itemElement.innerHTML = `
            <div class="card-body p-3">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="card-title mb-0">Item ${itemCount + 1}</h6>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-batch-item">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label small">Name</label>
                        <input type="text" class="form-control form-control-sm" name="itemName" 
                               value="Video ${itemCount + 1}" required>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small">Priority</label>
                        <select class="form-select form-select-sm" name="itemPriority">
                            <option value="low">Low</option>
                            <option value="normal" selected>Normal</option>
                            <option value="high">High</option>
                        </select>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-md-4">
                        <label class="form-label small">Duration (s)</label>
                        <input type="number" class="form-control form-control-sm" name="duration" 
                               value="${currentFormData.duration || 90}" min="10" max="300" required>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label small">Font Size</label>
                        <select class="form-select form-select-sm" name="fontSize">
                            <option value="16">16pt</option>
                            <option value="24">24pt</option>
                            <option value="32" selected>32pt</option>
                            <option value="48">48pt</option>
                            <option value="64">64pt</option>
                        </select>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label small">Typing Speed</label>
                        <input type="number" class="form-control form-control-sm" name="typingSpeed" 
                               value="${currentFormData.typingSpeed || 150}" min="50" max="300" required>
                    </div>
                </div>
                <div class="mt-2">
                    <label class="form-label small">Custom Text</label>
                    <textarea class="form-control form-control-sm" name="customText" rows="2" 
                              placeholder="Enter custom text for this item..."></textarea>
                </div>
            </div>
        `;
        
        // Replace empty state if this is the first item
        if (itemCount === 0) {
            itemsList.innerHTML = '';
        }
        
        itemsList.appendChild(itemElement);
        this.updateCreateBatchButton();
    },
    
    removeBatchItem(itemElement) {
        itemElement.remove();
        this.updateBatchItemNumbers();
        this.updateCreateBatchButton();
    },
    
    updateBatchItemNumbers() {
        const items = document.querySelectorAll('.batch-item');
        items.forEach((item, index) => {
            const title = item.querySelector('.card-title');
            title.textContent = `Item ${index + 1}`;
            
            const nameInput = item.querySelector('input[name="itemName"]');
            if (nameInput.value.startsWith('Video ')) {
                nameInput.value = `Video ${index + 1}`;
            }
        });
    },
    
    updateCreateBatchButton() {
        const createBtn = document.getElementById('createBatchBtn');
        const itemCount = document.querySelectorAll('.batch-item').length;
        
        createBtn.disabled = itemCount === 0;
        createBtn.innerHTML = itemCount > 0 
            ? `<i class="fas fa-layer-group me-2"></i>Create Batch (${itemCount} items)`
            : `<i class="fas fa-layer-group me-2"></i>Create Batch`;
    },
    
    getCurrentFormData() {
        return {
            duration: document.getElementById('duration')?.value,
            typingSpeed: document.getElementById('typingSpeed')?.value,
            fontSize: document.getElementById('fontSize')?.value,
            textColor: document.getElementById('textColor')?.value
        };
    },
    
    async createBatch() {
        try {
            const name = document.getElementById('batchName').value.trim();
            const description = document.getElementById('batchDescription').value.trim();
            const priority = document.getElementById('batchPriority').value;
            const concurrentLimit = parseInt(document.getElementById('batchConcurrentLimit').value);
            
            // Collect batch items
            const items = [];
            const batchItems = document.querySelectorAll('.batch-item');
            
            batchItems.forEach((itemElement, index) => {
                const itemName = itemElement.querySelector('input[name="itemName"]').value;
                const itemPriority = itemElement.querySelector('select[name="itemPriority"]').value;
                const duration = parseInt(itemElement.querySelector('input[name="duration"]').value);
                const fontSize = parseInt(itemElement.querySelector('select[name="fontSize"]').value);
                const typingSpeed = parseInt(itemElement.querySelector('input[name="typingSpeed"]').value);
                const customText = itemElement.querySelector('textarea[name="customText"]').value;
                
                items.push({
                    name: itemName,
                    effect_type: "typing",
                    priority: itemPriority,
                    parameters: {
                        duration: duration,
                        font_size: fontSize,
                        typing_speed: typingSpeed,
                        custom_text: customText || `Sample text for ${itemName}`,
                        output_format: "mp4",
                        font_family: "jetbrains",
                        text_color: "#00FF00"
                    }
                });
            });
            
            if (items.length === 0) {
                Utils.showToast('Please add at least one item to the batch', 'warning');
                return;
            }
            
            // Create batch via API
            const response = await fetch('/api/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    description: description,
                    priority: priority,
                    concurrent_limit: concurrentLimit,
                    items: items
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to create batch');
            }
            
            const result = await response.json();
            
            Utils.showToast(`Batch "${name}" created successfully with ${items.length} items`, 'success');
            
            // Reset form
            this.resetBatchForm();
            
            // Refresh batch list
            this.loadExistingBatches();
            
        } catch (error) {
            console.error('Failed to create batch:', error);
            Utils.showToast(`Failed to create batch: ${error.message}`, 'error');
        }
    },

    resetBatchForm() {
        document.getElementById('batchCreationForm').reset();
        document.getElementById('batchItemsList').innerHTML = `
            <div class="text-muted text-center py-3">
                <i class="fas fa-inbox fa-2x mb-2"></i>
                <p>No items added yet. Click "Add Item" to start building your batch.</p>
            </div>
        `;
        this.updateCreateBatchButton();
    },

    async loadExistingBatches() {
        try {
            const response = await fetch('/api/batch');
            if (!response.ok) {
                throw new Error('Failed to load batches');
            }

            const data = await response.json();
            this.displayBatches(data.batches || []);

        } catch (error) {
            console.error('Failed to load batches:', error);
        }
    },

    displayBatches(batches) {
        const container = document.getElementById('activeBatchesList');

        if (batches.length === 0) {
            container.innerHTML = `
                <div class="text-muted text-center py-3">
                    <i class="fas fa-tasks fa-2x mb-2"></i>
                    <p>No active batches. Create a batch to get started.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';

        batches.forEach(batch => {
            const batchCard = this.createBatchCard(batch);
            container.appendChild(batchCard);
        });
    },

    createBatchCard(batch) {
        const card = document.createElement('div');
        card.className = 'batch-card card bg-darker border-secondary mb-3';
        card.dataset.batchId = batch.batch_id;

        const statusClass = this.getStatusClass(batch.status);
        const statusIcon = this.getStatusIcon(batch.status);

        card.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <h6 class="card-title mb-1">${batch.name}</h6>
                        <p class="card-text text-muted small mb-0">${batch.description || 'No description'}</p>
                    </div>
                    <span class="badge ${statusClass}">
                        <i class="${statusIcon} me-1"></i>${batch.status}
                    </span>
                </div>

                <div class="row mb-3">
                    <div class="col-md-3">
                        <small class="text-muted">Progress</small>
                        <div class="progress mt-1" style="height: 6px;">
                            <div class="progress-bar bg-success" style="width: ${batch.progress}%"></div>
                        </div>
                        <small class="text-muted">${batch.progress}%</small>
                    </div>
                    <div class="col-md-3">
                        <small class="text-muted">Items</small>
                        <div class="fw-bold">${batch.completed_items}/${batch.total_items}</div>
                    </div>
                    <div class="col-md-3">
                        <small class="text-muted">Failed</small>
                        <div class="fw-bold text-danger">${batch.failed_items}</div>
                    </div>
                    <div class="col-md-3">
                        <small class="text-muted">Priority</small>
                        <div class="fw-bold">${batch.priority}</div>
                    </div>
                </div>

                <div class="d-flex gap-2">
                    ${this.getBatchActionButtons(batch.status)}
                </div>
            </div>
        `;

        return card;
    },

    getStatusClass(status) {
        const statusClasses = {
            'pending': 'bg-secondary',
            'running': 'bg-primary',
            'completed': 'bg-success',
            'failed': 'bg-danger',
            'cancelled': 'bg-warning',
            'paused': 'bg-info'
        };
        return statusClasses[status] || 'bg-secondary';
    },

    getStatusIcon(status) {
        const statusIcons = {
            'pending': 'fas fa-clock',
            'running': 'fas fa-play',
            'completed': 'fas fa-check',
            'failed': 'fas fa-exclamation-triangle',
            'cancelled': 'fas fa-ban',
            'paused': 'fas fa-pause'
        };
        return statusIcons[status] || 'fas fa-question';
    },

    getBatchActionButtons(status) {
        switch (status) {
            case 'pending':
                return `
                    <button class="btn btn-sm btn-success start-batch-btn">
                        <i class="fas fa-play me-1"></i>Start
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-batch-btn">
                        <i class="fas fa-trash me-1"></i>Delete
                    </button>
                `;
            case 'running':
                return `
                    <button class="btn btn-sm btn-warning pause-batch-btn">
                        <i class="fas fa-pause me-1"></i>Pause
                    </button>
                    <button class="btn btn-sm btn-danger cancel-batch-btn">
                        <i class="fas fa-stop me-1"></i>Cancel
                    </button>
                `;
            case 'paused':
                return `
                    <button class="btn btn-sm btn-success resume-batch-btn">
                        <i class="fas fa-play me-1"></i>Resume
                    </button>
                    <button class="btn btn-sm btn-danger cancel-batch-btn">
                        <i class="fas fa-stop me-1"></i>Cancel
                    </button>
                `;
            case 'completed':
            case 'failed':
            case 'cancelled':
                return `
                    <button class="btn btn-sm btn-outline-danger delete-batch-btn">
                        <i class="fas fa-trash me-1"></i>Delete
                    </button>
                `;
            default:
                return '';
        }
    },

    async startBatch(batchId) {
        try {
            const response = await fetch(`/api/batch/${batchId}/start`, {
                method: 'POST'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to start batch');
            }

            Utils.showToast('Batch started successfully', 'success');
            this.loadExistingBatches();

        } catch (error) {
            console.error('Failed to start batch:', error);
            Utils.showToast(`Failed to start batch: ${error.message}`, 'error');
        }
    },

    async pauseBatch(batchId) {
        try {
            const response = await fetch(`/api/batch/${batchId}/pause`, {
                method: 'POST'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to pause batch');
            }

            Utils.showToast('Batch paused successfully', 'success');
            this.loadExistingBatches();

        } catch (error) {
            console.error('Failed to pause batch:', error);
            Utils.showToast(`Failed to pause batch: ${error.message}`, 'error');
        }
    },

    async resumeBatch(batchId) {
        try {
            const response = await fetch(`/api/batch/${batchId}/resume`, {
                method: 'POST'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to resume batch');
            }

            Utils.showToast('Batch resumed successfully', 'success');
            this.loadExistingBatches();

        } catch (error) {
            console.error('Failed to resume batch:', error);
            Utils.showToast(`Failed to resume batch: ${error.message}`, 'error');
        }
    },

    async cancelBatch(batchId) {
        if (!confirm('Are you sure you want to cancel this batch? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/batch/${batchId}/cancel`, {
                method: 'POST'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to cancel batch');
            }

            Utils.showToast('Batch cancelled successfully', 'success');
            this.loadExistingBatches();

        } catch (error) {
            console.error('Failed to cancel batch:', error);
            Utils.showToast(`Failed to cancel batch: ${error.message}`, 'error');
        }
    },

    async deleteBatch(batchId) {
        if (!confirm('Are you sure you want to delete this batch? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/batch/${batchId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to delete batch');
            }

            Utils.showToast('Batch deleted successfully', 'success');
            this.loadExistingBatches();

        } catch (error) {
            console.error('Failed to delete batch:', error);
            Utils.showToast(`Failed to delete batch: ${error.message}`, 'error');
        }
    },

    // Auto-refresh batch status
    startAutoRefresh() {
        setInterval(() => {
            this.loadExistingBatches();
        }, 5000); // Refresh every 5 seconds
    }
};

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.BatchManager = BatchManager;
}
