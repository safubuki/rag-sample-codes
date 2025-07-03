"""
実装2：プロンプトスタッフィング (run_prompt_stuffing.py)
目的: LLMの広大なコンテキストウィンドウを使い、力技で全ての情報を与える手法の挙動を確認する。
"""

import asyncio
import time
from pathlib import Path
from typing import Any, Dict

from env_utils import create_vertex_ai_llm, setup_environment

# 環境変数を読み込み
setup_environment()


async def process_prompt_stuffing(query: str,
                                  knowledge_path: Path,
                                  demo_mode: bool = False) -> Dict[str, Any]:
    """プロンプトスタッフィング処理"""

    intermediate_steps = [{
        "step": "initialize",
        "description": "エンジンを初期化",
        "timestamp": time.time()
    }]

    if demo_mode:
        await asyncio.sleep(0.5)

    # knowledge.txtの全内容を読み込み
    with open(knowledge_path, "r", encoding="utf-8") as f:
        knowledge_content = f.read()

    intermediate_steps.append({
        "step": "load_knowledge",
        "description": f"ナレッジファイルを読み込み ({len(knowledge_content)}文字)",
        "timestamp": time.time()
    })

    if demo_mode:
        await asyncio.sleep(1.0)

    # プロンプト作成
    prompt = f"""以下の製品取扱説明書を参考にして、質問に答えてください。

=== 製品取扱説明書 ===
{knowledge_content}

=== 質問 ===
{query}

=== 回答 ===
製品取扱説明書の内容に基づいて、正確な情報を提供してください。"""

    intermediate_steps.append({
        "step": "create_prompt",
        "description": "ナレッジ情報を含むプロンプトを作成",
        "timestamp": time.time()
    })

    if demo_mode:
        await asyncio.sleep(1.0)

    # ChatVertexAIをgemini-2.5-flashモデルで初期化
    llm = create_vertex_ai_llm()

    response = llm.invoke(prompt)

    intermediate_steps.append({"step": "complete", "description": "処理完了", "timestamp": time.time()})

    return {
        "response": response.content,
        "intermediate_steps": intermediate_steps,
        "actual_prompt": prompt  # トークン数計算用に実際のプロンプトを返す
    }


def main():
    """直接実行時のテスト用"""
    import asyncio

    # 質問を定義
    question = "エラーコードE-404の対処法は？"
    knowledge_path = Path("../../data/knowledge.txt")

    print("=== 実装2: プロンプトスタッフィング ===")
    print(f"質問: {question}")
    print("-" * 50)

    # 非同期処理を実行
    result = asyncio.run(process_prompt_stuffing(question, knowledge_path))

    print("回答:")
    print(result["response"])
    print("-" * 50)


if __name__ == "__main__":
    main()
