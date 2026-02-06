"""
Instagram Uploader - Selenium automation for Instagram Reels
"""
import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)


class InstagramUploader:
    """Upload videos to Instagram Reels using Selenium"""
    
    def __init__(self, browser_manager, credential_manager):
        """
        Initialize Instagram uploader
        
        Args:
            browser_manager: BrowserManager instance
            credential_manager: CredentialManager instance
        """
        self.browser_manager = browser_manager
        self.credential_manager = credential_manager
        self.platform = 'instagram'
        self.base_url = 'https://www.instagram.com'
    
    def login(self, driver):
        """
        Login to Instagram
        
        Args:
            driver: WebDriver instance
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Logging in to Instagram")
        
        # Get credentials
        creds = self.credential_manager.get_credentials(self.platform)
        username = creds.get('username')
        password = creds.get('password')
        
        if not username or not password:
            logger.error("Instagram credentials not found")
            return False
        
        try:
            # Navigate to login page
            driver.get(f"{self.base_url}/accounts/login/")
            time.sleep(3)
            
            # Handle cookie consent
            self.browser_manager.handle_cookie_consent(driver)
            
            # Wait for and fill username
            username_input = self.browser_manager.wait_for_element(
                driver, By.NAME, 'username'
            )
            if not username_input:
                logger.error("Username field not found")
                return False
            
            self.browser_manager.safe_send_keys(username_input, username)
            time.sleep(1)
            
            # Fill password
            password_input = driver.find_element(By.NAME, 'password')
            self.browser_manager.safe_send_keys(password_input, password)
            time.sleep(1)
            
            # Click login button
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            self.browser_manager.safe_click(driver, login_button)
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful (look for home page elements)
            try:
                driver.find_element(By.XPATH, "//a[contains(@href, '/direct/')]")
                logger.info("Instagram login successful")
                return True
            except NoSuchElementException:
                logger.error("Login failed - home page elements not found")
                return False
        
        except Exception as e:
            logger.error(f"Instagram login failed: {e}")
            return False
    
    def upload_reel(self, driver, video_path, caption, hashtags=None):
        """
        Upload a reel to Instagram
        
        Args:
            driver: WebDriver instance
            video_path: Path to video file
            caption: Caption text
            hashtags: Optional list of hashtags
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Uploading reel to Instagram: {video_path}")
        
        try:
            # Navigate to home page
            driver.get(self.base_url)
            time.sleep(3)
            
            # Click on Create button (+ icon)
            create_button = self.browser_manager.wait_for_clickable(
                driver, By.XPATH, 
                "//a[contains(@href, '/create/')]|//svg[@aria-label='New post']/.."
            )
            
            if not create_button:
                logger.error("Create button not found")
                return False
            
            self.browser_manager.safe_click(driver, create_button)
            time.sleep(2)
            
            # Look for file input
            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            file_input.send_keys(os.path.abspath(video_path))
            time.sleep(3)
            
            # Wait for video to upload
            logger.info("Waiting for video to upload...")
            time.sleep(5)
            
            # Click Next button (may need to click multiple times)
            for _ in range(3):
                try:
                    next_button = self.browser_manager.wait_for_clickable(
                        driver, By.XPATH, 
                        "//button[contains(text(), 'Next')]"
                    )
                    if next_button:
                        self.browser_manager.safe_click(driver, next_button)
                        time.sleep(2)
                except:
                    break
            
            # Add caption
            caption_field = self.browser_manager.wait_for_element(
                driver, By.XPATH, 
                "//textarea[@aria-label='Write a caption...']|//div[@aria-label='Write a caption...']"
            )
            
            if caption_field:
                # Format caption with hashtags
                full_caption = caption
                if hashtags:
                    hashtag_str = ' '.join(['#' + tag for tag in hashtags])
                    full_caption = f"{caption}\n\n{hashtag_str}"
                
                self.browser_manager.safe_send_keys(caption_field, full_caption, clear_first=False)
                time.sleep(2)
            
            # Share/Post button
            share_button = self.browser_manager.wait_for_clickable(
                driver, By.XPATH, 
                "//button[contains(text(), 'Share')]|//button[contains(text(), 'Post')]"
            )
            
            if share_button:
                self.browser_manager.safe_click(driver, share_button)
                logger.info("Clicked share button")
                
                # Wait for upload to complete
                time.sleep(10)
                
                # Check for success message
                try:
                    success_indicator = driver.find_element(
                        By.XPATH, 
                        "//span[contains(text(), 'Your reel has been shared')]|//span[contains(text(), 'Post shared')]"
                    )
                    logger.info("Instagram reel uploaded successfully")
                    return True
                except NoSuchElementException:
                    logger.warning("Success indicator not found, but upload may have succeeded")
                    return True
            else:
                logger.error("Share button not found")
                return False
        
        except Exception as e:
            logger.error(f"Instagram upload failed: {e}")
            return False
    
    def upload(self, upload_task):
        """
        Main upload method for scheduler integration
        
        Args:
            upload_task: Upload task dictionary
            
        Returns:
            True if successful, False otherwise
        """
        video_path = upload_task.get('clip_path')
        metadata = upload_task.get('metadata', {})
        caption = metadata.get('caption', '')
        hashtags = metadata.get('hashtags', [])
        
        # Create driver
        driver = self.browser_manager.create_driver(profile_name=self.platform)
        
        try:
            # Login
            if not self.login(driver):
                return False
            
            # Upload reel
            success = self.upload_reel(driver, video_path, caption, hashtags)
            
            return success
        
        finally:
            # Close driver
            driver.quit()
