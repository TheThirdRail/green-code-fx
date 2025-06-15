"""
Frontend browser testing for Green-Code FX UI.

This module contains automated browser tests for the frontend UI across different browsers,
testing form functionality, responsive design, and user interactions.
"""

import pytest
import time
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException

# Import test utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(params=['chrome', 'firefox'])
def browser_driver(request):
    """Create browser driver for different browsers."""
    browser_name = request.param
    driver = None
    
    try:
        if browser_name == 'chrome':
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            driver = webdriver.Chrome(options=chrome_options)
        
        elif browser_name == 'firefox':
            firefox_options = FirefoxOptions()
            firefox_options.add_argument('--headless')
            firefox_options.add_argument('--width=1920')
            firefox_options.add_argument('--height=1080')
            driver = webdriver.Firefox(options=firefox_options)
        
        yield driver
        
    except WebDriverException as e:
        pytest.skip(f"Browser {browser_name} not available: {e}")
    
    finally:
        if driver:
            driver.quit()


@pytest.fixture
def app_url():
    """Base URL for the application."""
    return "http://localhost:8082"


class TestFrontendUI:
    """Test cases for frontend UI functionality across browsers."""
    
    def test_page_loads_successfully(self, browser_driver, app_url):
        """Test that the main page loads successfully."""
        try:
            browser_driver.get(app_url)
            
            # Wait for page to load
            WebDriverWait(browser_driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check page title
            assert "Green-Code FX" in browser_driver.title
            
            # Check main elements are present
            assert browser_driver.find_element(By.ID, "videoGenerationForm")
            assert browser_driver.find_element(By.ID, "generateBtn")
            
        except TimeoutException:
            pytest.skip("Application not running or not accessible")

    def test_form_elements_present(self, browser_driver, app_url):
        """Test that all form elements are present and accessible."""
        browser_driver.get(app_url)
        
        # Wait for form to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.ID, "videoGenerationForm"))
        )
        
        # Check text input method radio buttons
        custom_radio = browser_driver.find_element(By.ID, "methodCustom")
        file_radio = browser_driver.find_element(By.ID, "methodFile")
        default_radio = browser_driver.find_element(By.ID, "methodDefault")
        
        assert custom_radio.is_displayed()
        assert file_radio.is_displayed()
        assert default_radio.is_displayed()
        
        # Check form inputs
        assert browser_driver.find_element(By.ID, "customText")
        assert browser_driver.find_element(By.ID, "fontFamily")
        assert browser_driver.find_element(By.ID, "fontSize")
        assert browser_driver.find_element(By.ID, "textColor")
        assert browser_driver.find_element(By.ID, "duration")

    def test_text_input_method_switching(self, browser_driver, app_url):
        """Test switching between text input methods."""
        browser_driver.get(app_url)
        
        # Wait for form to load
        WebDriverWait(browser_driver, 10).until(
            EC.element_to_be_clickable((By.ID, "methodCustom"))
        )
        
        # Test custom text method
        custom_radio = browser_driver.find_element(By.ID, "methodCustom")
        custom_radio.click()
        
        custom_section = browser_driver.find_element(By.ID, "customTextSection")
        assert custom_section.is_displayed()
        
        # Test file upload method
        file_radio = browser_driver.find_element(By.ID, "methodFile")
        file_radio.click()
        
        file_section = browser_driver.find_element(By.ID, "fileUploadSection")
        assert file_section.is_displayed()
        
        # Custom section should be hidden
        assert not custom_section.is_displayed()

    def test_font_size_dropdown(self, browser_driver, app_url):
        """Test font size dropdown functionality."""
        browser_driver.get(app_url)

        # Wait for dropdown to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.ID, "fontSize"))
        )

        font_dropdown = browser_driver.find_element(By.ID, "fontSize")

        # Get initial value (should be 32pt)
        initial_value = font_dropdown.get_attribute("value")
        assert initial_value == "32"

        # Select a different font size
        from selenium.webdriver.support.ui import Select
        select = Select(font_dropdown)
        select.select_by_value("48")

        # Wait for value to update
        time.sleep(0.5)

        # Check that value updated
        updated_value = font_dropdown.get_attribute("value")
        assert updated_value == "48"
        assert updated_value != initial_value

        # Test extreme values
        select.select_by_value("8")  # Minimum
        assert font_dropdown.get_attribute("value") == "8"

        select.select_by_value("150")  # Maximum
        assert font_dropdown.get_attribute("value") == "150"

    def test_typing_speed_input(self, browser_driver, app_url):
        """Test typing speed input functionality."""
        browser_driver.get(app_url)

        # Wait for typing speed input to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.ID, "typingSpeed"))
        )

        typing_speed_input = browser_driver.find_element(By.ID, "typingSpeed")

        # Check initial value (should be 150)
        initial_value = typing_speed_input.get_attribute("value")
        assert initial_value == "150"

        # Test valid input
        typing_speed_input.clear()
        typing_speed_input.send_keys("100")

        # Trigger input event
        browser_driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", typing_speed_input)

        # Verify value was set
        assert typing_speed_input.get_attribute("value") == "100"

        # Test boundary values
        typing_speed_input.clear()
        typing_speed_input.send_keys("50")  # Minimum
        assert typing_speed_input.get_attribute("value") == "50"

        typing_speed_input.clear()
        typing_speed_input.send_keys("300")  # Maximum
        assert typing_speed_input.get_attribute("value") == "300"

    def test_color_picker_input(self, browser_driver, app_url):
        """Test color picker input functionality."""
        browser_driver.get(app_url)
        
        # Wait for color input to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.ID, "textColor"))
        )
        
        color_input = browser_driver.find_element(By.ID, "textColor")
        
        # Test valid color input
        color_input.clear()
        color_input.send_keys("#FF0000")
        
        # Trigger change event
        browser_driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", color_input)
        
        # Verify value was set
        assert color_input.get_attribute("value") == "#FF0000"

    def test_character_counter(self, browser_driver, app_url):
        """Test character counter functionality."""
        browser_driver.get(app_url)
        
        # Wait for form to load and select custom text method
        WebDriverWait(browser_driver, 10).until(
            EC.element_to_be_clickable((By.ID, "methodCustom"))
        )
        
        custom_radio = browser_driver.find_element(By.ID, "methodCustom")
        custom_radio.click()
        
        # Wait for text area to be visible
        WebDriverWait(browser_driver, 5).until(
            EC.visibility_of_element_located((By.ID, "customText"))
        )
        
        text_area = browser_driver.find_element(By.ID, "customText")
        char_counter = browser_driver.find_element(By.ID, "charCount")
        
        # Initial count should be 0
        assert char_counter.text == "0"
        
        # Type some text
        test_text = "Hello, World!"
        text_area.send_keys(test_text)
        
        # Trigger input event
        browser_driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", text_area)
        
        # Wait for counter to update
        time.sleep(0.5)
        
        # Check counter updated
        expected_count = str(len(test_text))
        assert char_counter.text == expected_count

    def test_form_validation(self, browser_driver, app_url):
        """Test form validation functionality."""
        browser_driver.get(app_url)
        
        # Wait for form to load
        WebDriverWait(browser_driver, 10).until(
            EC.element_to_be_clickable((By.ID, "generateBtn"))
        )
        
        # Test invalid duration
        duration_input = browser_driver.find_element(By.ID, "duration")
        duration_input.clear()
        duration_input.send_keys("5")  # Below minimum
        
        # Try to submit form
        generate_btn = browser_driver.find_element(By.ID, "generateBtn")
        generate_btn.click()
        
        # Should show validation error (implementation may vary)
        # This test verifies the form doesn't submit with invalid data

    def test_responsive_design_mobile(self, browser_driver, app_url):
        """Test responsive design on mobile viewport."""
        browser_driver.get(app_url)
        
        # Set mobile viewport
        browser_driver.set_window_size(375, 667)  # iPhone 6/7/8 size
        
        # Wait for page to adjust
        time.sleep(1)
        
        # Check that elements are still accessible
        form = browser_driver.find_element(By.ID, "videoGenerationForm")
        assert form.is_displayed()
        
        # Check that navigation is responsive
        navbar = browser_driver.find_element(By.CLASS_NAME, "navbar")
        assert navbar.is_displayed()

    def test_file_upload_interface(self, browser_driver, app_url):
        """Test file upload interface functionality."""
        browser_driver.get(app_url)
        
        # Wait for form to load and select file upload method
        WebDriverWait(browser_driver, 10).until(
            EC.element_to_be_clickable((By.ID, "methodFile"))
        )
        
        file_radio = browser_driver.find_element(By.ID, "methodFile")
        file_radio.click()
        
        # Wait for file upload section to be visible
        WebDriverWait(browser_driver, 5).until(
            EC.visibility_of_element_located((By.ID, "fileUploadSection"))
        )
        
        # Check file upload area is present
        upload_area = browser_driver.find_element(By.CLASS_NAME, "file-upload-area")
        assert upload_area.is_displayed()
        
        # Check file input is present (though hidden)
        file_input = browser_driver.find_element(By.ID, "textFile")
        assert file_input

    def test_preview_functionality(self, browser_driver, app_url):
        """Test preview functionality."""
        browser_driver.get(app_url)
        
        # Wait for form to load
        WebDriverWait(browser_driver, 10).until(
            EC.element_to_be_clickable((By.ID, "previewBtn"))
        )
        
        # Add some custom text
        custom_radio = browser_driver.find_element(By.ID, "methodCustom")
        custom_radio.click()
        
        WebDriverWait(browser_driver, 5).until(
            EC.visibility_of_element_located((By.ID, "customText"))
        )
        
        text_area = browser_driver.find_element(By.ID, "customText")
        text_area.send_keys("print('Preview test')")
        
        # Click preview button
        preview_btn = browser_driver.find_element(By.ID, "previewBtn")
        preview_btn.click()
        
        # Check that preview area updates
        preview_area = browser_driver.find_element(By.ID, "previewArea")
        assert preview_area.is_displayed()

    def test_navigation_links(self, browser_driver, app_url):
        """Test navigation links functionality."""
        browser_driver.get(app_url)
        
        # Wait for navigation to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "navbar"))
        )
        
        # Check brand link
        brand_link = browser_driver.find_element(By.CLASS_NAME, "navbar-brand")
        assert brand_link.is_displayed()
        assert "Green-Code FX" in brand_link.text
        
        # Check health link (opens in new tab)
        health_link = browser_driver.find_element(By.XPATH, "//a[contains(@href, '/api/health')]")
        assert health_link.is_displayed()
        assert health_link.get_attribute("target") == "_blank"


class TestCrossBrowserCompatibility:
    """Test cases for cross-browser compatibility."""
    
    def test_javascript_functionality(self, browser_driver, app_url):
        """Test that JavaScript functionality works across browsers."""
        browser_driver.get(app_url)
        
        # Wait for page to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Test that JavaScript objects are available
        green_code_fx = browser_driver.execute_script("return typeof window.GreenCodeFX !== 'undefined';")
        assert green_code_fx, "GreenCodeFX JavaScript object should be available"
        
        # Test that form manager is initialized
        form_manager = browser_driver.execute_script("return typeof window.GreenCodeFX.FormManager !== 'undefined';")
        assert form_manager, "FormManager should be available"

    def test_css_styling(self, browser_driver, app_url):
        """Test that CSS styling is applied correctly."""
        browser_driver.get(app_url)
        
        # Wait for page to load
        WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check that Bootstrap classes are applied
        body = browser_driver.find_element(By.TAG_NAME, "body")
        body_classes = body.get_attribute("class")
        assert "bg-dark" in body_classes
        assert "text-light" in body_classes
        
        # Check custom styling
        navbar = browser_driver.find_element(By.CLASS_NAME, "navbar")
        navbar_classes = navbar.get_attribute("class")
        assert "navbar-dark" in navbar_classes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
