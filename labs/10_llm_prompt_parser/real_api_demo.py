"""可选：用真实模型跑一遍（需要环境变量 OPENAI_API_KEY）。

跑法：$env:OPENAI_API_KEY="sk-..."; uv run python labs/10_llm_prompt_parser/real_api_demo.py

没有 Key 时它会打印提示并退出，不会报错——练习和测试都不依赖网络。
"""

from __future__ import annotations

import os


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print("未设置 OPENAI_API_KEY，跳过真实模型调用。")
        return

    from langchain_openai import ChatOpenAI

    from learnkit.lc_fakes import last_human_text

    model = ChatOpenAI(model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    response = model.invoke("用一句话解释什么是 GIL")
    print("回答:", response.content)
    print("用量:", getattr(response, "usage_metadata", None))
    print("最后一条用户消息:", last_human_text([response]))


if __name__ == "__main__":
    main()
