"""
Responsive design testing for Green-Code FX UI.

This module contains tests for responsive design validation across different device sizes,
ensuring the UI works properly on mobile devices, tablets, and desktop screens.
"""

import pytest
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException

# Import test utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# Device viewport configurations
DEVICE_VIEWPORTS = {
    'mobile_portrait': {'width': 375, 'height': 667},      # iPhone 6/7/8
    'mobile_landscape': {'width': 667, 'height': 375},     # iPhone 6/7/8 landscape
    'tablet_portrait': {'width': 768, 'height': 1024},     # iPad
    'tablet_landscape': {'width': 1024, 'height': 768},    # iPad landscape
    'desktop_small': {'width': 1280, 'height': 720},       # Small desktop
    'desktop_large': {'width': 1920, 'height': 1080},      # Large desktop
}


@pytest.fixture
def browser_driver():
    """Create Chrome browser driver for responsive testing."""
    chrome_options = ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        yield driver
    except WebDriverException as e:
        pytest.skip(f"Chrome browser not available: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()


@pytest.fixture
def app_url():
    """Base URL for the application."""
    return "http://localhost:8082"


class TestResponsiveLayout:
    """Test cases for responsive layout across different screen sizes."""
    
    @pytest.mark.parametrize("device_name,viewport", DEVICE_VIEWPORTS.items())
    def test_page_loads_on_device(self, browser_driver, app_url, device_name, viewport):
        """Test that the page loads properly on different device sizes."""
        # Set viewport size
        browser_driver.set_window_size(viewport['width'], viewport['height'])
        
        try:
            browser_driver.get(app_url)
            
            # Wait for page to load
            WebDriverWait(browser_driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check that main elements are present and visible
            form = browser_driver.find_element(By.ID, "videoGenerationForm")
            assert form.is_displayed(), f"Form not visible on {device_name}"
            
            # Check navigation
            navbar = browser_driver.find_element(By.CLASS_NAME, "navbar")
            assert navbar.is_displayed(), f"Navigation not visible on {device_name}"
            
        except TimeoutException:
            pytest.skip("Application not running or not accessible")

    def test_mobile_navigation_toggle(self, browser_driver, app_url):
        """Test mobile navigation toggle functionality."""
        # Set mobile viewport
        browser_driver.set_window_size(375, 667)
        browser_driver.get(app_url)
        
        # Wait for page to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "navbar"))
        )
        
        # Check if navbar toggle button is present (Bootstrap responsive behavior)
        try:
            toggle_button = browser_driver.find_element(By.CLASS_NAME, "navbar-toggler")
            # On mobile, toggle button should be visible
            assert toggle_button.is_displayed(), "Navbar toggle should be visible on mobile"
        except:
            # If no toggle button, navigation should still be accessible
            nav_items = browser_driver.find_elements(By.CLASS_NAME, "nav-link")
            assert len(nav_items) > 0, "Navigation items should be accessible"

    def test_form_layout_mobile(self, browser_driver, app_url):
        """Test form layout on mobile devices."""
        # Set mobile viewport
        browser_driver.set_window_size(375, 667)
        browser_driver.get(app_url)
        
        # Wait for form to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.ID, "videoGenerationForm"))
        )
        
        # Check that form elements stack vertically on mobile
        form_rows = browser_driver.find_elements(By.CLASS_NAME, "row")
        for row in form_rows:
            # On mobile, columns should stack (full width)
            columns = row.find_elements(By.XPATH, ".//*[contains(@class, 'col')]")
            for column in columns:
                # Check that columns are responsive
                assert column.is_displayed()

    def test_text_input_methods_mobile(self, browser_driver, app_url):
        """Test text input method selection on mobile."""
        # Set mobile viewport
        browser_driver.set_window_size(375, 667)
        browser_driver.get(app_url)
        
        # Wait for form to load
        WebDriverWait(browser_driver, 10).until(
            EC.element_to_be_clickable((By.ID, "methodCustom"))
        )
        
        # Test that radio button group is responsive
        button_group = browser_driver.find_element(By.CLASS_NAME, "btn-group")
        assert button_group.is_displayed()
        
        # Test switching between methods
        custom_radio = browser_driver.find_element(By.ID, "methodCustom")
        file_radio = browser_driver.find_element(By.ID, "methodFile")
        
        # Click file upload method
        file_radio.click()
        time.sleep(0.5)
        
        # Check that file upload section is visible and properly sized
        file_section = browser_driver.find_element(By.ID, "fileUploadSection")
        assert file_section.is_displayed()
        
        # Check file upload area is touch-friendly
        upload_area = browser_driver.find_element(By.CLASS_NAME, "file-upload-area")
        assert upload_area.is_displayed()
        
        # Get upload area dimensions
        area_size = upload_area.size
        assert area_size['height'] >= 100, "Upload area should be large enough for touch interaction"

    def test_form_controls_mobile(self, browser_driver, app_url):
        """Test form controls usability on mobile."""
        # Set mobile viewport
        browser_driver.set_window_size(375, 667)
        browser_driver.get(app_url)
        
        # Wait for form to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.ID, "fontSize"))
        )
        
        # Test font size slider on mobile
        font_slider = browser_driver.find_element(By.ID, "fontSize")
        assert font_slider.is_displayed()
        
        # Check slider is touch-friendly (minimum size)
        slider_size = font_slider.size
        assert slider_size['height'] >= 20, "Slider should be large enough for touch"
        
        # Test color input on mobile
        color_input = browser_driver.find_element(By.ID, "textColor")
        assert color_input.is_displayed()
        
        # Test duration input
        duration_input = browser_driver.find_element(By.ID, "duration")
        assert duration_input.is_displayed()

    def test_preview_panel_responsive(self, browser_driver, app_url):
        """Test preview panel responsiveness."""
        viewports = [
            {'width': 375, 'height': 667},   # Mobile
            {'width': 768, 'height': 1024},  # Tablet
            {'width': 1280, 'height': 720}   # Desktop
        ]
        
        for viewport in viewports:
            browser_driver.set_window_size(viewport['width'], viewport['height'])
            browser_driver.get(app_url)
            
            # Wait for page to load
            WebDriverWait(browser_driver, 10).until(
                EC.presence_of_element_located((By.ID, "previewArea"))
            )
            
            # Check preview area is visible and properly sized
            preview_area = browser_driver.find_element(By.ID, "previewArea")
            assert preview_area.is_displayed()
            
            # Check status area
            status_area = browser_driver.find_element(By.ID, "statusArea")
            assert status_area.is_displayed()

    def test_button_sizes_mobile(self, browser_driver, app_url):
        """Test button sizes are appropriate for mobile touch."""
        # Set mobile viewport
        browser_driver.set_window_size(375, 667)
        browser_driver.get(app_url)
        
        # Wait for buttons to load
        WebDriverWait(browser_driver, 10).until(
            EC.element_to_be_clickable((By.ID, "generateBtn"))
        )
        
        # Test main action buttons
        generate_btn = browser_driver.find_element(By.ID, "generateBtn")
        preview_btn = browser_driver.find_element(By.ID, "previewBtn")
        
        # Check button sizes are touch-friendly (minimum 44px height recommended)
        generate_size = generate_btn.size
        preview_size = preview_btn.size
        
        assert generate_size['height'] >= 35, "Generate button should be large enough for touch"
        assert preview_size['height'] >= 35, "Preview button should be large enough for touch"

    def test_text_readability_mobile(self, browser_driver, app_url):
        """Test text readability on mobile devices."""
        # Set mobile viewport
        browser_driver.set_window_size(375, 667)
        browser_driver.get(app_url)
        
        # Wait for page to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check that text is readable (not too small)
        labels = browser_driver.find_elements(By.CLASS_NAME, "form-label")
        for label in labels:
            if label.is_displayed():
                # Check font size is reasonable for mobile
                font_size = browser_driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).fontSize;", label
                )
                # Font size should be at least 14px for mobile readability
                size_value = float(font_size.replace('px', ''))
                assert size_value >= 14, f"Label font size {size_value}px too small for mobile"

    def test_horizontal_scrolling(self, browser_driver, app_url):
        """Test that there's no unwanted horizontal scrolling on mobile."""
        # Set mobile viewport
        browser_driver.set_window_size(375, 667)
        browser_driver.get(app_url)
        
        # Wait for page to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check page width doesn't exceed viewport
        page_width = browser_driver.execute_script("return document.body.scrollWidth;")
        viewport_width = browser_driver.execute_script("return window.innerWidth;")
        
        # Allow small tolerance for scrollbars
        assert page_width <= viewport_width + 20, "Page should not cause horizontal scrolling"

    def test_tablet_layout(self, browser_driver, app_url):
        """Test layout on tablet devices."""
        # Set tablet viewport
        browser_driver.set_window_size(768, 1024)
        browser_driver.get(app_url)
        
        # Wait for page to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.ID, "videoGenerationForm"))
        )
        
        # On tablet, form should use available space efficiently
        main_row = browser_driver.find_element(By.XPATH, "//div[contains(@class, 'row')][1]")
        assert main_row.is_displayed()
        
        # Check that columns are properly sized for tablet
        form_column = browser_driver.find_element(By.XPATH, "//div[contains(@class, 'col-lg-8')]")
        preview_column = browser_driver.find_element(By.XPATH, "//div[contains(@class, 'col-lg-4')]")
        
        assert form_column.is_displayed()
        assert preview_column.is_displayed()

    def test_landscape_orientation(self, browser_driver, app_url):
        """Test layout in landscape orientation."""
        # Set landscape mobile viewport
        browser_driver.set_window_size(667, 375)
        browser_driver.get(app_url)
        
        # Wait for page to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.ID, "videoGenerationForm"))
        )
        
        # Check that content is still accessible in landscape
        form = browser_driver.find_element(By.ID, "videoGenerationForm")
        assert form.is_displayed()
        
        # Check that vertical space is used efficiently
        viewport_height = browser_driver.execute_script("return window.innerHeight;")
        assert viewport_height == 375, "Viewport height should match landscape setting"

    def test_accessibility_mobile(self, browser_driver, app_url):
        """Test accessibility features on mobile."""
        # Set mobile viewport
        browser_driver.set_window_size(375, 667)
        browser_driver.get(app_url)
        
        # Wait for page to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check that form inputs have proper labels
        inputs = browser_driver.find_elements(By.TAG_NAME, "input")
        for input_elem in inputs:
            if input_elem.is_displayed() and input_elem.get_attribute("type") not in ["hidden", "radio"]:
                # Check for associated label or aria-label
                input_id = input_elem.get_attribute("id")
                if input_id:
                    try:
                        label = browser_driver.find_element(By.XPATH, f"//label[@for='{input_id}']")
                        assert label.is_displayed(), f"Label for {input_id} should be visible"
                    except:
                        # Check for aria-label as fallback
                        aria_label = input_elem.get_attribute("aria-label")
                        assert aria_label, f"Input {input_id} should have label or aria-label"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
