/**
 * Green-Code FX Mobile Optimization Module
 * Handles touch gestures, mobile-specific UI patterns, and responsive enhancements
 */

/**
 * Mobile Optimization Manager
 */
const MobileOptimizationManager = {
    isTouch: false,
    isMobile: false,
    swipeThreshold: 50,
    swipeTimeout: 300,
    
    init() {
        this.detectDevice();
        this.setupTouchHandling();
        this.setupMobileUI();
        this.setupSwipeGestures();
        this.setupOrientationHandling();
        this.setupMobileFAB();
        this.setupBottomSheet();
        
        console.log('Mobile Optimization initialized', {
            isTouch: this.isTouch,
            isMobile: this.isMobile
        });
    },
    
    detectDevice() {
        // Detect touch capability
        this.isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        
        // Detect mobile device
        this.isMobile = window.innerWidth <= 768 || /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        // Add classes to body for CSS targeting
        document.body.classList.toggle('touch-device', this.isTouch);
        document.body.classList.toggle('mobile-device', this.isMobile);
        
        // Set viewport meta tag for better mobile experience
        this.setupViewport();
    },
    
    setupViewport() {
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }
        
        // Enhanced viewport settings for better mobile experience
        viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes, viewport-fit=cover';
    },
    
    setupTouchHandling() {
        if (!this.isTouch) return;
        
        // Improve touch responsiveness
        document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
        
        // Prevent double-tap zoom on buttons and form controls
        const preventDoubleTap = (e) => {
            if (e.target.matches('button, input, select, textarea, .btn, .form-control')) {
                e.preventDefault();
            }
        };
        
        document.addEventListener('touchend', preventDoubleTap);
    },
    
    handleTouchStart(e) {
        // Add visual feedback for touch
        if (e.target.matches('.btn, button')) {
            e.target.classList.add('touch-active');
        }
    },
    
    handleTouchEnd(e) {
        // Remove visual feedback
        if (e.target.matches('.btn, button')) {
            setTimeout(() => {
                e.target.classList.remove('touch-active');
            }, 150);
        }
    },
    
    setupMobileUI() {
        if (!this.isMobile) return;
        
        // Add mobile-specific classes
        document.body.classList.add('mobile-optimized');
        
        // Enhance form labels for better touch interaction
        this.enhanceFormLabels();
        
        // Setup mobile-friendly tooltips
        this.setupMobileTooltips();
    },
    
    enhanceFormLabels() {
        const labels = document.querySelectorAll('label');
        labels.forEach(label => {
            label.addEventListener('click', (e) => {
                const target = document.getElementById(label.getAttribute('for'));
                if (target && target.focus) {
                    target.focus();
                }
            });
        });
    },
    
    setupMobileTooltips() {
        // Convert tooltips to touch-friendly versions on mobile
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(element => {
            if (this.isMobile) {
                // Change trigger to click for mobile
                element.setAttribute('data-bs-trigger', 'click');
            }
        });
    },
    
    setupSwipeGestures() {
        if (!this.isTouch) return;
        
        // Setup swipe detection for navigation elements
        this.setupCardSwipes();
        this.setupTabSwipes();
    },
    
    setupCardSwipes() {
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            this.addSwipeSupport(card, {
                onSwipeLeft: () => this.handleCardSwipeLeft(card),
                onSwipeRight: () => this.handleCardSwipeRight(card)
            });
        });
    },
    
    setupTabSwipes() {
        const tabContent = document.querySelector('.tab-content');
        if (tabContent) {
            this.addSwipeSupport(tabContent, {
                onSwipeLeft: () => this.switchToNextTab(),
                onSwipeRight: () => this.switchToPrevTab()
            });
        }
    },
    
    addSwipeSupport(element, callbacks) {
        let startX = 0;
        let startY = 0;
        let startTime = 0;
        
        element.addEventListener('touchstart', (e) => {
            const touch = e.touches[0];
            startX = touch.clientX;
            startY = touch.clientY;
            startTime = Date.now();
        }, { passive: true });
        
        element.addEventListener('touchend', (e) => {
            const touch = e.changedTouches[0];
            const endX = touch.clientX;
            const endY = touch.clientY;
            const endTime = Date.now();
            
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            const deltaTime = endTime - startTime;
            
            // Check if it's a valid swipe
            if (deltaTime < this.swipeTimeout && 
                Math.abs(deltaX) > this.swipeThreshold && 
                Math.abs(deltaX) > Math.abs(deltaY) * 2) {
                
                // Show swipe feedback
                this.showSwipeFeedback(element, deltaX > 0 ? 'right' : 'left');
                
                if (deltaX > 0 && callbacks.onSwipeRight) {
                    callbacks.onSwipeRight();
                } else if (deltaX < 0 && callbacks.onSwipeLeft) {
                    callbacks.onSwipeLeft();
                }
            }
        }, { passive: true });
    },
    
    showSwipeFeedback(element, direction) {
        const feedback = document.createElement('div');
        feedback.className = 'swipe-feedback active';
        element.style.position = 'relative';
        element.appendChild(feedback);
        
        setTimeout(() => {
            feedback.remove();
        }, 300);
    },
    
    handleCardSwipeLeft(card) {
        // Implement card-specific left swipe action
        console.log('Card swiped left', card);
        // Could be used for dismissing cards or navigating
    },
    
    handleCardSwipeRight(card) {
        // Implement card-specific right swipe action
        console.log('Card swiped right', card);
        // Could be used for favoriting or other actions
    },
    
    switchToNextTab() {
        const activeTab = document.querySelector('.nav-tabs .nav-link.active');
        if (activeTab) {
            const nextTab = activeTab.parentElement.nextElementSibling?.querySelector('.nav-link');
            if (nextTab) {
                nextTab.click();
                Utils.showToast('Swiped to next section', 'info');
            }
        }
    },
    
    switchToPrevTab() {
        const activeTab = document.querySelector('.nav-tabs .nav-link.active');
        if (activeTab) {
            const prevTab = activeTab.parentElement.previousElementSibling?.querySelector('.nav-link');
            if (prevTab) {
                prevTab.click();
                Utils.showToast('Swiped to previous section', 'info');
            }
        }
    },
    
    setupOrientationHandling() {
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });
        
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    },
    
    handleOrientationChange() {
        // Refresh mobile detection after orientation change
        this.detectDevice();
        
        // Adjust UI for new orientation
        if (this.isMobile) {
            this.adjustForOrientation();
        }
        
        console.log('Orientation changed', {
            orientation: screen.orientation?.angle || 'unknown',
            width: window.innerWidth,
            height: window.innerHeight
        });
    },
    
    adjustForOrientation() {
        const isLandscape = window.innerWidth > window.innerHeight;
        document.body.classList.toggle('landscape-mode', isLandscape);
        document.body.classList.toggle('portrait-mode', !isLandscape);
    },
    
    handleResize() {
        // Update mobile detection on resize
        const wasMobile = this.isMobile;
        this.detectDevice();
        
        if (wasMobile !== this.isMobile) {
            // Device type changed, reinitialize mobile UI
            this.setupMobileUI();
        }
    },
    
    setupMobileFAB() {
        if (!this.isMobile) return;
        
        // Create floating action button for quick actions
        const fab = document.createElement('button');
        fab.className = 'mobile-fab';
        fab.innerHTML = '<i class="fas fa-plus"></i>';
        fab.title = 'Quick Actions';
        fab.setAttribute('aria-label', 'Quick Actions');
        
        fab.addEventListener('click', () => {
            this.showQuickActions();
        });
        
        document.body.appendChild(fab);
    },
    
    showQuickActions() {
        // Show bottom sheet with quick actions
        this.showBottomSheet('Quick Actions', `
            <div class="d-grid gap-2">
                <button class="btn btn-outline-success" onclick="document.getElementById('generateBtn').click()">
                    <i class="fas fa-play me-2"></i>Generate Video
                </button>
                <button class="btn btn-outline-success" onclick="document.getElementById('previewBtn').click()">
                    <i class="fas fa-eye me-2"></i>Preview
                </button>
                <button class="btn btn-outline-success" onclick="ThemeManager.toggleTheme()">
                    <i class="fas fa-palette me-2"></i>Toggle Theme
                </button>
            </div>
        `);
    },
    
    setupBottomSheet() {
        // Create bottom sheet container
        const bottomSheet = document.createElement('div');
        bottomSheet.className = 'mobile-bottom-sheet';
        bottomSheet.id = 'mobileBottomSheet';
        
        const handle = document.createElement('div');
        handle.className = 'mobile-bottom-sheet-handle';
        
        const content = document.createElement('div');
        content.className = 'mobile-bottom-sheet-content';
        
        bottomSheet.appendChild(handle);
        bottomSheet.appendChild(content);
        document.body.appendChild(bottomSheet);
        
        // Handle close gestures
        handle.addEventListener('click', () => this.hideBottomSheet());
        bottomSheet.addEventListener('click', (e) => {
            if (e.target === bottomSheet) {
                this.hideBottomSheet();
            }
        });
        
        // Add swipe down to close
        this.addVerticalSwipeSupport(bottomSheet, {
            onSwipeDown: () => this.hideBottomSheet()
        });
    },
    
    showBottomSheet(title, content) {
        const bottomSheet = document.getElementById('mobileBottomSheet');
        const contentDiv = bottomSheet.querySelector('.mobile-bottom-sheet-content');
        
        contentDiv.innerHTML = `
            <h5 class="text-success mb-3">${title}</h5>
            ${content}
        `;
        
        bottomSheet.classList.add('show');
        
        // Add backdrop
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fade show';
        backdrop.addEventListener('click', () => this.hideBottomSheet());
        document.body.appendChild(backdrop);
    },
    
    hideBottomSheet() {
        const bottomSheet = document.getElementById('mobileBottomSheet');
        const backdrop = document.querySelector('.modal-backdrop');

        bottomSheet.classList.remove('show');
        if (backdrop) {
            backdrop.remove();
        }
    },

    addVerticalSwipeSupport(element, callbacks) {
        let startY = 0;
        let startTime = 0;

        element.addEventListener('touchstart', (e) => {
            const touch = e.touches[0];
            startY = touch.clientY;
            startTime = Date.now();
        }, { passive: true });

        element.addEventListener('touchend', (e) => {
            const touch = e.changedTouches[0];
            const endY = touch.clientY;
            const endTime = Date.now();

            const deltaY = endY - startY;
            const deltaTime = endTime - startTime;

            // Check if it's a valid vertical swipe
            if (deltaTime < this.swipeTimeout && Math.abs(deltaY) > this.swipeThreshold) {
                if (deltaY > 0 && callbacks.onSwipeDown) {
                    callbacks.onSwipeDown();
                } else if (deltaY < 0 && callbacks.onSwipeUp) {
                    callbacks.onSwipeUp();
                }
            }
        }, { passive: true });
    },

    // Utility methods for mobile optimization
    isMobileDevice() {
        return this.isMobile;
    },

    isTouchDevice() {
        return this.isTouch;
    },

    getDeviceInfo() {
        return {
            isMobile: this.isMobile,
            isTouch: this.isTouch,
            screenWidth: window.innerWidth,
            screenHeight: window.innerHeight,
            orientation: window.innerWidth > window.innerHeight ? 'landscape' : 'portrait',
            pixelRatio: window.devicePixelRatio || 1
        };
    },

    // Performance optimization for mobile
    optimizeForMobile() {
        if (!this.isMobile) return;

        // Reduce animations on low-end devices
        if (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 2) {
            document.body.classList.add('reduced-animations');
        }

        // Optimize images for mobile
        this.optimizeImages();

        // Lazy load non-critical content
        this.setupLazyLoading();
    },

    optimizeImages() {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (!img.loading) {
                img.loading = 'lazy';
            }
        });
    },

    setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const element = entry.target;
                        element.classList.add('loaded');
                        observer.unobserve(element);
                    }
                });
            });

            document.querySelectorAll('.lazy-load').forEach(el => {
                observer.observe(el);
            });
        }
    }
};

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.MobileOptimizationManager = MobileOptimizationManager;
}
