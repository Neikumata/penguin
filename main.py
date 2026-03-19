"""
Penguin - Multi-AI Agent Loop System
主入口 - REPL交互界面
"""

import sys
from src.penguin.config import Config
from src.penguin.agent import run_conversation_stream
from src.penguin.cli import PenguinCLI


def main():
    """主函数 - REPL循环"""
    cli = PenguinCLI()
    cli.print_banner()

    # 对话历史
    messages = []
    cli.current_model = Config.get_model()

    while True:
        try:
            # 获取用户输入
            user_input = cli.get_input()

            # 跳过空输入
            if not user_input:
                continue

            # 处理命令
            if user_input.startswith("/"):
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()

                if command in ("/exit", "/quit"):
                    cli.console.print("\n[bold cyan]再见! 👋[/bold cyan]")
                    break

                elif command == "/help":
                    cli.print_help()

                elif command == "/models":
                    cli.print_models()

                elif command == "/model":
                    if len(parts) < 2:
                        cli.print_info("用法: /model <模型名>")
                        cli.print_info("示例: /model openai/gpt-4o")
                    else:
                        new_model = parts[1].strip()
                        cli.current_model = new_model
                        cli.print_success(f"已切换到模型: {new_model}")

                elif command == "/clear":
                    messages = []
                    cli.print_success("对话历史已清空")

                else:
                    cli.print_error(f"未知命令: {command}")
                    cli.print_info("输入 /help 查看可用命令")

                continue

            # 创建流式输出回调
            stream_handler = cli.create_stream_handler()

            def on_content(chunk: str):
                stream_handler(chunk)

            def on_tool_call(name: str, args: str):
                cli.print_tool_call(name, args)

            def on_tool_result(result: str):
                cli.print_tool_result(result)

            # 运行对话（流式）
            response = run_conversation_stream(
                user_input,
                messages,
                cli.current_model,
                on_content=on_content,
                on_tool_call=on_tool_call,
                on_tool_result=on_tool_result,
            )

            # 渲染最终响应
            cli.render_response(response)

        except KeyboardInterrupt:
            cli.console.print("\n\n[yellow]已中断。输入 /exit 退出。[/yellow]")
            continue

        except EOFError:
            cli.console.print("\n\n[bold cyan]再见! 👋[/bold cyan]")
            break

        except Exception as e:
            cli.print_error(str(e))
            continue


if __name__ == "__main__":
    main()
