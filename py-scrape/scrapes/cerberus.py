import os
import json
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# Constants #
json_file_path = "../jsons/cerberus.json"
base_folder = "C:\\Users\\hassh\\OneDrive\\שולחן העבודה\\Projects\\groczi\\py-scrape\\scrapes\\files"

####### function to find files #######
def find_files(driver):
    # Get the current date and format it as YYYYMMDD
    current_date = datetime.now().strftime("%Y%m%d")
    print(f"Searching for files from the current date: {current_date}")
    ####### Locate the search bar and enter the formatted date ########
    search_bar = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@type='search']")))
    search_bar.clear()
    search_bar.send_keys(current_date)
    search_bar.submit()

    # Scroll to the bottom of the page to load all files
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        current_height = driver.execute_script("return document.body.scrollHeight")
        if current_height == last_height:
            break
        last_height = current_height
                
    # Find all .gz file links on the page
    file_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '.gz')]")
    file_links = [file_elem.get_attribute("href") for file_elem in file_elements]
    print(f"Found {len(file_links)} .gz file links:")
    for link in file_links:
        print(link)

    if not file_links:
        print("No .gz files found.")
        driver.quit()
        exit()

####### function to download files #######
def download_files(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
    

    
def main():
####### Check if the file exists #######
    try: 
        with open(json_file_path, "r") as json_file:
            cerberusJson = json.load(json_file)
    except FileNotFoundError:
        print("Error: cerberus.py : File not found")
        exit()
    except json.decoder.JSONDecodeError as e:
        print("Error: cerberus.py : Invalid JSON file")
        exit()

    ####### Check if the file is empty ######
    login_url = cerberusJson.get("url","")
    users_list = cerberusJson.get("users",[])

    ####### Check if the file has the required fields #######
    if not login_url:
        print("Error: cerberus.py : No login url found")
        exit()

    if not users_list or not isinstance(users_list, list):
        print("Error: cerberus.py : No users found")
        exit()

    # Creating relevant folders 
    download_folder = os.path.join(base_folder, "gzFiles")
    xml_folder = os.path.join(base_folder, "xmlFiles")
    os.makedirs(download_folder, exist_ok=True)
    os.makedirs(xml_folder, exist_ok=True)
    
    for users in users_list:
        username = users.get("username","")
        password = users.get("password","")

        if not username:
            print("Error: cerberus.py : No username found")
            exit()
        

        driver = webdriver.Chrome()
        driver.get(login_url)

        try:
            username_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
            username_field.send_keys(username)
            if password:
                password_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password")))
                password_field.send_keys(password)
            
            username_field.submit()
            WebDriverWait(driver,10).until(EC.url_contains("/file"))

            print("Logged in successfully. Proceeding to the file page...")
            
            
            find_files(driver)
            
            



            download_files(driver)
        except Exception as e:
            print("Error: cerberus.py : Login failed")

        finally:
            driver.quit()


main()
find_files()
download_files()
    








    
