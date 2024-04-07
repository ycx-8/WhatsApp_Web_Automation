# WhatsApp-Web-Automation
WhatsApp Web Automation using Python, Selenium and Azure.

## Background
Do you have trouble remembering to send birthday messages or holiday greeting messages? Do you have 100 contacts and do not want to send messages manually? Fear not as I have the solution for you...

## Tech Stack
- Python
- Selenium
- Azure Cosmos DB for MongoDB
- Azure Blob Storage

## Set up and Run
Create a contacts.json file in the resources directory (in the future I will make a desktop GUI app using PyQt where you can carry out CRUD operations with your list of contact...but for now you have to hard code it). The json file should have the following structure (make sure all the fields in the below example are present):
{
  "contact_00001": {
    "name": "Adam",
    "number": "+61000000000",
    "bday": "2024-05-14",
    "tag": "work"
  },
  "contact_00002": {
    "name": "Jerry",
    "number": "+61000000000",
    "bday": "2024-02-07",
    "tag": "friend"
  }
}
You will need an Azure account to work with the Azure part of the program. As for now, I have not implemented code that can create resources groups and resources so you will have to set it up manually. You will need: Cosmos DB for MongoDB and a storage account for Blob storage with 3 containers: images, text and docs.
Once cloned, just python main.py on your Windows machine (important as I have not developed checks against other OS), either from VS Code (if you want to edit the source code) or from PowerShell/Cmd Line.

## Future Features & Improvements
Use Selenium to send documents to individuals for customized message.
Ability to send text message, photos, videos and documents to a group chat.
Work on calculating Chinese new year.
A desktop Python program to manage the list of contacts: a GUI app using PyQt.
Ability to work with relational databases in Azure (Azure Cosmos DB for PostgreSQL).
Automatic creation of Azure resource groups and resouces (for this project, a storage account with 3 Blob containers and files uploaded to each and an Azure Cosmos DB for MongoDB (RU) account).
Deploy to Azure function with a time trigger.
