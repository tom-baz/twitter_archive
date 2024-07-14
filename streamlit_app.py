import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

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
            input("Please solve the CAPTCHA manually in the browser window. Press Enter to continue...")
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
        st.write(f"Error archiving {handle}: {str(e)}")
        return None

def main():
    st.title("Twitter Handle Archiver")
    
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
    
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.write("Uploaded Excel file:")
        st.write(df)
        
        if 'handle' in df.columns:
            handles = df['handle'].tolist()
            st.write("Processing handles...")
            
            # Set up the webdriver
            driver = webdriver.Chrome(ChromeDriverManager().install())
            
            archived_urls = []
            for handle in handles:
                st.write(f"Processing handle: {handle}")
                archived_url = archive_twitter_profile(driver, handle)
                archived_urls.append(archived_url)
                if archived_url:
                    st.write(f"Archived URL for {handle}: {archived_url}")
                wait_time = random.uniform(2, 5)
                st.write(f"Waiting for {wait_time:.2f} seconds before processing the next handle...")
                time.sleep(wait_time)
            
            driver.quit()
            
            df['archived_url'] = archived_urls
            
            st.write("Processed DataFrame with Archived URLs:")
            st.write(df)
            
            output_file = "handles_archived.xlsx"
            df.to_excel(output_file, index=False)
            st.download_button(
                label="Download Excel file with archived URLs",
                data=open(output_file, "rb").read(),
                file_name=output_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("The Excel file must contain a column named 'handle'.")
    
if __name__ == "__main__":
    main()
