from dotenv import load_dotenv
import os

load_dotenv()

ZAPIER_WEBHOOK_URL = os.getenv("ZAPIER_WEBHOOK_URL", "")

OMNIQUE_CONFIG = {
    "url":          "https://app.omnique.com/Login.aspx",
    "username":     os.getenv("OMNIQUE_USERNAME"),
    "password":     os.getenv("OMNIQUE_PASSWORD"),
    "download_dir": os.getenv("OMNIQUE_DOWNLOAD_DIR", "./downloads"),
}

CLOUD_CONFIG = {
    "provider":              os.getenv("CLOUD_PROVIDER", "dropbox"),
    "dropbox_app_key":       os.getenv("DROPBOX_APP_KEY"),
    "dropbox_app_secret":    os.getenv("DROPBOX_APP_SECRET"),
    "dropbox_refresh_token": os.getenv("DROPBOX_REFRESH_TOKEN"),
    "folder_id":             os.getenv("GDRIVE_FOLDER_ID"),
}
