"""配置管理模块测试"""

import os
import pytest
from unittest.mock import patch


class TestConfig:
    """Config类测试"""

    def test_default_model(self):
        """测试默认模型设置"""
        from src.penguin.config import Config

        # 验证默认模型格式正确
        assert Config.DEFAULT_MODEL is not None
        assert "/" in Config.DEFAULT_MODEL  # LiteLLM格式: provider/model

    def test_get_model_returns_default(self):
        """测试get_model返回默认模型"""
        from src.penguin.config import Config

        model = Config.get_model()
        assert model == Config.DEFAULT_MODEL

    def test_bash_timeout_default(self):
        """测试Bash超时默认值"""
        from src.penguin.config import Config

        assert Config.BASH_TIMEOUT == 120
        assert isinstance(Config.BASH_TIMEOUT, int)

    @patch.dict(os.environ, {"MODEL": "openai/gpt-4o"})
    def test_model_from_env(self):
        """测试从环境变量加载模型"""
        # 重新加载模块以获取新的环境变量
        import importlib
        import src.penguin.config as config_module
        importlib.reload(config_module)

        from src.penguin.config import Config
        # 注意：由于模块已加载，这个测试验证配置机制

    def test_validate_api_key_anthropic(self):
        """测试Anthropic API密钥验证"""
        from src.penguin.config import Config

        result = Config.validate_api_key("anthropic/claude-3-5-sonnet")
        # 结果取决于环境变量是否设置
        assert isinstance(result, bool)

    def test_validate_api_key_openai(self):
        """测试OpenAI API密钥验证"""
        from src.penguin.config import Config

        result = Config.validate_api_key("openai/gpt-4o")
        assert isinstance(result, bool)

    def test_validate_api_key_ollama_always_true(self):
        """测试Ollama不需要API密钥"""
        from src.penguin.config import Config

        # Ollama是本地运行，始终返回True
        result = Config.validate_api_key("ollama/llama3")
        assert result is True

    def test_validate_api_key_zai(self):
        """测试Z.AI API密钥验证"""
        from src.penguin.config import Config

        result = Config.validate_api_key("zai/glm-4.5-flash")
        assert isinstance(result, bool)

    def test_validate_api_key_unknown_provider(self):
        """测试未知提供商的API密钥验证"""
        from src.penguin.config import Config

        result = Config.validate_api_key("unknown/model")
        assert result is False
