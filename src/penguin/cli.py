"""
Penguin CLI - 增强的命令行界面
支持流式输出、Markdown渲染、高级输入
"""

import sys
from typing import Callable, Optional
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

from .config import Config

# 条件导入 prompt_toolkit
_HAS_TTY = sys.stdin.isatty()
if _HAS_TTY:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style
else:
    PromptSession = None
    FileHistory = None
    Style = None


# 定义提示符样式
PROMPT_STYLE = Style.from_dict({
    'prompt': 'bold green',
}) if Style else None


class PenguinCLI:
    """Penguin命令行界面"""

    def __init__(self, history_file: Optional[str] = None):
        """
        初始化CLI

        Args:
            history_file: 历史记录文件路径
        """
        self.console = Console()
        self.session = None

        # 设置历史记录文件
        if history_file is None:
            history_dir = Path.home() / ".penguin"
            history_dir.mkdir(exist_ok=True)
            history_file = str(history_dir / "history")

        # 创建输入会话（仅在交互式终端中）
        if _HAS_TTY and PromptSession is not None:
            try:
                self.session = PromptSession(
                    history=FileHistory(history_file),
                    enable_history_search=True,
                )
            except Exception:
                self.session = None

        self.current_model = Config.get_model()

    def print_banner(self):
        """打印欢迎横幅"""
        banner = """
[bold cyan]🐧 Penguin - Multi-AI Agent Loop System[/bold cyan]
"""
        self.console.print(Panel(
            f"{banner}\n"
            f"当前模型: [green]{self.current_model}[/green]\n"
            "命令: [yellow]/help[/yellow] | [yellow]/model <模型>[/yellow] | [yellow]/clear[/yellow] | [yellow]/exit[/yellow]",
            border_style="cyan",
            padding=(0, 2),
        ))
        self.console.print()

    def print_markdown(self, text: str):
        """
        渲染Markdown内容

        Args:
            text: Markdown文本
        """
        self.console.print(Markdown(text))

    def print_code(self, code: str, language: str = "python"):
        """
        渲染代码块

        Args:
            code: 代码内容
            language: 编程语言
        """
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)

    def print_tool_call(self, tool_name: str, args: str):
        """打印工具调用信息"""
        self.console.print(f"\n[bold yellow]⚙ 工具调用:[/bold yellow] [cyan]{tool_name}[/cyan]({args})")

    def print_tool_result(self, result: str, max_length: int = 200):
        """打印工具结果"""
        truncated = result[:max_length]
        if len(result) > max_length:
            truncated += "..."
        self.console.print(f"[bold green]✓ 工具结果:[/bold green] {truncated}")

    def print_error(self, message: str):
        """打印错误信息"""
        self.console.print(f"[bold red]✗ 错误:[/bold red] {message}")

    def print_success(self, message: str):
        """打印成功信息"""
        self.console.print(f"[bold green]✓[/bold green] {message}")

    def print_info(self, message: str):
        """打印信息"""
        self.console.print(f"[bold blue]ℹ[/bold blue] {message}")

    def get_input(self) -> str:
        """
        获取用户输入（支持多行）

        Returns:
            用户输入的文本
        """
        try:
            if self.session is not None:
                # 先用 rich 打印带颜色的提示
                self.console.print("[bold green]你:[/bold green] ", end="")
                return self.session.prompt(
                    "",
                    multiline=False,
                    mouse_support=True,
                ).strip()
            else:
                # 非交互式环境，使用标准输入
                self.console.print("[bold green]你:[/bold green] ", end="")
                return input().strip()
        except Exception:
            return ""

    def stream_output(self, text: str, prefix: str = "\n🤖 "):
        """
        流式输出文本（使用Live实现实时更新）

        Args:
            text: 要输出的完整文本
            prefix: 输出前缀
        """
        self.console.print(prefix, end="")

    def create_stream_handler(self) -> Callable[[str], None]:
        """
        创建流式输出回调函数

        Returns:
            回调函数，接收文本块并实时打印
        """
        first_chunk = True

        def handler(chunk: str):
            nonlocal first_chunk
            if first_chunk:
                self.console.print("\n[bold magenta]🤖 助手:[/bold magenta] ", end="")
                first_chunk = False
            # 直接打印，保留原始格式
            print(chunk, end="", flush=True)

        return handler

    def render_response(self, text: str):
        """
        渲染助手响应（自动检测Markdown）

        Args:
            text: 响应文本
        """
        self.console.print()  # 换行

        # 检测是否包含Markdown元素
        has_markdown = any([
            "```" in text,  # 代码块
            "**" in text or "__" in text,  # 粗体
            "*" in text or "_" in text,  # 斜体
            "##" in text or "#" in text,  # 标题
            "- " in text or "* " in text,  # 列表
            "| " in text,  # 表格
            "[" in text and "](" in text,  # 链接
        ])

        if has_markdown:
            self.print_markdown(text)
        else:
            self.console.print(text)

    def print_help(self):
        """打印帮助信息"""
        help_text = """
## 可用命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/model <模型名>` | 切换AI模型 |
| `/models` | 列出常用模型 |
| `/clear` | 清空对话历史 |
| `/exit`, `/quit` | 退出程序 |

## 模型格式 (LiteLLM)

- `anthropic/claude-3-5-sonnet`
- `openai/gpt-4o`
- `deepseek/deepseek-chat`
- `zhipu/glm-4`
- `ollama/llama3`

## 示例

```
你好
列出当前目录的文件
/model openai/gpt-4o
```
"""
        self.print_markdown(help_text)

    def print_models(self):
        """打印常用模型列表"""
        models_text = """
## 常用模型

### Z.AI (智谱) - 推荐

| 模型 | 说明 |
|------|------|
| `zai/glm-4.5-flash` | 免费 |
| `zai/glm-4.7` | 最新旗舰, 200K上下文 |
| `zai/glm-4.6` | 200K上下文 |
| `zai/glm-4.5` | 128K上下文 |
| `zai/glm-4.5v` | 视觉模型 |

### Anthropic

- `anthropic/claude-3-5-sonnet`
- `anthropic/claude-3-opus`
- `anthropic/claude-3-haiku`

### OpenAI

- `openai/gpt-4o`
- `openai/gpt-4-turbo`
- `openai/gpt-3.5-turbo`

### DeepSeek

- `deepseek/deepseek-chat`
- `deepseek/deepseek-coder`

### Ollama (本地)

- `ollama/llama3`
- `ollama/qwen2`
- `ollama/codellama`
"""
        self.print_markdown(models_text)
