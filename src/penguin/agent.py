"""Agent Loop核心模块"""

import json
from typing import Optional, Callable
from litellm import completion
from .config import Config
from .tools import execute_tool, get_tools


def agent_loop(
    messages: list,
    model: Optional[str] = None,
    tools: Optional[list] = None,
    max_iterations: int = 50,
) -> str:
    """
    Agent Loop核心函数

    Args:
        messages: 对话消息列表
        model: 使用的模型 (LiteLLM格式: provider/model)
        tools: 工具定义列表
        max_iterations: 最大迭代次数

    Returns:
        最终响应内容
    """
    if model is None:
        model = Config.get_model()

    if tools is None:
        tools = get_tools()

    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        try:
            # 调用LiteLLM
            response = completion(
                model=model,
                messages=messages,
                tools=tools,
            )
        except Exception as e:
            return f"API调用错误: {str(e)}"

        # LiteLLM统一返回OpenAI格式
        message = response.choices[0].message

        # 构建助手消息
        assistant_message = {"role": "assistant", "content": message.content or ""}

        # 如果有工具调用，添加到消息中
        if message.tool_calls:
            assistant_message["tool_calls"] = []
            for tc in message.tool_calls:
                assistant_message["tool_calls"].append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

        messages.append(assistant_message)

        # 如果没有工具调用，返回最终结果
        if not message.tool_calls:
            return message.content or ""

        # 执行所有工具调用
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments

            print(f"\n[工具调用] {tool_name}({tool_args})")

            # 执行工具
            result = execute_tool(tool_name, tool_args)

            print(f"[工具结果] {result[:200]}{'...' if len(result) > 200 else ''}")

            # 添加工具结果消息
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    return "错误: 达到最大迭代次数限制"


def agent_loop_stream(
    messages: list,
    model: Optional[str] = None,
    tools: Optional[list] = None,
    max_iterations: int = 50,
    on_content: Optional[Callable[[str], None]] = None,
    on_tool_call: Optional[Callable[[str, str], None]] = None,
    on_tool_result: Optional[Callable[[str], None]] = None,
) -> str:
    """
    流式Agent Loop核心函数

    Args:
        messages: 对话消息列表
        model: 使用的模型 (LiteLLM格式: provider/model)
        tools: 工具定义列表
        max_iterations: 最大迭代次数
        on_content: 内容流式输出回调
        on_tool_call: 工具调用回调
        on_tool_result: 工具结果回调

    Returns:
        最终响应内容
    """
    if model is None:
        model = Config.get_model()

    if tools is None:
        tools = get_tools()

    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        try:
            # 调用LiteLLM (流式)
            response = completion(
                model=model,
                messages=messages,
                tools=tools,
                stream=True,
            )
        except Exception as e:
            return f"API调用错误: {str(e)}"

        # 处理流式响应
        full_content = ""
        tool_calls = []
        current_tool_call = None

        for chunk in response:
            delta = chunk.choices[0].delta

            # 处理内容
            if delta.content:
                full_content += delta.content
                if on_content:
                    on_content(delta.content)

            # 处理工具调用
            if hasattr(delta, "tool_calls") and delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.id:  # 新工具调用开始
                        current_tool_call = {
                            "id": tc.id,
                            "name": tc.function.name if tc.function else "",
                            "arguments": "",
                        }
                        tool_calls.append(current_tool_call)

                    if tc.function:
                        if tc.function.name:
                            if current_tool_call:
                                current_tool_call["name"] = tc.function.name
                        if tc.function.arguments:
                            if current_tool_call:
                                current_tool_call["arguments"] += tc.function.arguments

        # 构建助手消息
        assistant_message = {"role": "assistant", "content": full_content or ""}

        # 如果有工具调用，添加到消息中
        if tool_calls:
            assistant_message["tool_calls"] = []
            for tc in tool_calls:
                assistant_message["tool_calls"].append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"],
                    },
                })

        messages.append(assistant_message)

        # 如果没有工具调用，返回最终结果
        if not tool_calls:
            return full_content

        # 执行所有工具调用
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["arguments"]

            if on_tool_call:
                on_tool_call(tool_name, tool_args)

            # 执行工具
            result = execute_tool(tool_name, tool_args)

            if on_tool_result:
                on_tool_result(result)

            # 添加工具结果消息
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": result,
            })

    return "错误: 达到最大迭代次数限制"


def run_conversation(user_input: str, messages: list, model: Optional[str] = None) -> str:
    """
    运行单轮对话

    Args:
        user_input: 用户输入
        messages: 对话历史
        model: 使用的模型

    Returns:
        助手响应
    """
    # 添加用户消息
    messages.append({"role": "user", "content": user_input})

    # 运行agent loop
    response = agent_loop(messages, model)

    return response


def run_conversation_stream(
    user_input: str,
    messages: list,
    model: Optional[str] = None,
    on_content: Optional[Callable[[str], None]] = None,
    on_tool_call: Optional[Callable[[str, str], None]] = None,
    on_tool_result: Optional[Callable[[str], None]] = None,
) -> str:
    """
    运行单轮对话（流式）

    Args:
        user_input: 用户输入
        messages: 对话历史
        model: 使用的模型
        on_content: 内容流式输出回调
        on_tool_call: 工具调用回调
        on_tool_result: 工具结果回调

    Returns:
        助手响应
    """
    # 添加用户消息
    messages.append({"role": "user", "content": user_input})

    # 运行流式agent loop
    response = agent_loop_stream(
        messages,
        model,
        on_content=on_content,
        on_tool_call=on_tool_call,
        on_tool_result=on_tool_result,
    )

    return response
