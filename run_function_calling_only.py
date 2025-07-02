"""
実装4：Function Callingのみ (run_function_calling_only.py)
目的: LLMが自律的にツール（関数）を呼び出す挙動の基本を実装する。
"""

from langchain.tools import tool
from langchain_google_vertexai import ChatVertexAI


@tool
def search_manual(query: str) -> str:
    """製品取扱説明書内でテキスト検索を行います。
    
    Args:
        query: 検索したいキーワードや文字列
        
    Returns:
        検索結果として見つかった関連する情報
    """
    # knowledge.txtから関連情報を検索
    with open("knowledge.txt", "r", encoding="utf-8") as f:
        content = f.read()

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


def main():
    print("=== 実装4: Function Callingのみ ===")

    # LLMを初期化し、ツールをバインド
    llm = ChatVertexAI(model_name="gemini-2.5-flash", temperature=0.1)
    llm_with_tools = llm.bind_tools([search_manual])

    # 質問
    question = "エラーコードE-404の対処法は？"
    print(f"質問: {question}")
    print("-" * 50)

    # 最初のLLM呼び出し（ツール使用判断）
    print("1. LLMがツール使用を判断中...")
    response = llm_with_tools.invoke(question)

    # ツール呼び出しが含まれているかチェック
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print("2. LLMがツール呼び出しを決定しました")

        # ツール実行
        tool_call = response.tool_calls[0]
        tool_name = tool_call['name']
        tool_args = tool_call['args']

        print(f"   ツール名: {tool_name}")
        print(f"   引数: {tool_args}")

        # 実際にツールを実行
        if tool_name == "search_manual":
            tool_result = search_manual.invoke(tool_args)
            print(f"3. ツール実行結果:")
            print(f"   {tool_result}")

            # ツール結果を含めて再度LLMに問い合わせ
            final_prompt = f"""以下のツール実行結果を基に、ユーザーの質問に答えてください。

質問: {question}

ツール実行結果:
{tool_result}

回答:"""

            print("4. ツール結果を基に最終回答を生成中...")
            final_response = llm.invoke(final_prompt)

            print("\n最終回答:")
            print(final_response.content)
        else:
            print("   未知のツールが呼び出されました")
    else:
        print("2. LLMは直接回答を選択しました")
        print("\n回答:")
        print(response.content)

    print("-" * 50)


if __name__ == "__main__":
    main()
