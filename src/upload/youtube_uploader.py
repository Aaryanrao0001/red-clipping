"""
YouTube Uploader - Selenium automation for YouTube Shorts
"""
import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)


class YouTubeUploader:
    """Upload videos to YouTube Shorts using Selenium"""
    
    def __init__(self, browser_manager, credential_manager):
        """
        Initialize YouTube uploader
        
        Args:
            browser_manager: BrowserManager instance
            credential_manager: CredentialManager instance
        """
        self.browser_manager = browser_manager
        self.credential_manager = credential_manager
        self.platform = 'youtube'
        self.base_url = 'https://studio.youtube.com'
    
    def login(self, driver):
        """
        Login to YouTube
        
        Args:
            driver: WebDriver instance
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Logging in to YouTube")
        
        # Get credentials
        creds = self.credential_manager.get_credentials(self.platform)
        email = creds.get('email')
        password = creds.get('password')
        
        if not email or not password:
            logger.error("YouTube credentials not found")
            return False
        
        try:
            # Navigate to YouTube Studio
            driver.get(f"{self.base_url}")
            time.sleep(3)
            
            # Check if already logged in
            try:
                driver.find_element(By.XPATH, "//ytcp-button[@id='create-icon']")
                logger.info("Already logged in to YouTube")
                return True
            except NoSuchElementException:
                pass
            
            # Click Sign In
            try:
                sign_in_button = self.browser_manager.wait_for_clickable(
                    driver, By.XPATH, 
                    "//a[contains(@href, 'accounts.google.com')]"
                )
                if sign_in_button:
                    self.browser_manager.safe_click(driver, sign_in_button)
                    time.sleep(2)
            except:
                pass
            
            # Enter email
            email_input = self.browser_manager.wait_for_element(
                driver, By.XPATH, 
                "//input[@type='email']"
            )
            if email_input:
                self.browser_manager.safe_send_keys(email_input, email)
                time.sleep(1)
                email_input.send_keys(Keys.RETURN)
                time.sleep(3)
            
            # Enter password
            password_input = self.browser_manager.wait_for_element(
                driver, By.XPATH, 
                "//input[@type='password']"
            )
            if password_input:
                self.browser_manager.safe_send_keys(password_input, password)
                time.sleep(1)
                password_input.send_keys(Keys.RETURN)
                time.sleep(5)
            
            # Check if login was successful
            try:
                driver.find_element(By.XPATH, "//ytcp-button[@id='create-icon']")
                logger.info("YouTube login successful")
                return True
            except NoSuchElementException:
                logger.error("Login failed - create button not found")
                return False
        
        except Exception as e:
            logger.error(f"YouTube login failed: {e}")
            return False
    
    def upload_short(self, driver, video_path, title, description, hashtags=None):
        """
        Upload a short to YouTube
        
        Args:
            driver: WebDriver instance
            video_path: Path to video file
            title: Video title
            description: Video description
            hashtags: Optional list of hashtags
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Uploading short to YouTube: {video_path}")
        
        try:
            # Navigate to YouTube Studio
            driver.get(f"{self.base_url}")
            time.sleep(3)
            
            # Click Create button
            create_button = self.browser_manager.wait_for_clickable(
                driver, By.XPATH, 
                "//ytcp-button[@id='create-icon']"
            )
            if not create_button:
                logger.error("Create button not found")
                return False
            
            self.browser_manager.safe_click(driver, create_button)
            time.sleep(2)
            
            # Click Upload videos
            upload_option = self.browser_manager.wait_for_clickable(
                driver, By.XPATH, 
                "//tp-yt-paper-item[@test-id='upload-beta']"
            )
            if upload_option:
                self.browser_manager.safe_click(driver, upload_option)
                time.sleep(2)
            
            # Select file
            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            file_input.send_keys(os.path.abspath(video_path))
            logger.info("Video file selected, uploading...")
            time.sleep(5)
            
            # Wait for upload to process
            time.sleep(10)
            
            # Add title
            title_field = self.browser_manager.wait_for_element(
                driver, By.XPATH, 
                "//div[@id='textbox'][@aria-label='Title']"
            )
            if title_field:
                # Use caption as title if no title provided
                if not title:
                    title = "YouTube Short"
                
                self.browser_manager.safe_send_keys(title_field, title, clear_first=True)
                time.sleep(1)
            
            # Add description
            description_field = driver.find_element(
                By.XPATH, 
                "//div[@id='textbox'][@aria-label='Description']"
            )
            if description_field:
                # Format description with hashtags
                full_description = description
                if hashtags:
                    # Limit hashtags for YouTube (max 15)
                    limited_hashtags = hashtags[:15]
                    hashtag_str = ' '.join(['#' + tag for tag in limited_hashtags])
                    full_description = f"{description}\n\n{hashtag_str}"
                
                self.browser_manager.safe_send_keys(description_field, full_description, clear_first=True)
                time.sleep(2)
            
            # Mark as "Not made for kids" (required step)
            try:
                not_for_kids = self.browser_manager.wait_for_clickable(
                    driver, By.NAME, 
                    "VIDEO_MADE_FOR_KIDS_NOT_MFK"
                )
                if not_for_kids:
                    self.browser_manager.safe_click(driver, not_for_kids)
                    time.sleep(1)
            except:
                logger.warning("Could not set 'not for kids' option")
            
            # Click Next button multiple times
            for i in range(3):
                try:
                    next_button = self.browser_manager.wait_for_clickable(
                        driver, By.XPATH, 
                        "//ytcp-button[@id='next-button']"
                    )
                    if next_button:
                        self.browser_manager.safe_click(driver, next_button)
                        time.sleep(2)
                except:
                    break
            
            # Set visibility to Public
            try:
                public_option = self.browser_manager.wait_for_clickable(
                    driver, By.NAME, 
                    "PUBLIC"
                )
                if public_option:
                    self.browser_manager.safe_click(driver, public_option)
                    time.sleep(1)
            except:
                logger.warning("Could not set public visibility")
            
            # Click Publish button
            publish_button = self.browser_manager.wait_for_clickable(
                driver, By.XPATH, 
                "//ytcp-button[@id='done-button']"
            )
            if publish_button:
                self.browser_manager.safe_click(driver, publish_button)
                logger.info("Clicked publish button")
                time.sleep(5)
                
                logger.info("YouTube short uploaded successfully")
                return True
            else:
                logger.error("Publish button not found")
                return False
        
        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
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
            
            # Upload short
            # Use first line of caption as title
            title_lines = caption.split('\n')
            title = title_lines[0][:100] if title_lines else "YouTube Short"
            
            success = self.upload_short(driver, video_path, title, caption, hashtags)
            
            return success
        
        finally:
            # Close driver
            driver.quit()
