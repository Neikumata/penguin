"""配置管理模块"""

import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


class Config:
    """配置类，管理API密钥和模型设置"""

    # 默认模型
    DEFAULT_MODEL = os.getenv("MODEL", "zai/glm-4.5-flash")

    # API Keys (LiteLLM自动识别这些环境变量)
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    ZAI_API_KEY = os.getenv("ZAI_API_KEY")  # Z.AI (智谱)

    # 自定义base_url (可选)
    ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")

    # 工具配置
    BASH_TIMEOUT = int(os.getenv("BASH_TIMEOUT", "120"))  # 默认120秒超时

    @classmethod
    def get_model(cls) -> str:
        """获取当前配置的模型"""
        return cls.DEFAULT_MODEL

    @classmethod
    def validate_api_key(cls, model: str) -> bool:
        """验证指定模型的API密钥是否存在"""
        provider = model.split("/")[0] if "/" in model else ""

        key_mapping = {
            "anthropic": cls.ANTHROPIC_API_KEY,
            "openai": cls.OPENAI_API_KEY,
            "deepseek": cls.DEEPSEEK_API_KEY,
            "zai": cls.ZAI_API_KEY,  # Z.AI (智谱)
            "ollama": "ollama",  # Ollama本地运行，不需要API密钥
        }

        return bool(key_mapping.get(provider))
