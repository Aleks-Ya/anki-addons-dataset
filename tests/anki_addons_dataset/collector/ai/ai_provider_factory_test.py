from pathlib import Path

from anki_addons_dataset.collector.ai.ai_provider import AiProvider
from anki_addons_dataset.collector.ai.ai_provider_factory import AiProviderFactory
from anki_addons_dataset.collector.ai.deepseek_ai_provider import DeepSeekAiProvider
from anki_addons_dataset.collector.ai.no_ai_provider import NoAiProvider
from anki_addons_dataset.collector.ai.openai_ai_provider import OpenAiAiProvider
from anki_addons_dataset.config.app_config import AiConfig

MODEL: str = "test-model"


def __ai_config(api_key_file: Path, endpoint: str = "https://ai.example.com") -> AiConfig:
    return AiConfig(endpoint=endpoint, api_key_file=api_key_file, model=MODEL, readme_max_chars=8000)


def __api_key_file(tmp_path: Path) -> Path:
    api_key_file: Path = tmp_path / "ai-api-key.txt"
    api_key_file.write_text("secret-ai-key\n")
    return api_key_file


def test_deepseek_endpoint_creates_the_deepseek_provider(tmp_path: Path) -> None:
    config: AiConfig = __ai_config(__api_key_file(tmp_path), "https://api.deepseek.com")

    provider: AiProvider = AiProviderFactory.create(config, offline=False)

    assert isinstance(provider, DeepSeekAiProvider)
    assert provider.get_model() == MODEL


def test_other_endpoint_creates_the_openai_provider(tmp_path: Path) -> None:
    config: AiConfig = __ai_config(__api_key_file(tmp_path))

    provider: AiProvider = AiProviderFactory.create(config, offline=False)

    assert isinstance(provider, OpenAiAiProvider)
    assert not isinstance(provider, DeepSeekAiProvider)
    assert provider.get_model() == MODEL


def test_offline_creates_the_no_ai_provider(tmp_path: Path) -> None:
    config: AiConfig = __ai_config(tmp_path / "absent.txt")

    provider: AiProvider = AiProviderFactory.create(config, offline=True)

    assert isinstance(provider, NoAiProvider)
    assert provider.get_model() == MODEL
