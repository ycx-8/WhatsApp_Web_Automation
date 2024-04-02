"""Provides functions to automate sending birthday, holiday messages, customized text messages and photos to a list of contact (can be filtered through tags) via WhatsApp Web.

It utilizes the selenium to automate this process. The contact can be updated and retrieved in and from a local directory or Azure Cosmos DB for MongoDB. The images and text messages can be retrieved from Azure Blob Storage or locally.

Provide functions that generate current date, customized message, contact list from local storage or from Azure Cosmos DB for MongoDB.

Provides utility functions for Selenium automation on WhatsApp Web e.g., finding a button and click it.

Note: the choice of using CSS selector rather than XPath to find elements is for better speed, browser support, readability and specificity.
"""

from time import sleep
from datetime import datetime as dt
import json
import datetime
from const import CONTACT_PATH_LOCAL, DOCUMENT_ID, TEMP_PATH, TAGS, MSG_KEY_NAME, CONTACT_KEY_NAME,PATH_TO_RESOURCES
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bson import ObjectId
from cryptography.fernet import Fernet
import os
from azure.storage.blob import BlobServiceClient
from pymongo import MongoClient


def get_blob_service_client():
    """Retrieve the Azure Blob Service Client
    
    Alternative way to authenticate: use Microsoft Entra ID instead of connection strings

    Returns:
        BlobServiceClient: the BlobServiceClient returned based on the Blob Connection String save in local env variable
    """
    try:
        BLOB_CONN_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        return BlobServiceClient.from_connection_string(BLOB_CONN_STRING)
    except Exception as e:
        print(f"An error has occurred: {e}")


def get_image_from_blob():
    """Download birthday meme image from the "images" container from "demofunc0001" storage account

    Returns:
        str: the path to the image downloaded.
    """
    # local_file_name = str(uuid.uuid4()) + ".jpg"
    local_file_name = "bday_meme.jpg"
    blob_service_client = get_blob_service_client()
    container_name = "images"
    # blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)
    blob_name = "bday1.jpg"
    download_file_path = os.path.join(PATH_TO_RESOURCES, str.replace(local_file_name ,'.jpg', 'DOWNLOAD.jpg'))
    
    download(blob_service_client=blob_service_client, container_name=container_name, download_file_path=download_file_path, blob_name=blob_name)
    
    return download_file_path


def get_text_from_blob():
    """Download birthday message from the "text" container from "demofunc0001" storage account

    Returns:
        str: the birthday message
    """
    # local_file_name = str(uuid.uuid4()) + ".txt"
    local_file_name = "msg.txt"
    blob_service_client = get_blob_service_client()
    container_name = "text"
    # blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)
    blob_name = "msg.txt"
    download_file_path = os.path.join(PATH_TO_RESOURCES, str.replace(local_file_name ,'.txt', 'DOWNLOAD.txt'))
    
    download(blob_service_client=blob_service_client, container_name=container_name, download_file_path=download_file_path, blob_name=blob_name)
    
    with open(download_file_path, "r") as f:
        msg = f.read()
        return msg


def get_doc_from_blob():
    """Download a document from the "docs" container from "demofunc0001" storage account
    
    Returns:
        str: the path to the document downloaded.
    """
    local_file_name = "notice.pdf"
    blob_service_client = get_blob_service_client()
    container_name = "docs"
    # blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)
    blob_name = "rent_notice.pdf"
    download_file_path = os.path.join(PATH_TO_RESOURCES, str.replace(local_file_name ,'.txt', 'DOWNLOAD.txt'))
    
    download(blob_service_client=blob_service_client, container_name=container_name, download_file_path=download_file_path, blob_name=blob_name)
    
    return download_file_path


def download(blob_service_client, container_name: str, download_file_path: str, blob_name: str):
    """The actual process of downloading from Azure Blob

    Args:
        blob_service_client (_type_): The Blob service client.
        container_name (str): Name of the Blob container.
        download_file_path (str): Path to download.
        blob_name (str): Name of the blob.
    """
    container_client = blob_service_client.get_container_client(container_name) 
    print("\nDownloading blob to \n\t" + download_file_path)
    
    with open(file=download_file_path, mode="wb") as download_file:
        download_file.write(container_client.download_blob(blob_name).readall())


def get_collection():
    """To return a collection (of contacts) from the local MongoDB database

    Returns:
        pymongo.collection.Collection: the collection of a MongoDB database.
    """
    variable = "AzureMongoDBConnectionStr"
    CONNECTION_STRING = os.getenv(variable)
    client = MongoClient(CONNECTION_STRING)
    database = client[os.getenv("AZURE_MONGODB_DB")]
    return database[os.getenv("AZURE_MONGODB_COLLECTION")]


def encrypt_json(path: str, key_name: str):
    """To encrypt contacts.json stored in local directory

    Args:
        path (str): The path to contacts.json
    """
    key = Fernet.generate_key()
    with open(key_name, "wb") as f:
        f.write(key)
    with open(key_name, "rb") as f:
        key = f.read()
    fernet = Fernet(key)
    with open(path, "rb") as f:
        original = f.read()
    encrypted = fernet.encrypt(original)
    with open(path, "wb") as f:
        f.write(encrypted)


def decrypt_json(path: str, key_name: str):
    """To decrypt contacts.json stored in local directory

    Args:
        path (str): The path to contacts.json
    """
    with open(key_name, "rb") as f:
        key = f.read()
    fernet = Fernet(key)
    with open(path, "rb") as f:
        encrypted = f.read()
    decrypted = fernet.decrypt(encrypted)
    with open(path, "wb") as f:
        f.write(decrypted)
        

def is_encrypted(path, key_name: str):
    """Check if contacts.json is encrypted or not

    Args:
        path (str): The path to contacts.json

    Returns:
        bool: returns True if encrypted, otherwise False
    """
    try:
        decrypt_json(path, key_name)
        encrypt_json(path, key_name)
        return True
    except Exception as e:
        return False


def create_chromedriver_options():
    """Set up ChromeDriver options to avoid 2nd login to WhatsApp Web with QR code each time for session persistence along with some extra configuration.
    
    Below you can see the Chrome cmd-line option that specifies the dir where user data (like profiles, settings, etc.) is stored - useful when you want to reuse an existing Chrome user profile, enabling you to persist settings, cookies, and other user-specific data between browser sessions.
    
    Note: "--headless=new" rather than just "--headlesss" for Chrome versions >= 109. Disable headless mode for demo purpose.

    Returns:
        Options: The Configured ChromeDriver options.
    """
    dir_path = os.getcwd()
    profile = os.path.join(dir_path, "profile", "wpp")
    ops = webdriver.ChromeOptions()
    ops.add_argument(f"user-data-dir={profile}")
    ops.add_argument("--start-maximized")
    # ops.add_argument('--headless=new')
    ops.add_experimental_option('excludeSwitches', ['enable-logging'])
    ops.add_argument("--log-level=3") 
    # TODO: explore more option arguments to maximize speed and minimize resource usage.
    return ops


def open_whatsapp_web(user: list, msg=""):
    """Create a ChromeDriver with options and open WhatsApp Web in Chrome.
    
    Note: user[2] indicates user's mobile number.

    Args:
        user (list): User's details.
        msg (str, optional): text message to send to a contact. Defaults to "".

    Returns:
        WebDriver: A Chrome WebDriver object.
    """
    ops = create_chromedriver_options()
    link = f"https://web.whatsapp.com/send?phone={user[2]}&text={msg}"
    driver = webdriver.Chrome(options=ops)
    driver.get(link)
    return driver


def click_plus_btn_in_chat(driver):
    """Find the "+" button next to the message text box by its CSS selector and click it.

    Args:
        driver (WebDriver): The Chrome WebDriver object required.
    """
    plus_btn_selector = "#main > footer > div._2lSWV._3cjY2.copyable-area > div > span:nth-child(2) > div > div._2xy_p._1bAtO > div._1OT67 > div > div"
    # TODO: experiment with the wait time to improve speed.
    plus_btn = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, plus_btn_selector))
    )
    plus_btn.click()
    
    
def click_send_photo_btn(driver):
    """Find the "Photos & Videos" button by its CSS selector and click it.
    
    Note: increase sleep time for demo purposes. 

    Args:
        driver (WebDriver): The Chrome WebDriver object required
    """
    selector = "#app > div > div.two._1jJ70 > div._2QgSC > div._2Ts6i._2xAQV > span > div > span > div > div > div.g0rxnol2.thghmljt.p357zi0d.rjo8vgbg.ggj6brxn.f8m0rgwh.gfz4du6o.r7fjleex.bs7a17vp > div > div.O2_ew > div._3wFFT > div > div"
    # TODO: experiment with the wait time to improve speed.
    send_btn = WebDriverWait(driver, 17).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
    send_btn.click()
    sleep(5)


def click_send_btn(driver):
    """Find the ">" (send) button by its CSS selector and click it.

    Note: increase sleep time for demo purposes. 
    
    Args:
        driver (WebDriver): The Chrome WebDriver object required
    """
    selector = "#main > footer > div._2lSWV._3cjY2.copyable-area > div > span:nth-child(2) > div > div._1VZX7 > div._2xy_p._3XKXx > button"
    # TODO: experiment with the wait time to improve speed.
    send_btn = WebDriverWait(driver, 17).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
    send_btn.click()
    sleep(5)


def generate_cur_date():
    """Generate current date

    Returns:
    - dict: A dictionary containing the current date
      ```
      Example:
      {
          'current_date': 'YYYY-MM-DD'
      }
      ```

    Raises:
    - ValueError: If there is an issue retrieving the current date or time.
    """
    try:
        cur_datetime = dt.now().date()
        return {'current date': cur_datetime}
    except Exception as e:
        print(f"An error occurred: {e}")


def generate_msg():
    """Provide user input for the message the user wants to send.

    Returns:
        str: user's custom message.
    """
    msg = input(
        "Enter your msg here\n(If you want to add someone's name, type zzzz as a placeholder)\n> ")
    return msg


def generate_users_from_local():
    """Generate all user details from contact.json stored in the local directory and put them in a list

    The list consists of: contact key, contact name, contact phone number, contact's birthday, contact tag

    Returns:
        list: A list of contact details [key, name, phone number, birthday, tag]
    """
    try:
        if is_encrypted(CONTACT_PATH_LOCAL, CONTACT_KEY_NAME) or is_encrypted("resources/msgDOWNLOAD.txt", MSG_KEY_NAME):
            decrypt_json(CONTACT_PATH_LOCAL, CONTACT_KEY_NAME)
            with open(CONTACT_PATH_LOCAL) as f:
                data = json.load(f)
            encrypt_json(CONTACT_PATH_LOCAL, CONTACT_KEY_NAME)
            return convert_contact_dict_to_nested_list(data)
        else:
            print("contacts.json is not encrypted!")
    except Exception as e:
        print(f"An error occurred when trying to load local contact.json: {e}")


def generate_users_from_mongodb():
    """Retrieve users' details from Azure Cosmos DB for MongoDB database and transform them to a nested list of contact information.

    Returns:
        list: A list of contact details [key, name, phone number, birthday, tag]
    """
    data_raw_with_id = get_document_from_azure_mongodb()

    # Omit 1st iteration of _id and add rest of dict to a new dict, then save it to a temp json file for future reads (while the program is still running).
    # TODO: work directly with the data structure received from Azure database, manipulate it to a new dictionary without the _id field.
    data_raw_no_id = {key: value for index,
                      (key, value) in enumerate(data_raw_with_id.items()) if index > 0}
    try:
        with open(TEMP_PATH, 'w') as f:
            json.dump(data_raw_no_id, f, indent=2)
        with open(TEMP_PATH, "r") as f:
            data = json.load(f)
            # encrypt_json(TEMP_PATH)
    except Exception as e:
        print(f"An error occurred when trying to load temp json file: {e}")
        return
    return convert_contact_dict_to_nested_list(data)


def get_document_from_azure_mongodb():
    """Return a document from Azure Cosmos DB for MongoDB as a dictionary.
    
    The dictionary will consists of the document id and the data (which is a list of contact details)

    Returns:
        dict: document id and a list of contact details.
    """
    try:
        collection = get_collection()
        return collection.find_one()
    except Exception as e:
        print(f"An error has occurred when trying to find the document in Azure: {e}")
        return None


def convert_contact_dict_to_nested_list(data):
    """Once data has been retrieved from Azure MongoDB, it is transformed to a nested list in this function.
    
    No need to skip the 1st iteration unlike dealing with contact.json from local directory because we already extracted the json data without _id to the temp file. 

    Args:
        data (dict): a dictionary of contact details

    Returns:
        list: a list of user details [key, name, phone number, birthday, tag]
    """
    contact_list = []    
    for key, value in data.items():
        user_info = [key, value["name"], value["number"],
                     dt.strptime(value["bday"], "%Y-%m-%d").date(), value["tag"]]
        contact_list.append(user_info)
    return contact_list


# -----below for testing-----
# encrypt_json(CONTACT_PATH_LOCAL, key_name="resources/js.key")
# encrypt_json("resources/msgDOWNLOAD.txt", key_name="resources/msg.key")
# decrypt_json(CONTACT_PATH_LOCAL, key_name="resources/js.key")
# decrypt_json("resources/msgDOWNLOAD.txt", key_name="resources/msg.key")

    
def send_txtmsg(user: list, msg=""):
    """Send automated message via WhatsApp Web to a phone number.

    Args:
        user (list): user details including user key, user name, user phone number and user birthday.
        msg (str): message to be sent.
    """
    driver = open_whatsapp_web(user=user, msg=msg)
    click_send_btn(driver=driver)
    driver.quit()
    

def send_photo(user, msg=""):
    """Send photo via WhatsApp Web to a phone number.

    Args:
        user (list): User's details
        msg (str, optional): Caption for the photo which is optional. Defaults to "".
    """
    driver = open_whatsapp_web(user=user, msg=msg)

    click_plus_btn_in_chat(driver=driver)
    
    photos_btn_selector = "#main > footer > div._2lSWV._3cjY2.copyable-area > div > span:nth-child(2) > div > div._2xy_p._1bAtO > div._1OT67 > div > span > div > ul > div > div:nth-child(2) > li > div"
    photo_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, photos_btn_selector))
    )
    photo_btn.click()
    
    sleep(3)
    try:
        file_upload_selector = "#main > footer > div._2lSWV._3cjY2.copyable-area > div > span:nth-child(2) > div > div._2xy_p._1bAtO > div._1OT67 > div > span > div > ul > div > div:nth-child(2) > li > div > input[type=file]"
        file_upload = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, file_upload_selector))
        )
        file_upload.send_keys(os.path.abspath("resources/bday_memeDOWNLOAD.jpg"))
        sleep(3)
        click_send_photo_btn(driver=driver)
        sleep(6)
        driver.quit()
    except TimeoutError as e:
        print(f"Exception: {e}")
  

def send_documents(user, msg=""):
    pass
  

def update_year_in_local(user: list):
    """Increment user's birthday year by one after birthday message is sent and update list of user details (json)

    Args:
        user (list): user details including user key, user name, user phone number and user birthday.
    """
    with open(CONTACT_PATH_LOCAL, "r") as f:
        decrypt_json(CONTACT_PATH_LOCAL, CONTACT_KEY_NAME)
        data = json.load(f)
    
    bday_year_increment_update = increment_year(user)
    data[user[0]]["bday"] = bday_year_increment_update
    
    with open(CONTACT_PATH_LOCAL, "w") as f:
        json.dump(data, f, indent=2)
    encrypt_json(CONTACT_PATH_LOCAL, CONTACT_KEY_NAME)
    return data


def update_year_in_cloud(user: list):
    """_summary_

    Args:
        user (_type_): _description_

    Returns:
        _type_: _description_
    """
    with open(TEMP_PATH, "r") as f:
        data = json.load(f)

    bday_year_increment_update = increment_year(user)
    data[user[0]]["bday"] = bday_year_increment_update
    
    with open(TEMP_PATH, "w") as f:
        json.dump(data, f, indent=2)
        
    # If you go into Azure Cosmos DB for MongoDB account (RU) Data Explorer sometimes you have refresh the entire tab (rather than just the refresh button for the document) to see the updated results. This is probably a bug from Microsoft :(
    collection = get_collection()
    collection.update_one({"_id": ObjectId(DOCUMENT_ID)}, {"$set": data})
    return data


def send_bday_msgs_from_local(user_list, msg: str):
    """Send customized automated birthday messages to a list of contacts

    Args:
        user_list (dict): the contact list to go through in order to send automated messages.

    Returns:
        dict: updated contact list.
    """
    current_date = generate_cur_date()["current date"]
    updated_data = {}
    for user in user_list:
        msg_new = msg.replace("zzzz", user[1])
        
        # check leap year
        if is_leap_year(current_date.year):
            # If today is 02-29, consider it as 02-28 for comparison
            if current_date.month == 2 and current_date.day == 29:
                current_date = dt.date(current_date.year, 2, 28)
            # Adjust the birthdate if it's 02-29 in a non-leap year
            if not is_leap_year(user[3].year):
                user[3] = datetime.date(user[3].year, 2, 28)
        
        # If bday matches:
        if current_date == user[3]:
            send_txtmsg(user, msg_new)
            send_photo(user)
            updated_data = update_year_in_local(user)
            print(f"It is {user[1]}'s bday today! Msg sent")
        else:
            print(f"NOT {user[1]}'s bday today")
    return updated_data


def send_bday_msgs_from_cloud(user_list, msg: str):
    """Send customized automated birthday messages to a list of contacts.

    Args:
        user_list (dict): the contact list to go through in order to send automated messages.

    Returns:
        dict: updated contact list.
    """
    current_date = generate_cur_date()["current date"]
    updated_data = {}
    for user in user_list:
        # msg = f"Happy Birthday {user[1]}! Hope you have a good one!"
        msg_new = msg.replace("zzzz", user[1])

        # If bday matches:
        if current_date == user[3]:
            send_txtmsg(user, msg_new)
            send_photo(user)
            updated_data = update_year_in_cloud(user)
            print(f"It is {user[1]}'s bday today! Msg sent")
        else:
            print(f"NOT {user[1]}'s bday today")
    return updated_data


def send_holiday_msgs(user_list):   
    """Send Xmas and NY messages to a list of contacts.

    Args:
        user_list (dict): the contact list to go through in order to send automated messages.
    """
    current_date = generate_cur_date()["current date"]
    # current_date_to_compare = dt(int(dt.now().year), int(dt.now().month), int(dt.now().day)).date()
    # TODO: get holiday messages from Azure Blob Storage.
    for user in user_list:
        if current_date == dt(int(dt.now().year), 12, 25).date():
            msg = f"Merry Xmas {user[1]}! May your holidays be filled with joy and laughter."
            send_txtmsg(user, msg)
        elif current_date == dt(int(dt.now().year), 1, 1).date():
            msg = f"Happy New Year {user[1]}! May your holidays be filled with joy and laughter. Wishing you a happy and prosperous New Year filled with joy and new beginnings!"
            send_txtmsg(user, msg)
        # elif current_date == current_date_to_compare:
        #     msg = f"Happy {dt.now().strftime("%A")} {user[1]}! Hope you have a productive day!"
        #     send_msg(user, msg)
        else:
            print("No holiday today!")
            break
            

def send_custom_msg(user_list: dict):
    """Send customized messages (use placeholders for a person's name). Can be filtered through tag input.
    
    Note: user[4] is the associated tag.

    Args:
        user_list (dict): the contact list to go through in order to send automated messages.
    """
    msg = generate_msg()
    tag_filter = input("Enter a tag to send the msg to selected contacts or type 'all' to send to all:\n> ").lower()
    for user in user_list:
        msg_customized = msg.replace("zzzz", user[1])
        if tag_filter == user[4]:
            send_txtmsg(user, msg_customized)
        if tag_filter == "all":
            send_txtmsg(user, msg_customized)
        if tag_filter.isspace() or not any(tag_filter == s for s in TAGS):
            print("Enter a valid tag or 'all'!")
            break
        

def increment_year(user: list):
    """Increment year by 1

    Args:
        user (list): a contact's details

    Returns:
        str: updated datetime in yyyy-mm-dd format
    """
    data_split = user[3].strftime("%Y-%m-%d").split("-")
    data_split_year_increment = str(int(data_split[0])+1)
    data_split_month = data_split[1]
    data_split_day = data_split[2]
    return f"{data_split_year_increment}-{data_split_month}-{data_split_day}"


def is_leap_year(year: int):
    """Check if a year is a leap year.
    
    Arg:
        year (int): year.
    
    Returns:
        bool: True if it's a leap year, otherwise False.
    """
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

