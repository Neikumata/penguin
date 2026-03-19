"""工具模块测试"""

import pytest
from unittest.mock import patch, MagicMock


class TestDangerousCommands:
    """危险命令检测测试"""

    def test_rm_rf_is_dangerous(self):
        """测试rm -rf被识别为危险命令"""
        from src.penguin.tools import is_dangerous_command

        assert is_dangerous_command("rm -rf /") is True
        assert is_dangerous_command("rm -rf ~") is True
        assert is_dangerous_command("rm -rf /home") is True

    def test_safe_command_not_dangerous(self):
        """测试安全命令不被阻止"""
        from src.penguin.tools import is_dangerous_command

        assert is_dangerous_command("ls -la") is False
        assert is_dangerous_command("echo hello") is False
        assert is_dangerous_command("cat file.txt") is False

    def test_mkfs_is_dangerous(self):
        """测试mkfs被识别为危险命令"""
        from src.penguin.tools import is_dangerous_command

        assert is_dangerous_command("mkfs.ext4 /dev/sda1") is True

    def test_fork_bomb_is_dangerous(self):
        """测试fork炸弹被识别"""
        from src.penguin.tools import is_dangerous_command

        assert is_dangerous_command(":(){ :|:& };:") is True

    def test_case_insensitive(self):
        """测试危险命令检测不区分大小写"""
        from src.penguin.tools import is_dangerous_command

        assert is_dangerous_command("RM -RF /") is True


class TestExecuteBash:
    """Bash执行测试"""

    def test_timeout_exception(self):
        """测试命令超时"""
        from src.penguin.tools import execute_bash

        # Windows下用ping模拟长时间命令
        result = execute_bash("ping -n 10 127.0.0.1", timeout=1)
        assert "超时" in result

    def test_echo_command(self):
        """测试简单echo命令"""
        from src.penguin.tools import execute_bash

        result = execute_bash("echo Hello")
        assert "Hello" in result

    def test_command_with_output(self):
        """测试有输出的命令"""
        from src.penguin.tools import execute_bash

        result = execute_bash("echo test123")
        assert "test123" in result

    def test_blocked_dangerous_command(self):
        """测试危险命令被阻止"""
        from src.penguin.tools import execute_bash

        result = execute_bash("rm -rf /")
        assert "错误" in result or "阻止" in result

    def test_invalid_command(self):
        """测试无效命令处理"""
        from src.penguin.tools import execute_bash

        result = execute_bash("nonexistent_command_xyz123")
        # 应该返回错误或非零返回码信息
        assert result  # 应该有输出

    def test_timeout_parameter(self):
        """测试超时参数"""
        from src.penguin.tools import execute_bash

        # 短命令应该很快完成
        result = execute_bash("echo test", timeout=5)
        assert "test" in result


class TestExecuteTool:
    """工具执行器测试"""

    def test_execute_bash_tool(self):
        """测试执行bash工具"""
        from src.penguin.tools import execute_tool

        result = execute_tool("bash", '{"command": "echo test"}')
        assert "test" in result

    def test_execute_bash_tool_dict_args(self):
        """测试使用字典参数执行bash工具"""
        from src.penguin.tools import execute_tool

        result = execute_tool("bash", {"command": "echo hello"})
        assert "hello" in result

    def test_execute_unknown_tool(self):
        """测试未知工具返回错误"""
        from src.penguin.tools import execute_tool

        result = execute_tool("unknown_tool", "{}")
        assert "错误" in result or "未知" in result

    def test_execute_invalid_json_args(self):
        """测试无效JSON参数"""
        from src.penguin.tools import execute_tool

        result = execute_tool("bash", "not valid json")
        assert "错误" in result


class TestToolsDefinition:
    """工具定义测试"""

    def test_get_tools_returns_list(self):
        """测试get_tools返回列表"""
        from src.penguin.tools import get_tools

        tools = get_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_bash_tool_definition(self):
        """测试bash工具定义格式"""
        from src.penguin.tools import get_tools

        tools = get_tools()
        bash_tool = next(
            (t for t in tools if t["function"]["name"] == "bash"), None
        )

        assert bash_tool is not None
        assert bash_tool["type"] == "function"
        assert "parameters" in bash_tool["function"]
        assert "command" in bash_tool["function"]["parameters"]["properties"]
