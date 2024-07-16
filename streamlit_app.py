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
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('app.log'),
                        logging.StreamHandler()
                    ])

@st.cache(allow_output_mutation=True)
def create_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless")  # Run Firefox in headless mode
    driver = webdriver.Firefox(options=options)
    return driver

def archive_twitter_profile(driver, handle):
    # ... (same as before) ...

def main():
    st.title("Twitter Archive App")
    
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])
    
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df["archived_url"] = ""

        if 'driver' not in st.session_state:
            st.session_state.driver = create_driver()

        driver = st.session_state.driver

        progress_bar = st.progress(0)
        status_text = st.empty()

        for index, row in df.iterrows():
            handle = row["handle"]
            status_text.text(f"Processing handle: {handle}")

            archived_url = archive_twitter_profile(driver, handle)

            if archived_url:
                df.at[index, "archived_url"] = archived_url
                logging.info(f"Archived URL for {handle}: {archived_url}")
            else:
                logging.error(f"Failed to archive {handle}")

            progress_bar.progress((index + 1) / len(df))

            wait_time = random.uniform(2, 5)
            status_text.text(f"Waiting for {wait_time:.2f} seconds before processing the next handle...")
            time.sleep(wait_time)

        driver.quit()
        st.session_state.driver = None

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
