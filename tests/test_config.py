from chat_plugin.config import ChatPluginSettings


def test_default_home_dir():
    settings = ChatPluginSettings()
    assert str(settings.home_dir).endswith(".amplifier-chat")


def test_custom_home_dir(tmp_path):
    settings = ChatPluginSettings(home_dir=tmp_path / "custom")
    assert settings.home_dir == tmp_path / "custom"
