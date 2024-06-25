import json
import typing as t

from prediction_market_agent_tooling.config import APIKeys as APIKeysBase
from prediction_market_agent_tooling.loggers import logger
from prediction_market_agent_tooling.tools.utils import (
    check_not_none,
    should_not_happen,
)
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBKeys(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    SQLALCHEMY_DB_URL: t.Optional[str] = None


class APIKeys(APIKeysBase):
    SERP_API_KEY: t.Optional[SecretStr] = None
    OPENAI_API_KEY: t.Optional[SecretStr] = None
    TAVILY_API_KEY: t.Optional[SecretStr] = None
    PINECONE_API_KEY: t.Optional[SecretStr] = None
    PINATA_API_KEY: t.Optional[SecretStr] = None
    PINATA_API_SECRET: t.Optional[SecretStr] = None

    @property
    def serp_api_key(self) -> SecretStr:
        return check_not_none(
            self.SERP_API_KEY, "SERP_API_KEY missing in the environment."
        )

    @property
    def openai_api_key(self) -> SecretStr:
        return check_not_none(
            self.OPENAI_API_KEY, "OPENAI_API_KEY missing in the environment."
        )

    @property
    def tavily_api_key(self) -> SecretStr:
        return check_not_none(
            self.TAVILY_API_KEY, "TAVILY_API_KEY missing in the environment."
        )

    @property
    def pinecone_api_key(self) -> SecretStr:
        return check_not_none(
            self.PINECONE_API_KEY, "PINECONE_API_KEY missing in the environment."
        )

    @property
    def pinata_api_key(self) -> SecretStr:
        return check_not_none(
            self.PINATA_API_KEY, "PINATA_API_KEY missing in the environment."
        )

    @property
    def pinata_api_secret(self) -> SecretStr:
        return check_not_none(
            self.PINATA_API_SECRET, "PINATA_API_SECRET missing in the environment."
        )


class SocialMediaAPIKeys(APIKeys):
    FARCASTER_PRIVATE_KEY: t.Optional[SecretStr] = None
    TWITTER_ACCESS_TOKEN: t.Optional[SecretStr] = None
    TWITTER_ACCESS_TOKEN_SECRET: t.Optional[SecretStr] = None
    TWITTER_BEARER_TOKEN: t.Optional[SecretStr] = None
    TWITTER_API_KEY: t.Optional[SecretStr] = None
    TWITTER_API_KEY_SECRET: t.Optional[SecretStr] = None

    @property
    def farcaster_private_key(self) -> SecretStr:
        return check_not_none(
            self.FARCASTER_PRIVATE_KEY,
            "FARCASTER_PRIVATE_KEY missing in the environment.",
        )

    @property
    def twitter_access_token(self) -> SecretStr:
        return check_not_none(
            self.TWITTER_ACCESS_TOKEN,
            "TWITTER_ACCESS_TOKEN missing in the environment.",
        )

    @property
    def twitter_access_token_secret(self) -> SecretStr:
        return check_not_none(
            self.TWITTER_ACCESS_TOKEN_SECRET,
            "TWITTER_ACCESS_TOKEN_SECRET missing in the environment.",
        )

    @property
    def twitter_bearer_token(self) -> SecretStr:
        return check_not_none(
            self.TWITTER_BEARER_TOKEN,
            "TWITTER_BEARER_TOKEN missing in the environment.",
        )

    @property
    def twitter_api_key(self) -> SecretStr:
        return check_not_none(
            self.TWITTER_API_KEY,
            "TWITTER_API_KEY missing in the environment.",
        )

    @property
    def twitter_api_key_secret(self) -> SecretStr:
        return check_not_none(
            self.TWITTER_API_KEY_SECRET,
            "TWITTER_API_KEY_SECRET missing in the environment.",
        )


def get_market_prompt(question: str) -> str:
    prompt = (
        f"Research and report on the following question:\n\n"
        f"{question}\n\n"
        f"Return ONLY a single world answer: 'Yes' or 'No', even if you are unsure. If you are unsure, make your best guess.\n"
    )
    return prompt


def parse_result_to_boolean(result: str) -> bool:
    return (
        True
        if result.lower() == "yes"
        else (
            False
            if result.lower() == "no"
            else should_not_happen(f"Invalid result: {result}")
        )
    )


def parse_result_to_str(result: bool) -> str:
    return "Yes" if result else "No"


def completion_str_to_json(completion: str) -> dict[str, t.Any]:
    """
    Cleans completion JSON in form of a string:

    ```json
    {
        ...
    }
    ```

    into just { ... }
    ```
    """
    start_index = completion.find("{")
    end_index = completion.rfind("}")
    completion = completion[start_index : end_index + 1]
    completion_dict: dict[str, t.Any] = json.loads(completion)
    return completion_dict


def patch_sqlite3() -> None:
    """
    Helps in the environemnt where one can't update system's sqlite3 installation, for example, Streamlit Cloud, where we get:

    ```
    Your system has an unsupported version of sqlite3. Chroma requires sqlite3 >= 3.35.0.
    ```

    This function patches the sqlite3 module to use pysqlite3 instead of sqlite3.
    """
    try:
        __import__("pysqlite3")
        import sys

        sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
    except ImportError:
        logger.warning("pysqlite3-binary not found, using sqlite3 instead.")
