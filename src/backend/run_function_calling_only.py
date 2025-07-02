"""
実装4：Function Callingのみ (run_function_calling_only.py)
目的: LLMが自律的にツール（関数）を呼び出す挙動の基本を実装する。
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List

from env_utils import create_vertex_ai_llm, setup_environment
from langchain.tools import tool

# 環境変数を読み込み
setup_environment()


@tool
def search_manual(query: str) -> str:
    """製品取扱説明書内でテキスト検索を行います。
    
    Args:
        query: 検索したいキーワードや文字列
        
    Returns:
        検索結果として見つかった関連する情報
    """
    # knowledge.txtから関連情報を検索
    # 相対パスではなく、適切なパスを使用
    knowledge_path = Path(__file__).parent.parent.parent / "data" / "knowledge.txt"

    try:
        with open(knowledge_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return f"ナレッジベースファイルが見つかりません: {knowledge_path}"

    # 単純な文字列検索
    lines = content.split('\n')
    relevant_lines = []

    for line in lines:
        if query.lower() in line.lower():
            relevant_lines.append(line.strip())

    if relevant_lines:
        return "\n".join(relevant_lines)
    else:
        return f"'{query}'に関する情報は見つかりませんでした。"


async def process_function_calling_only(user_query: str, demo_mode: bool = False) -> Dict[str, Any]:
    """Function Callingのみのモードで処理を実行する
    
    Args:
        user_query: ユーザーからの質問
        demo_mode: デモモード（詳細なログ出力）
        
    Returns:
        Dict containing response, intermediate_steps, and actual_prompt
    """
    intermediate_steps = []

    if demo_mode:
        print("=== 実装4: Function Callingのみ ===")
        print(f"質問: {user_query}")
        print("-" * 50)

    # LLMを初期化し、ツールをバインド
    llm = create_vertex_ai_llm()
    llm_with_tools = llm.bind_tools([search_manual])

    intermediate_steps.append({"step": 1, "action": "LLM初期化完了", "details": "LLMにツールをバインドしました"})

    # 最初のLLM呼び出し（ツール使用判断）
    if demo_mode:
        print("1. LLMがツール使用を判断中...")

    response = llm_with_tools.invoke(user_query)
    actual_prompt = user_query  # 初期プロンプト

    intermediate_steps.append({
        "step":
            2,
        "action":
            "初回LLM呼び出し",
        "details":
            f"ツール呼び出し判断: {'あり' if hasattr(response, 'tool_calls') and response.tool_calls else 'なし'}"
    })

    # ツール呼び出しが含まれているかチェック
    if hasattr(response, 'tool_calls') and response.tool_calls:
        if demo_mode:
            print("2. LLMがツール呼び出しを決定しました")

        # ツール実行
        tool_call = response.tool_calls[0]
        tool_name = tool_call['name']
        tool_args = tool_call['args']

        if demo_mode:
            print(f"   ツール名: {tool_name}")
            print(f"   引数: {tool_args}")

        intermediate_steps.append({
            "step": 3,
            "action": "ツール呼び出し決定",
            "details": f"ツール: {tool_name}, 引数: {tool_args}"
        })

        # 実際にツールを実行
        if tool_name == "search_manual":
            tool_result = search_manual.invoke(tool_args)

            if demo_mode:
                print(f"3. ツール実行結果:")
                print(f"   {tool_result}")

            intermediate_steps.append({
                "step":
                    4,
                "action":
                    "ツール実行完了",
                "details":
                    f"検索結果: {tool_result[:100]}..." if len(tool_result) > 100 else tool_result
            })

            # ツール結果を含めて再度LLMに問い合わせ
            final_prompt = f"""以下のツール実行結果を基に、ユーザーの質問に答えてください。

質問: {user_query}

ツール実行結果:
{tool_result}

回答:"""

            actual_prompt = final_prompt  # 実際に使用されたプロンプトを更新

            if demo_mode:
                print("4. ツール結果を基に最終回答を生成中...")

            final_response = llm.invoke(final_prompt)
            final_answer = final_response.content

            intermediate_steps.append({
                "step": 5,
                "action": "最終回答生成",
                "details": "ツール結果を基に最終回答を生成しました"
            })
        else:
            final_answer = f"未知のツール '{tool_name}' が呼び出されました"
            intermediate_steps.append({
                "step": 3,
                "action": "エラー",
                "details": f"未知のツール: {tool_name}"
            })
    else:
        if demo_mode:
            print("2. LLMは直接回答を選択しました")

        final_answer = response.content
        intermediate_steps.append({"step": 3, "action": "直接回答", "details": "LLMはツールを使用せずに直接回答しました"})

    if demo_mode:
        print("\n最終回答:")
        print(final_answer)
        print("-" * 50)

    return {
        "response": final_answer,
        "intermediate_steps": intermediate_steps,
        "actual_prompt": actual_prompt
    }


def main():
    """メイン関数 - 直接実行用"""

    async def run():
        return await process_function_calling_only("エラーコードE-404の対処法は？", demo_mode=True)

    return asyncio.run(run())


if __name__ == "__main__":
    main()
