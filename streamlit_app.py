import streamlit as st
import pandas as pd
from seleniumbase import BaseCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import io
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('app.log'),
                        logging.StreamHandler()
                    ])

class TwitterArchiver(BaseCase):
    def setUp(self, headless=True):
        super().setUp()
        if headless:
            self.headless()
        self.browser = "firefox"

def archive_twitter_profile(driver, handle):
    try:
        logging.info(f"Navigating to https://archive.is/ for {handle}")
        driver.get("https://archive.is/")
        
        logging.info(f"Locating input field for {handle}")
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "url"))
        )
        logging.info(f"Filling in input field with URL for {handle}")
        input_field.send_keys(f"https://twitter.com/{handle}")
        
        logging.info(f"Locating archive button for {handle}")
        archive_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
        )
        logging.info(f"Clicking archive button for {handle}")
        archive_button.click()
        
        # Check if the profile has been archived before
        try:
            logging.info(f"Checking if {handle} has been archived before")
            save_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//input[@value='save']"))
            )
            logging.info(f"{handle} has been archived before, clicking save button")
            save_button.click()
        except:
            logging.info(f"{handle} has not been archived before")
            pass
        
        # Check if the CAPTCHA is present
        try:
            logging.info(f"Checking if CAPTCHA is present for {handle}")
            captcha_checkbox = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "checkbox"))
            )
            logging.info(f"CAPTCHA is present for {handle}, clicking checkbox")
            captcha_checkbox.click()
            # Disable headless mode and recreate the driver
            driver.quit()
            driver = create_driver(headless=False)
            input("Please solve the CAPTCHA manually. Press Enter to continue...")
            # Re-enable headless mode and recreate the driver
            driver.quit()
            driver = create_driver(headless=True)
        except:
            logging.info(f"CAPTCHA is not present for {handle}")
            pass
        
        # Wait for the archiving process to complete
        start_time = time.time()
        while True:
            archived_url = driver.current_url
            if "wip" not in archived_url:
                logging.info(f"Archiving process completed for {handle}")
                break
            elif time.time() - start_time > 180:
                logging.error(f"Archiving process timed out for {handle}")
                raise Exception("Archiving process timed out")
            else:
                time.sleep(1)
        
        return archived_url
    
    except Exception as e:
        logging.error(f"Error archiving {handle}: {str(e)}")
        return None


@st.cache(allow_output_mutation=True)
def create_archiver(headless=True):
    archiver = TwitterArchiver()
    archiver.setUp(headless=headless)
    return archiver

def main():
    st.title("Twitter Archive App")
    
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])
    
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df["archived_url"] = ""

        if 'archiver' not in st.session_state:
            st.session_state.archiver = create_archiver()

        archiver = st.session_state.archiver

        progress_bar = st.progress(0)
        status_text = st.empty()

        for index, row in df.iterrows():
            handle = row["handle"]
            status_text.text(f"Processing handle: {handle}")

            archived_url = archiver.archive_twitter_profile(handle)

            if archived_url:
                df.at[index, "archived_url"] = archived_url
                logging.info(f"Archived URL for {handle}: {archived_url}")
            else:
                logging.error(f"Failed to archive {handle}")

            progress_bar.progress((index + 1) / len(df))

            wait_time = random.uniform(2, 5)
            status_text.text(f"Waiting for {wait_time:.2f} seconds before processing the next handle...")
            time.sleep(wait_time)

        archiver.tearDown()
        st.session_state.archiver = None

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        st.download_button(
            label="Download Updated Excel",
            data=output,
            file_name='handles_archived.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

if __name__ == '__main__':
    main()
