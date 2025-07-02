"""
実装2：プロンプトスタッフィング (run_prompt_stuffing.py)
目的: LLMの広大なコンテキストウィンドウを使い、力技で全ての情報を与える手法の挙動を確認する。
"""

from langchain_google_vertexai import ChatVertexAI


def main():
    # ChatVertexAIをgemini-2.5-flashモデルで初期化
    llm = ChatVertexAI(model_name="gemini-2.5-flash", temperature=0.1)

    # knowledge.txtの全内容を読み込み
    with open("knowledge.txt", "r", encoding="utf-8") as f:
        knowledge_content = f.read()

    # 質問を定義
    question = "エラーコードE-404の対処法は？"

    # ヘッダーと質問を組み合わせた最終的なプロンプトを作成
    prompt = f"""以下の製品取扱説明書を参考にして、質問に答えてください。

=== 製品取扱説明書 ===
{knowledge_content}

=== 質問 ===
{question}

=== 回答 ===
製品取扱説明書の内容に基づいて、正確な情報を提供してください。"""

    print("=== 実装2: プロンプトスタッフィング ===")
    print(f"質問: {question}")
    print("-" * 50)

    # llm.invoke()で実行
    response = llm.invoke(prompt)

    print("回答:")
    print(response.content)
    print("-" * 50)


if __name__ == "__main__":
    main()
