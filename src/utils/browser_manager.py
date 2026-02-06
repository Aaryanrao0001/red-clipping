"""
Browser Manager - Manage undetected-chromedriver sessions and profiles
"""
import os
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manage browser sessions for platform uploads"""
    
    def __init__(self, config):
        """
        Initialize browser manager
        
        Args:
            config: Browser configuration dictionary
        """
        self.config = config
        self.driver = None
        self.user_data_dir = config.get('user_data_dir', 'cache/browser_profiles')
        self.headless = config.get('headless', False)
        self.page_load_timeout = config.get('page_load_timeout', 30)
        self.element_wait_timeout = config.get('element_wait_timeout', 20)
        self.implicit_wait = config.get('implicit_wait', 10)
        
        # Ensure user data directory exists
        os.makedirs(self.user_data_dir, exist_ok=True)
    
    def create_driver(self, profile_name=None):
        """
        Create a new undetected Chrome driver instance
        
        Args:
            profile_name: Optional profile name for persistent sessions
            
        Returns:
            WebDriver instance
        """
        options = uc.ChromeOptions()
        
        # Set user data directory for persistent sessions
        if profile_name:
            profile_dir = os.path.join(self.user_data_dir, profile_name)
            os.makedirs(profile_dir, exist_ok=True)
            options.add_argument(f'--user-data-dir={profile_dir}')
        
        # Headless mode (note: some platforms may detect headless browsers)
        if self.headless:
            options.add_argument('--headless=new')
        
        # Additional options to avoid detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # User agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            driver = uc.Chrome(options=options, version_main=None)
            
            # Set timeouts
            driver.set_page_load_timeout(self.page_load_timeout)
            driver.implicitly_wait(self.implicit_wait)
            
            # Execute CDP commands to hide automation
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info(f"Created browser driver with profile: {profile_name or 'default'}")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to create browser driver: {e}")
            raise
    
    def get_driver(self, platform=None):
        """
        Get or create driver for specific platform
        
        Args:
            platform: Platform name for profile selection
            
        Returns:
            WebDriver instance
        """
        if self.driver is None:
            self.driver = self.create_driver(profile_name=platform)
        return self.driver
    
    def close_driver(self):
        """Close the current driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Closed browser driver")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
            finally:
                self.driver = None
    
    def wait_for_element(self, driver, by, value, timeout=None):
        """
        Wait for element to be present and visible
        
        Args:
            driver: WebDriver instance
            by: Locator strategy (By.ID, By.XPATH, etc.)
            value: Locator value
            timeout: Optional timeout override
            
        Returns:
            WebElement or None
        """
        timeout = timeout or self.element_wait_timeout
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.warning(f"Timeout waiting for element: {by}={value}")
            return None
    
    def wait_for_clickable(self, driver, by, value, timeout=None):
        """
        Wait for element to be clickable
        
        Args:
            driver: WebDriver instance
            by: Locator strategy
            value: Locator value
            timeout: Optional timeout override
            
        Returns:
            WebElement or None
        """
        timeout = timeout or self.element_wait_timeout
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            logger.warning(f"Timeout waiting for clickable element: {by}={value}")
            return None
    
    def safe_click(self, driver, element, retry_count=3):
        """
        Safely click an element with retry logic
        
        Args:
            driver: WebDriver instance
            element: WebElement to click
            retry_count: Number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(retry_count):
            try:
                # Scroll element into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)
                
                # Try to click
                element.click()
                return True
                
            except Exception as e:
                logger.warning(f"Click attempt {attempt + 1} failed: {e}")
                
                if attempt < retry_count - 1:
                    # Try JavaScript click as fallback
                    try:
                        driver.execute_script("arguments[0].click();", element)
                        return True
                    except Exception as js_e:
                        logger.warning(f"JavaScript click failed: {js_e}")
                        time.sleep(1)
        
        return False
    
    def safe_send_keys(self, element, text, clear_first=True, retry_count=3):
        """
        Safely send keys to an element with retry logic
        
        Args:
            element: WebElement
            text: Text to send
            clear_first: Clear element before sending keys
            retry_count: Number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(retry_count):
            try:
                if clear_first:
                    element.clear()
                    time.sleep(0.3)
                
                element.send_keys(text)
                return True
                
            except Exception as e:
                logger.warning(f"Send keys attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    time.sleep(1)
        
        return False
    
    def switch_to_new_tab(self, driver):
        """
        Switch to newly opened tab
        
        Args:
            driver: WebDriver instance
        """
        # Wait for new tab to open
        time.sleep(2)
        
        # Get all window handles
        handles = driver.window_handles
        
        # Switch to the last opened window
        if len(handles) > 1:
            driver.switch_to.window(handles[-1])
            logger.info("Switched to new tab")
    
    def close_extra_tabs(self, driver):
        """
        Close all tabs except the first one
        
        Args:
            driver: WebDriver instance
        """
        handles = driver.window_handles
        
        # Keep only the first tab
        for i in range(len(handles) - 1, 0, -1):
            driver.switch_to.window(handles[i])
            driver.close()
        
        # Switch back to first tab
        driver.switch_to.window(handles[0])
        logger.info("Closed extra tabs")
    
    def handle_cookie_consent(self, driver):
        """
        Try to handle common cookie consent dialogs
        
        Args:
            driver: WebDriver instance
        """
        # Common cookie consent button selectors
        consent_selectors = [
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'Accept all')]",
            "//button[contains(text(), 'I agree')]",
            "//button[@id='accept']",
            "//button[@class*='accept']",
        ]
        
        for selector in consent_selectors:
            try:
                button = self.wait_for_clickable(driver, By.XPATH, selector, timeout=5)
                if button:
                    self.safe_click(driver, button)
                    logger.info("Accepted cookie consent")
                    time.sleep(1)
                    break
            except:
                pass
    
    def take_screenshot(self, driver, filename):
        """
        Take a screenshot
        
        Args:
            driver: WebDriver instance
            filename: Output filename
        """
        try:
            driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
