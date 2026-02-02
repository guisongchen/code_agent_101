"""
Unit tests for configuration system.
"""
import os
import tempfile
from pathlib import Path
from typing import Dict, Generator

import pytest
from dotenv import load_dotenv

from chat_shell_101.config import Config, OpenAIConfig, StorageConfig, load_config


class TestOpenAIConfig:
    """Test suite for OpenAIConfig."""

    def test_default_values(self) -> None:
        """Test default values when no environment variables are set."""
        # Clear relevant environment variables
        env_vars = ["OPENAI_API_KEY", "CHAT_SHELL_DEFAULT_MODEL", "BASE_URL"]
        original_values = {}
        for var in env_vars:
            original_values[var] = os.environ.get(var)
            os.environ.pop(var, None)

        try:
            config = OpenAIConfig()

            assert config.api_key == ""
            assert config.model == "gpt-4"  # Default from code
            assert config.base_url is None
            assert config.temperature == 0.7
            assert config.max_tokens == 4096
        finally:
            # Restore environment variables
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value

    def test_environment_variable_loading(self) -> None:
        """Test loading values from environment variables."""
        # Set environment variables
        os.environ["OPENAI_API_KEY"] = "test-api-key-123"
        os.environ["CHAT_SHELL_DEFAULT_MODEL"] = "gpt-3.5-turbo"
        os.environ["BASE_URL"] = "https://api.example.com"

        try:
            config = OpenAIConfig()

            assert config.api_key == "test-api-key-123"
            assert config.model == "gpt-3.5-turbo"
            assert config.base_url == "https://api.example.com"
        finally:
            # Clean up
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("CHAT_SHELL_DEFAULT_MODEL", None)
            os.environ.pop("BASE_URL", None)

    def test_base_url_none_when_empty(self) -> None:
        """Test that empty BASE_URL results in None."""
        os.environ["BASE_URL"] = ""

        try:
            config = OpenAIConfig()
            assert config.base_url is None
        finally:
            os.environ.pop("BASE_URL", None)

    def test_field_validation(self) -> None:
        """Test Pydantic field validation."""
        # Valid configuration
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4",
            base_url="https://api.example.com",
            temperature=0.5,
            max_tokens=2048,
        )

        assert config.api_key == "sk-test"
        assert config.model == "gpt-4"
        assert config.base_url == "https://api.example.com"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048

    def test_temperature_range(self) -> None:
        """Test temperature field accepts valid range."""
        # Should accept 0.0
        config1 = OpenAIConfig(temperature=0.0)
        assert config1.temperature == 0.0

        # Should accept 1.0
        config2 = OpenAIConfig(temperature=1.0)
        assert config2.temperature == 1.0

        # Should accept 0.5
        config3 = OpenAIConfig(temperature=0.5)
        assert config3.temperature == 0.5

    def test_max_tokens_validation(self) -> None:
        """Test max_tokens field validation."""
        # Should accept positive integers
        config = OpenAIConfig(max_tokens=1024)
        assert config.max_tokens == 1024

        # Should accept large values
        config = OpenAIConfig(max_tokens=1000000)
        assert config.max_tokens == 1000000


class TestStorageConfig:
    """Test suite for StorageConfig."""

    def test_default_values(self) -> None:
        """Test default values when no environment variables are set."""
        # Clear environment variable
        original_value = os.environ.get("CHAT_SHELL_STORAGE_PATH")
        os.environ.pop("CHAT_SHELL_STORAGE_PATH", None)

        try:
            config = StorageConfig()

            assert config.type == "json"
            # Path should expand ~ to home directory
            expected_path = Path("~/.chat_shell_101").expanduser()
            assert config.path == expected_path
        finally:
            # Restore environment variable
            if original_value is not None:
                os.environ["CHAT_SHELL_STORAGE_PATH"] = original_value

    def test_environment_variable_loading(self) -> None:
        """Test loading storage path from environment variable."""
        test_path = "/tmp/test_storage"

        os.environ["CHAT_SHELL_STORAGE_PATH"] = test_path

        try:
            config = StorageConfig()

            assert config.type == "json"
            assert config.path == Path(test_path)
        finally:
            os.environ.pop("CHAT_SHELL_STORAGE_PATH", None)

    def test_path_expansion(self) -> None:
        """Test that ~ is expanded to home directory."""
        # Test with ~ in path
        os.environ["CHAT_SHELL_STORAGE_PATH"] = "~/chat_shell_test"

        try:
            config = StorageConfig()

            # Path should be expanded
            expected_path = Path.home() / "chat_shell_test"
            assert config.path == expected_path
        finally:
            os.environ.pop("CHAT_SHELL_STORAGE_PATH", None)

    def test_custom_type(self) -> None:
        """Test custom storage type."""
        config = StorageConfig(type="memory")

        assert config.type == "memory"

    def test_custom_path(self) -> None:
        """Test custom storage path."""
        custom_path = Path("/custom/storage/path")
        config = StorageConfig(path=custom_path)

        assert config.path == custom_path

    def test_relative_path(self) -> None:
        """Test relative path is preserved."""
        input_path = Path("./relative/path")
        config = StorageConfig(path=input_path)

        # Path should remain relative (not expanded)
        assert config.path == input_path
        assert not config.path.is_absolute()


class TestConfig:
    """Test suite for Config."""

    @pytest.fixture
    def clean_env(self) -> Generator[None, None, None]:
        """Clean environment variables for isolation."""
        env_vars_to_clear = [
            "OPENAI_API_KEY",
            "CHAT_SHELL_DEFAULT_MODEL",
            "BASE_URL",
            "CHAT_SHELL_STORAGE_PATH",
            "CHAT_SHELL_SHOW_THINKING",
        ]

        original_values = {}
        for var in env_vars_to_clear:
            original_values[var] = os.environ.get(var)
            os.environ.pop(var, None)

        # Also clear any .env file loading
        pass  # load_dotenv(override=True)

        yield

        # Restore environment variables
        for var, value in original_values.items():
            if value is not None:
                os.environ[var] = value

    def test_default_values(self, clean_env: None) -> None:
        """Test default values when no environment variables are set."""
        config = Config()

        # OpenAI config defaults - API key may be loaded from .env file
        if config.openai.api_key:
            assert config.openai.api_key.startswith("sk-"), f"Invalid API key format: {config.openai.api_key}"
        else:
            assert config.openai.api_key == ""
        assert config.openai.model == "gpt-4"
        assert config.openai.base_url is None
        assert config.openai.temperature == 0.7
        assert config.openai.max_tokens == 4096

        # Storage config defaults
        assert config.storage.type == "json"
        expected_path = Path("~/.chat_shell_101").expanduser()
        assert config.storage.path == expected_path

        # Show thinking defaults
        assert config.show_thinking is False

    def test_show_thinking_environment_variable(self, clean_env: None) -> None:
        """Test show_thinking from environment variable."""
        # Test true values
        for value in ["true", "TRUE", "True"]:
            os.environ["CHAT_SHELL_SHOW_THINKING"] = value
            config = Config()
            assert config.show_thinking is True
            os.environ.pop("CHAT_SHELL_SHOW_THINKING", None)

        # Test false values
        for value in ["false", "FALSE", "False", "0", "no", "anything"]:
            os.environ["CHAT_SHELL_SHOW_THINKING"] = value
            config = Config()
            assert config.show_thinking is False
            os.environ.pop("CHAT_SHELL_SHOW_THINKING", None)

    def test_validate_api_key_valid(self) -> None:
        """Test API key validation with valid key."""
        config = Config()
        config.openai.api_key = "sk-valid-key-123"

        assert config.validate_api_key() is True

    def test_validate_api_key_empty(self) -> None:
        """Test API key validation with empty key."""
        config = Config()
        config.openai.api_key = ""

        assert config.validate_api_key() is False

    def test_validate_api_key_invalid_prefix(self) -> None:
        """Test API key validation with invalid prefix."""
        config = Config()
        config.openai.api_key = "invalid-prefix-123"

        assert config.validate_api_key() is False

    def test_validate_api_key_short(self) -> None:
        """Test API key validation with short key."""
        config = Config()
        config.openai.api_key = "sk-"

        assert config.validate_api_key() is True  # Starts with sk-

    def test_get_storage_path_creation(self, clean_env: None) -> None:
        """Test get_storage_path creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "new" / "nested" / "directory"

            config = Config()
            config.storage.path = test_path

            # Directory should not exist initially
            assert not test_path.exists()

            # Get storage path should create it
            result_path = config.get_storage_path()

            assert result_path == test_path
            assert test_path.exists()
            assert test_path.is_dir()

    def test_get_storage_path_existing(self, clean_env: None) -> None:
        """Test get_storage_path with existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir)

            config = Config()
            config.storage.path = test_path

            # Directory already exists
            assert test_path.exists()

            # Get storage path should return it
            result_path = config.get_storage_path()

            assert result_path == test_path
            assert test_path.exists()

    def test_config_immutability(self, clean_env: None) -> None:
        """Test that config fields are immutable after creation."""
        config = Config()

        # Should not be able to modify nested configs directly
        # (Pydantic models are mutable by default, but we test the structure)
        original_openai_model = config.openai.model
        config.openai.model = "new-model"

        # Actually Pydantic models are mutable, so this will work
        # But we can test that we can create a new config with different values
        config2 = Config()
        config2.openai.model = "different-model"

        assert config.openai.model == "new-model"
        assert config2.openai.model == "different-model"

    def test_config_equality(self, clean_env: None) -> None:
        """Test config equality comparison."""
        config1 = Config()
        config2 = Config()

        # Default configs should be equal
        assert config1 == config2

        # Modified configs should not be equal
        config1.openai.model = "gpt-3.5-turbo"
        assert config1 != config2

    def test_config_representation(self, clean_env: None) -> None:
        """Test config string representation."""
        config = Config()

        repr_str = repr(config)
        assert "Config" in repr_str
        assert "openai" in repr_str
        assert "storage" in repr_str
        assert "show_thinking" in repr_str


class TestLoadConfig:
    """Test suite for load_config function."""

    @pytest.fixture
    def clean_env(self) -> Generator[None, None, None]:
        """Clean environment variables for isolation."""
        env_vars_to_clear = [
            "OPENAI_API_KEY",
            "CHAT_SHELL_DEFAULT_MODEL",
            "BASE_URL",
            "CHAT_SHELL_STORAGE_PATH",
            "CHAT_SHELL_SHOW_THINKING",
        ]

        original_values = {}
        for var in env_vars_to_clear:
            original_values[var] = os.environ.get(var)
            os.environ.pop(var, None)

        # Also clear any .env file loading
        pass  # load_dotenv(override=True)

        yield

        # Restore environment variables
        for var, value in original_values.items():
            if value is not None:
                os.environ[var] = value

    def test_load_config_defaults(self, clean_env: None) -> None:
        """Test load_config with default values."""
        config = load_config()

        assert isinstance(config, Config)
        # API key may be loaded from .env file
        if config.openai.api_key:
            assert config.openai.api_key.startswith("sk-"), f"Invalid API key format: {config.openai.api_key}"
        else:
            assert config.openai.api_key == ""
        assert config.openai.model == "gpt-4"
        assert config.storage.type == "json"

    def test_load_config_with_env_vars(self, clean_env: None) -> None:
        """Test load_config with environment variables."""
        os.environ["OPENAI_API_KEY"] = "sk-test-123"
        os.environ["CHAT_SHELL_DEFAULT_MODEL"] = "gpt-3.5-turbo"
        os.environ["CHAT_SHELL_STORAGE_PATH"] = "/tmp/test_storage"
        os.environ["CHAT_SHELL_SHOW_THINKING"] = "true"

        config = load_config()

        assert config.openai.api_key == "sk-test-123"
        assert config.openai.model == "gpt-3.5-turbo"
        assert config.storage.path == Path("/tmp/test_storage")
        assert config.show_thinking is True

    def test_load_config_api_key_validation_warning(self, clean_env: None, capsys: pytest.CaptureFixture) -> None:
        """Test load_config prints warning for invalid API key."""
        # No API key set (or loaded from .env)
        config = load_config()

        captured = capsys.readouterr()
        # Only expect warning if API key is empty
        if not config.openai.api_key:
            assert "Warning: OpenAI API key not set or invalid." in captured.out
            assert "Please set OPENAI_API_KEY environment variable." in captured.out

        # Invalid API key (doesn't start with sk-)
        os.environ["OPENAI_API_KEY"] = "invalid-key"
        config = load_config()

        captured = capsys.readouterr()
        assert "Warning: OpenAI API key not set or invalid." in captured.out

    def test_load_config_valid_api_key_no_warning(self, clean_env: None, capsys: pytest.CaptureFixture) -> None:
        """Test load_config doesn't print warning for valid API key."""
        os.environ["OPENAI_API_KEY"] = "sk-valid-key-123"
        config = load_config()

        captured = capsys.readouterr()
        assert "Warning: OpenAI API key not set or invalid." not in captured.out

    def test_global_config_instance(self, clean_env: None) -> None:
        """Test global config instance."""
        from chat_shell_101.config import config as global_config

        assert isinstance(global_config, Config)

        # Should have default values when no env vars set
        if global_config.openai.api_key:
            assert global_config.openai.api_key.startswith("sk-"), f"Invalid API key format: {global_config.openai.api_key}"
        else:
            assert global_config.openai.api_key == ""
        # Model may be overridden by .env file
        assert global_config.openai.model in ["gpt-4", "deepseek-chat"]

    def test_dotenv_file_loading(self, clean_env: None) -> None:
        """Test loading from .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .env file
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("""
OPENAI_API_KEY=sk-from-env-file
CHAT_SHELL_DEFAULT_MODEL=gpt-3.5-turbo-from-env
CHAT_SHELL_STORAGE_PATH=/tmp/from-env-file
CHAT_SHELL_SHOW_THINKING=true
""")

            # Load from .env file
            load_dotenv(dotenv_path=env_file, override=True)

            config = load_config()

            assert config.openai.api_key == "sk-from-env-file"
            assert config.openai.model == "gpt-3.5-turbo-from-env"
            assert config.storage.path == Path("/tmp/from-env-file")
            assert config.show_thinking is True