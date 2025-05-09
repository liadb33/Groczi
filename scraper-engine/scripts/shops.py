import os
import json
import shutil
import logging
import gzip
import zipfile
import time
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from selenium.common.exceptions import WebDriverException, TimeoutException
# Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from requests.exceptions import RequestException

# === PATHS AND CONSTANTS ===
SCRIPT_DIR = Path(__file__).parent.resolve()
SHOPS_JSON_FILE = SCRIPT_DIR.parent / "configs" / "shop.json"
GZ_FOLDER_PATH = SCRIPT_DIR.parent / "output" / "gzFiles"
XML_FOLDER_GROCERY_PATH = SCRIPT_DIR.parent / "output" / "groceries"
XML_FOLDER_STORE_PATH = SCRIPT_DIR.parent / "output" / "stores"
XML_FOLDER_PROMOTION_PATH = SCRIPT_DIR.parent / "output" / "promotions"
XML_OTHERS_FOLDER_PATH = SCRIPT_DIR.parent / "output" / "others"

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M'
)

# === HELPER FUNCTIONS ===
def load_config(file_path: str | Path) -> dict:
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"❌ Configuration file not found: '{file_path}'")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"❌ Failed to decode JSON from '{file_path}': {e}")
        raise
    except Exception as e:
        logging.error(f"❌ Failed to load config '{file_path}': {type(e).name} - {e}")
        raise

def access_site(driver: webdriver.Chrome, url: str,config: dict) -> bool:
    logging.info(f"Accessing site: {url}")
    try:
        driver.get(url)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, config["wait_for_selector"]))
        )

        logging.info(f"✅ Found table.")
        return True
    except TimeoutException:
        logging.error(f"❌ Timed out waiting for site confirmation")
        return False
    except WebDriverException as e:
        logging.error(f"❌ Site access failed {e}")
        return False    
    except Exception as e:
        logging.error(f"❌ Error accessing {url}: {e}")
        return False

def fetch_all_file_entries(driver: webdriver.Chrome,config: dict) -> None:
    res = fetch_file_list(driver,config)
    while not res:
        try:
            page_il = driver.find_element(By.CSS_SELECTOR, config["pagination_selector"])
            if page_il:
                page_il.click()
                WebDriverWait(driver, 10).until(EC.staleness_of(driver.find_element(By.TAG_NAME, "table")))
            else:
                break
        except Exception as e:
            logging.info("No next page found or error clicking next page; ending pagination.")
            break
     
def fetch_file_list(driver: webdriver.Chrome,config: dict) -> bool:
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, config["row_selector"])  
        current_hour = datetime.now().hour - 1
        for row in rows:            
            timestamp = row.find_element(By.CSS_SELECTOR, config["timestamp_selector"])
            file_hour = get_file_hour(timestamp.text)  
            if file_hour != current_hour:
                return True
            download_link = row.find_element(By.CSS_SELECTOR, config["link_config"])
            download_link.click()
            logging.info(f"⬇️ Downloading")
            wait_for_download_complete(GZ_FOLDER_PATH)
    except Exception as e:
         logging.error(f"❌ Error fetching file list: {e}")
         return False
    return False

def wait_for_download_complete(folder: Path, timeout: int = 60) -> bool:
    logging.info("⏳ Waiting for download to complete...")
    elapsed = 0
    while elapsed < timeout:
        files = list(folder.glob("*.crdownload"))
        if not files:
            logging.info("✅ Download finished.")
            return True
        time.sleep(1)
        elapsed += 1
    logging.warning("⚠️ Download may not have completed in time.")
    return False


def get_file_hour(timestamp_text: str) -> int:
    formats = [
        "%H:%M",                      
        "%m/%d/%Y %I:%M:%S %p",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%H:%M %d/%m/%Y",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(timestamp_text, fmt)
            return dt.hour
        except ValueError:
            continue
    raise ValueError(f"Unrecognized timestamp format: {timestamp_text}")

def extract(username: str) -> None:
    """Extracts .gz or .zip files from GZ_FOLDER_PATH to the given folder."""
    
    gz_files = list(Path(GZ_FOLDER_PATH).glob("*.gz"))
    if not gz_files:
        logging.warning("⚠️ No .gz files found to extract.")
        return
    
    for gz_path in gz_files:
        try:
            with open(gz_path, "rb") as f:
                magic = f.read(2)
                f.seek(0)  # Reset file pointer

                file_name_gz = gz_path.name
                
                user_xml_folder = (
                    XML_FOLDER_GROCERY_PATH if "price" in file_name_gz.lower() else
                    XML_FOLDER_STORE_PATH if "store" in file_name_gz.lower() else
                    XML_FOLDER_PROMOTION_PATH if "promo" in file_name_gz.lower() else
                    XML_OTHERS_FOLDER_PATH
                )

                file_name_xml = file_name_gz + ".xml"
                extracted_path = user_xml_folder / username / file_name_xml
                extracted_path.parent.mkdir(parents=True, exist_ok=True)

                if magic == b'\x1f\x8b':  # GZIP magic number
                    with gzip.open(f, "rb") as f_gzip, open(extracted_path, "wb") as f_xml:
                        shutil.copyfileobj(f_gzip, f_xml)

                elif magic == b'PK':  # ZIP file magic number
                    with zipfile.ZipFile(f) as z:
                        for zipped_file in z.namelist():
                            # Extract the first file in the zip
                            with z.open(zipped_file) as zip_file, open(extracted_path, 'wb') as out_file:
                                shutil.copyfileobj(zip_file, out_file)

                else:
                    raise ValueError("Unknown file format")

            logging.info(f"✅ Extracted & removed: {file_name_gz}") 
        except Exception as e:
            logging.error(f"❌ Failed to extract {gz_path}: {type(e).__name__} - {e}")

# === MAIN FLOW ===
def main():
    try:
        config = load_config(SHOPS_JSON_FILE)
    except Exception:
        logging.critical("Failed to load configuration. Exiting.")
        return
    
    driver = None
    try:
        logging.info("Initializing WebDriver")
        options = Options()
        options.add_argument("--headless") 
        prefs = {
            "download.default_directory": str(GZ_FOLDER_PATH),  # Set the default download directory
            "download.prompt_for_download": False,  # disables the "Save As" dialog
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True  # avoid security prompts
        }
        options.add_experimental_option("prefs", prefs) 
        driver = webdriver.Chrome(options=options)
        logging.info("WebDriver initialized.")
        users = config.get("users", [])
        for user in users:
            os.makedirs(GZ_FOLDER_PATH, exist_ok=True)
            site_url = user.get("url", "").strip()
            if not site_url:
                logging.warning("⚠️ No 'url' found in user entry; skipping.")
                continue

            logging.info(f"\n===== PROCESSING: {site_url} =====")
            if not access_site(driver, site_url, user["config"]):
                logging.error(f"Skipping {site_url} due to site access failure.")
                continue

            fetch_all_file_entries(driver,user["config"])

            extract(user.get("username", ""))
            os.shutil.rmtree(GZ_FOLDER_PATH)
            logging.info(f"===== FINISHED: {site_url} =====")
    except Exception as e:
        logging.critical(f"An unexpected error occurred in main: {e}", exc_info=True)
    finally:
        if driver:
            logging.info("Closing WebDriver...")
            driver.quit()
            logging.info("WebDriver closed.")

if __name__ == "__main__":
    main()
