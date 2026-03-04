from pathlib import Path

from pydantic_settings import BaseSettings


class ChatPluginSettings(BaseSettings):
    home_dir: Path = Path.home() / ".amplifier-chat"

    model_config = {"env_prefix": "CHAT_PLUGIN_"}
