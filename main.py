import util as u
from const import TEMP_PATH, MSG_KEY_NAME
import os

def main(): 
    """Program entry point.
    """
    u.get_image_from_blob()
    msg = u.get_text_from_blob()
    # msg = get_msg()
    while True:
        local_or_db = input("Do you want to work with offline storage or Azure CosmosDB?\n1 for offline, 2 for Azure, q to quit\n>> ")
        init_flag = init_validation(local_or_db)
        if init_flag == 0: break
        if init_flag == 1: pass
        if init_flag == 2: continue
        
        while True:
            if local_or_db == "1":
                user_list = u.generate_users_from_local()
                user_op_str = input("1 for bday\n2 for holiday\n3 for custom msg\nq to go back\n>> ")
                if user_op_str == "q":
                    break
                try:
                    user_op_int = int(user_op_str)
                    if user_op_int == 1:
                        u.send_bday_msgs_from_local(user_list, msg=msg)
                    elif user_op_int == 2:
                        u.send_holiday_msgs(user_list)
                    elif user_op_int == 3:
                        u.send_custom_msg(user_list)
                except Exception as e:
                    print(f"Enter a valid option! {e}")
                    continue
            
            # TODO after demo: validate inputs
            if local_or_db == "2":
                user_list = u.generate_users_from_mongodb()  
                user_op_str = input("1 for bday\n2 for holiday\n3 for custom msg\nq to go back\n> ")
                if user_op_str == "q":
                    break
                user_op_int = int(user_op_str)
                if user_op_int == 1:
                    u.send_bday_msgs_from_cloud(user_list, msg=msg)
                elif user_op_int == 2:
                    u.send_holiday_msgs(user_list)
                elif user_op_int == 3:
                    u.send_custom_msg(user_list)
    
    delete_all_temp()

             
def delete_all_temp():
    """Delete all temporary files created e.g., text, images, JSON files.
    
    Alternative method: use the temp folder to work with temp files.
    """
    if os.path.exists(TEMP_PATH):
        os.unlink(TEMP_PATH)
    os.unlink(path="resources/bday_memeDOWNLOAD.jpg")
    os.unlink(path="resources/msgDOWNLOAD.txt")


def get_msg():
    """Decrypt the text file that contains the message and retrieve it as a string.

    Returns:
        str: The message.
    """
    path_to_msg = "resources/msgDOWNLOAD.txt"
    u.decrypt_json(path=path_to_msg, key_name=MSG_KEY_NAME)
    with open(path_to_msg, "r") as f:
        msg = f.read()
    u.encrypt_json(path=path_to_msg, key_name=MSG_KEY_NAME)
    return msg


def init_validation(user_input):
    if user_input == "q":
        return 0
    if user_input == "1" or user_input == "2":
        return 1
    if user_input != "1" or user_input != "2":
        return 2

if __name__ == "__main__":
    main()