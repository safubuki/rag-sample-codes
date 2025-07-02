"""
実装1：LLM単体利用 (run_llm_only.py)
目的: 外部情報を一切与えなかった場合の、LLMの基準（ベースライン）を確認する。
"""

from langchain_google_vertexai import ChatVertexAI


def main():
    # ChatVertexAIをgemini-2.5-flashモデルで初期化
    llm = ChatVertexAI(model_name="gemini-2.5-flash", temperature=0.1)

    # 質問を定義
    question = "エラーコードE-404の対処法は？"

    print("=== 実装1: LLM単体利用 ===")
    print(f"質問: {question}")
    print("-" * 50)

    # llm.invoke()で直接実行
    response = llm.invoke(question)

    print("回答:")
    print(response.content)
    print("-" * 50)


if __name__ == "__main__":
    main()
