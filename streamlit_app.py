import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import time
import random
import io
import logging

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def create_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless")  # Run Firefox in headless mode
    driver = webdriver.Firefox(options=options)
    return driver

def archive_twitter_profile(driver, handle):
    try:
        driver.get("https://archive.is/")
        
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "url"))
        )
        input_field.send_keys(f"https://twitter.com/{handle}")
        
        archive_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
        )
        archive_button.click()
        
        # Check if the profile has been archived before
        try:
            save_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//input[@value='save']"))
            )
            save_button.click()
        except:
            pass
        
        # Check if the CAPTCHA is present
        try:
            captcha_checkbox = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "checkbox"))
            )
            captcha_checkbox.click()
            # Disable headless mode and recreate the driver
            driver.quit()
            driver = create_driver(headless=False)
            input("Please solve the CAPTCHA manually. Press Enter to continue...")
            # Re-enable headless mode and recreate the driver
            driver.quit()
            driver = create_driver(headless=True)
        except:
            pass
        
        # Wait for the archiving process to complete
        start_time = time.time()
        while True:
            archived_url = driver.current_url
            if "wip" not in archived_url:
                break
            elif time.time() - start_time > 180:
                raise Exception("Archiving process timed out")
            else:
                time.sleep(1)
        
        return archived_url
    
    except Exception as e:
        logging.error(f"Error archiving {handle}: {str(e)}")
        return None

def main():
    st.title("Twitter Archive App")
    
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])
    
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df["archived_url"] = ""

        driver = create_driver()

        for index, row in df.iterrows():
            handle = row["handle"]
            st.write(f"Processing handle: {handle}")

            archived_url = archive_twitter_profile(driver, handle)

            if archived_url:
                df.at[index, "archived_url"] = archived_url
                st.write(f"Archived URL for {handle}: {archived_url}")
            else:
                st.write(f"Failed to archive {handle}")
                logging.error(f"Failed to archive {handle}")

            wait_time = random.uniform(2, 5)
            st.write(f"Waiting for {wait_time:.2f} seconds before processing the next handle...")
            time.sleep(wait_time)

        driver.quit()

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
