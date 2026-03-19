"""工具定义和执行模块"""

import json
import subprocess
import shlex
from typing import Any
from .config import Config


# 危险命令黑名单
DANGEROUS_COMMANDS = [
    "rm -rf",
    "rm -rf /",
    "rm -rf ~",
    ":(){ :|:& };:",  # Fork bomb
    "mkfs",
    "dd if=",
    "> /dev/sda",
    "chmod -R 777 /",
    "chown -R",
    "wget http",
    "curl http",
]


def is_dangerous_command(command: str) -> bool:
    """检查命令是否危险"""
    command_lower = command.lower().strip()
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous.lower() in command_lower:
            return True
    return False


def execute_bash(command: str, timeout: int = None) -> str:
    """
    执行Bash命令

    Args:
        command: 要执行的命令
        timeout: 超时时间(秒)

    Returns:
        命令输出结果
    """
    if timeout is None:
        timeout = Config.BASH_TIMEOUT

    if is_dangerous_command(command):
        return f"错误: 命令被阻止，可能存在危险: {command}"

    try:
        # 使用shell执行命令
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=None,  # 使用当前工作目录
        )

        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"

        if result.returncode != 0:
            output += f"\n[返回码]: {result.returncode}"

        return output.strip() if output.strip() else "命令执行完成(无输出)"

    except subprocess.TimeoutExpired:
        return f"错误: 命令执行超时 (超过 {timeout} 秒)"
    except Exception as e:
        return f"错误: {str(e)}"


# LiteLLM工具定义 (OpenAI格式)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "执行Bash命令。使用此工具运行系统命令、脚本或程序。支持管道、重定向等shell特性。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的Bash命令",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "可选: 命令超时时间(秒)，默认120秒",
                    },
                },
                "required": ["command"],
            },
        },
    }
]


def execute_tool(name: str, arguments: str | dict) -> str:
    """
    执行工具调用

    Args:
        name: 工具名称
        arguments: 工具参数 (JSON字符串或字典)

    Returns:
        工具执行结果
    """
    # 解析参数
    if isinstance(arguments, str):
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            return f"错误: 无法解析参数: {arguments}"
    else:
        args = arguments

    # 执行对应工具
    if name == "bash":
        command = args.get("command", "")
        timeout = args.get("timeout")
        return execute_bash(command, timeout)
    else:
        return f"错误: 未知工具 '{name}'"


def get_tools() -> list:
    """获取工具定义列表"""
    return TOOLS
