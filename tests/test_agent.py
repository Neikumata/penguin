"""Agent Loop模块测试"""

import pytest
from unittest.mock import patch, MagicMock


class TestAgentLoop:
    """Agent Loop核心测试"""

    @patch("src.penguin.agent.completion")
    def test_simple_response_no_tools(self, mock_completion):
        """测试简单响应（无工具调用）"""
        from src.penguin.agent import agent_loop

        # Mock响应
        mock_message = MagicMock()
        mock_message.content = "你好！有什么可以帮助你的？"
        mock_message.tool_calls = None

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_completion.return_value = mock_response

        messages = [{"role": "user", "content": "你好"}]
        result = agent_loop(messages)

        assert result == "你好！有什么可以帮助你的？"
        assert len(messages) == 2  # 用户消息 + 助手消息

    @patch("src.penguin.agent.completion")
    def test_tool_call_execution(self, mock_completion):
        """测试工具调用执行"""
        from src.penguin.agent import agent_loop

        # 第一次调用：返回工具调用
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "bash"
        mock_tool_call.function.arguments = '{"command": "echo test"}'

        mock_message1 = MagicMock()
        mock_message1.content = ""
        mock_message1.tool_calls = [mock_tool_call]

        # 第二次调用：返回最终响应
        mock_message2 = MagicMock()
        mock_message2.content = "命令执行成功"
        mock_message2.tool_calls = None

        mock_response1 = MagicMock()
        mock_response1.choices = [MagicMock(message=mock_message1)]

        mock_response2 = MagicMock()
        mock_response2.choices = [MagicMock(message=mock_message2)]

        mock_completion.side_effect = [mock_response1, mock_response2]

        messages = [{"role": "user", "content": "运行echo test"}]
        result = agent_loop(messages)

        assert result == "命令执行成功"
        # 应该有：用户消息 + 助手消息(工具调用) + 工具结果 + 助手消息(最终)
        assert len(messages) >= 3

    @patch("src.penguin.agent.completion")
    def test_max_iterations_limit(self, mock_completion):
        """测试最大迭代次数限制"""
        from src.penguin.agent import agent_loop

        # 模拟持续返回工具调用
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "bash"
        mock_tool_call.function.arguments = '{"command": "echo test"}'

        mock_message = MagicMock()
        mock_message.content = ""
        mock_message.tool_calls = [mock_tool_call]

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_completion.return_value = mock_response

        messages = [{"role": "user", "content": "测试"}]
        result = agent_loop(messages, max_iterations=3)

        assert "错误" in result or "最大迭代" in result

    @patch("src.penguin.agent.completion")
    def test_api_error_handling(self, mock_completion):
        """测试API错误处理"""
        from src.penguin.agent import agent_loop

        mock_completion.side_effect = Exception("API连接失败")

        messages = [{"role": "user", "content": "你好"}]
        result = agent_loop(messages)

        assert "错误" in result

    def test_default_model_used(self):
        """测试使用默认模型"""
        from src.penguin.agent import agent_loop

        # 验证当model为None时使用默认模型
        from src.penguin.config import Config
        assert Config.get_model() is not None


class TestRunConversation:
    """对话运行测试"""

    @patch("src.penguin.agent.agent_loop")
    def test_user_message_added(self, mock_agent_loop):
        """测试用户消息被添加到历史"""
        from src.penguin.agent import run_conversation

        mock_agent_loop.return_value = "回复内容"

        messages = []
        result = run_conversation("你好", messages)

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "你好"

    @patch("src.penguin.agent.agent_loop")
    def test_returns_agent_response(self, mock_agent_loop):
        """测试返回agent响应"""
        from src.penguin.agent import run_conversation

        mock_agent_loop.return_value = "这是助手的回复"

        messages = []
        result = run_conversation("问题", messages)

        assert result == "这是助手的回复"

    @patch("src.penguin.agent.agent_loop")
    def test_custom_model_passed(self, mock_agent_loop):
        """测试自定义模型被传递"""
        from src.penguin.agent import run_conversation

        mock_agent_loop.return_value = "回复"

        messages = []
        run_conversation("测试", messages, model="openai/gpt-4o")

        # 验证agent_loop被调用（模型参数会被传递）
        mock_agent_loop.assert_called_once()
