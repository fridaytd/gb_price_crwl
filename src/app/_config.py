import os

from dotenv import load_dotenv

from pydantic import BaseModel


class Config(BaseModel):
    # Keys
    KEYS_PATH: str

    # Sheets
    SPREADSHEET_KEY: str
    SHEET_NAME: str

    OUR_SELLER_NAME: str

    @staticmethod
    def from_env(dotenv_path: str = "settings.env") -> "Config":
        load_dotenv(dotenv_path)
        return Config.model_validate(os.environ)
