"""
実装1：LLM単体利用 (run_llm_only.py)
目的: 外部情報を一切与えなかった場合の、LLMの基準（ベースライン）を確認する。
"""

import asyncio
import time
from typing import Any, Dict

from env_utils import create_vertex_ai_llm, setup_environment

# 環境変数を読み込み
setup_environment()


async def process_llm_only(query: str, demo_mode: bool = False) -> Dict[str, Any]:
    """LLM単体処理"""

    intermediate_steps = [{
        "step": "initialize",
        "description": "LLMを初期化",
        "timestamp": time.time()
    }]

    if demo_mode:
        await asyncio.sleep(1.0)

    intermediate_steps.append({
        "step": "llm_invoke",
        "description": "LLMに直接クエリを送信",
        "timestamp": time.time()
    })

    # ChatVertexAIをgemini-2.5-flashモデルで初期化
    llm = create_vertex_ai_llm()

    # 統一されたプロンプト形式を使用（他のモードと同じ）
    formatted_prompt = f"""以下の製品取扱説明書を参考にして、質問に答えてください。

=== 製品取扱説明書 ===
（この質問では外部情報は提供されていません）

=== 質問 ===
{query}

=== 回答 ===
製品取扱説明書の内容に基づいて、正確な情報を提供してください。"""

    response = llm.invoke(formatted_prompt)

    if demo_mode:
        await asyncio.sleep(0.5)

    intermediate_steps.append({"step": "complete", "description": "処理完了", "timestamp": time.time()})

    return {
        "response": response.content,
        "intermediate_steps": intermediate_steps,
        "actual_prompt": formatted_prompt  # 実際に使用されたプロンプトを返す
    }


def main():
    """直接実行時のテスト用"""
    import asyncio

    # 質問を定義
    question = "エラーコードE-404の対処法は？"

    print("=== 実装1: LLM単体利用 ===")
    print(f"質問: {question}")
    print("-" * 50)

    # 非同期処理を実行
    result = asyncio.run(process_llm_only(question))

    print("回答:")
    print(result["response"])
    print("-" * 50)


if __name__ == "__main__":
    main()
