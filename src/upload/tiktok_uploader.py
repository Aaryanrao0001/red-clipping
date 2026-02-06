"""
TikTok Uploader - Selenium automation for TikTok
"""
import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)


class TikTokUploader:
    """Upload videos to TikTok using Selenium"""
    
    def __init__(self, browser_manager, credential_manager):
        """
        Initialize TikTok uploader
        
        Args:
            browser_manager: BrowserManager instance
            credential_manager: CredentialManager instance
        """
        self.browser_manager = browser_manager
        self.credential_manager = credential_manager
        self.platform = 'tiktok'
        self.base_url = 'https://www.tiktok.com'
    
    def login(self, driver):
        """
        Login to TikTok
        
        Args:
            driver: WebDriver instance
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Logging in to TikTok")
        
        # Get credentials
        creds = self.credential_manager.get_credentials(self.platform)
        username = creds.get('username')
        password = creds.get('password')
        
        if not username or not password:
            logger.error("TikTok credentials not found")
            return False
        
        try:
            # Navigate to TikTok
            driver.get(f"{self.base_url}/login")
            time.sleep(3)
            
            # Handle cookie consent
            self.browser_manager.handle_cookie_consent(driver)
            
            # Click "Use phone / email / username"
            try:
                email_login_option = self.browser_manager.wait_for_clickable(
                    driver, By.XPATH, 
                    "//div[contains(text(), 'Use phone / email / username')]|//a[contains(text(), 'Use phone / email / username')]"
                )
                if email_login_option:
                    self.browser_manager.safe_click(driver, email_login_option)
                    time.sleep(2)
            except:
                pass
            
            # Click on "Log in with email or username"
            try:
                username_option = self.browser_manager.wait_for_clickable(
                    driver, By.XPATH, 
                    "//a[contains(text(), 'Log in with email or username')]"
                )
                if username_option:
                    self.browser_manager.safe_click(driver, username_option)
                    time.sleep(2)
            except:
                pass
            
            # Enter username
            username_input = self.browser_manager.wait_for_element(
                driver, By.XPATH, 
                "//input[@type='text'][@placeholder='Email or username']"
            )
            if username_input:
                self.browser_manager.safe_send_keys(username_input, username)
                time.sleep(1)
            
            # Enter password
            password_input = driver.find_element(
                By.XPATH, 
                "//input[@type='password']"
            )
            if password_input:
                self.browser_manager.safe_send_keys(password_input, password)
                time.sleep(1)
            
            # Click login button
            login_button = driver.find_element(
                By.XPATH, 
                "//button[@type='submit']"
            )
            self.browser_manager.safe_click(driver, login_button)
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            try:
                # Look for upload button or user avatar
                driver.find_element(By.XPATH, "//a[contains(@href, '/upload')]|//div[@data-e2e='profile-icon']")
                logger.info("TikTok login successful")
                return True
            except NoSuchElementException:
                logger.error("Login failed - home page elements not found")
                return False
        
        except Exception as e:
            logger.error(f"TikTok login failed: {e}")
            return False
    
    def upload_video(self, driver, video_path, caption, hashtags=None):
        """
        Upload a video to TikTok
        
        Args:
            driver: WebDriver instance
            video_path: Path to video file
            caption: Caption text
            hashtags: Optional list of hashtags
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Uploading video to TikTok: {video_path}")
        
        try:
            # Navigate to upload page
            driver.get(f"{self.base_url}/upload")
            time.sleep(3)
            
            # Select file
            file_input = self.browser_manager.wait_for_element(
                driver, By.XPATH, 
                "//input[@type='file']"
            )
            if not file_input:
                logger.error("File input not found")
                return False
            
            file_input.send_keys(os.path.abspath(video_path))
            logger.info("Video file selected, uploading...")
            time.sleep(5)
            
            # Wait for upload to process
            logger.info("Waiting for video to process...")
            time.sleep(10)
            
            # Add caption
            caption_field = self.browser_manager.wait_for_element(
                driver, By.XPATH, 
                "//div[@contenteditable='true'][@data-text='placeholder']|//div[@role='textbox']"
            )
            
            if caption_field:
                # Format caption with hashtags
                full_caption = caption
                if hashtags:
                    hashtag_str = ' '.join(['#' + tag for tag in hashtags])
                    full_caption = f"{caption}\n\n{hashtag_str}"
                
                # TikTok has specific requirements - hashtags should be integrated
                self.browser_manager.safe_send_keys(caption_field, full_caption, clear_first=True)
                time.sleep(2)
            
            # Set who can view (Public)
            try:
                public_option = self.browser_manager.wait_for_clickable(
                    driver, By.XPATH, 
                    "//div[contains(text(), 'Public')]"
                )
                if public_option:
                    self.browser_manager.safe_click(driver, public_option)
                    time.sleep(1)
            except:
                logger.warning("Could not set public visibility")
            
            # Allow comments (optional)
            try:
                allow_comments = driver.find_element(
                    By.XPATH, 
                    "//div[contains(text(), 'Allow comments')]//input[@type='checkbox']"
                )
                if not allow_comments.is_selected():
                    self.browser_manager.safe_click(driver, allow_comments)
                    time.sleep(1)
            except:
                pass
            
            # Click Post button
            post_button = self.browser_manager.wait_for_clickable(
                driver, By.XPATH, 
                "//button[contains(text(), 'Post')]"
            )
            
            if post_button:
                self.browser_manager.safe_click(driver, post_button)
                logger.info("Clicked post button")
                
                # Wait for upload to complete
                time.sleep(10)
                
                # Check for success
                try:
                    success_indicator = driver.find_element(
                        By.XPATH, 
                        "//div[contains(text(), 'Your video is being uploaded')]|//div[contains(text(), 'Your video has been uploaded')]"
                    )
                    logger.info("TikTok video uploaded successfully")
                    return True
                except NoSuchElementException:
                    logger.warning("Success indicator not found, but upload may have succeeded")
                    return True
            else:
                logger.error("Post button not found")
                return False
        
        except Exception as e:
            logger.error(f"TikTok upload failed: {e}")
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
            
            # Upload video
            success = self.upload_video(driver, video_path, caption, hashtags)
            
            return success
        
        finally:
            # Close driver
            driver.quit()
