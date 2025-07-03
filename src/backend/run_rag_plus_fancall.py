"""
実装5：RAG + Function Calling (run_rag_plus_fancall.py)
目的: RAGの強力な検索能力をツール化し、LLMに他のツールと使い分けさせる、最も高度で推奨される構成を実装する。
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List

from env_utils import create_vertex_ai_llm, setup_environment
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import tool
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# 環境変数を読み込み
setup_environment()

# グローバル変数でretrieverを保持
retriever = None


def setup_rag_retriever(knowledge_file: Path):
    """RAG用のretrieverを設定"""
    global retriever

    print("   RAG Retrieverを準備中...")

    # ドキュメント読み込み
    loader = TextLoader(str(knowledge_file), encoding="utf-8")
    documents = loader.load()

    # テキスト分割
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500,
                                                   chunk_overlap=50,
                                                   separators=["\n\n", "\n", "。", "、", " ", ""])
    splits = text_splitter.split_documents(documents)

    # ベクトルストア構築
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(splits, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    print(f"   RAG準備完了（{len(splits)}個のチャンク）")
    return len(splits)


@tool
def search_knowledge_base(query: str) -> str:
    """製品取扱説明書のナレッジベースを高度な意味検索で検索します。
    
    Args:
        query: 検索したい内容を表すクエリ
        
    Returns:
        関連する情報のテキスト
    """
    global retriever

    if retriever is None:
        return "エラー: ナレッジベースが初期化されていません"

    # RAGのretrieverを使用して検索
    docs = retriever.invoke(query)

    if docs:
        result = "\n\n".join([doc.page_content for doc in docs])
        return f"検索結果:\n{result}"
    else:
        return f"'{query}'に関する情報は見つかりませんでした。"


@tool
def get_robot_serial_number() -> str:
    """ロボットのシリアル番号を取得します。
    
    Returns:
        ロボットのシリアル番号
    """
    # ダミーのシリアル番号を返す
    return "AW3-2024-001255"


async def process_rag_plus_function_calling(user_query: str,
                                            knowledge_file: Path,
                                            demo_mode: bool = False) -> Dict[str, Any]:
    """RAG + Function Callingのモードで処理を実行する
    
    Args:
        user_query: ユーザーからの質問
        knowledge_file: ナレッジベースファイルのパス
        demo_mode: デモモード（詳細なログ出力）
        
    Returns:
        Dict containing response, intermediate_steps, and actual_prompt
    """
    intermediate_steps = []

    if demo_mode:
        print("=== 実装5: RAG + Function Calling ===")

    # 1. RAG Retrieverの準備
    if demo_mode:
        print("1. RAG Retrieverを準備中...")

    chunk_count = setup_rag_retriever(knowledge_file)
    intermediate_steps.append({
        "step": 1,
        "action": "RAG Retriever準備完了",
        "details": f"ナレッジベースを{chunk_count}個のチャンクに分割"
    })

    # 2. エージェントの構築
    if demo_mode:
        print("2. エージェントを構築中...")

    # LLMを初期化
    llm = create_vertex_ai_llm()

    # ツールリストを定義
    tools = [search_knowledge_base, get_robot_serial_number]

    # エージェント用のプロンプトテンプレート
    prompt = ChatPromptTemplate.from_messages([("system", "あなたは製品「Auto-Welder V3」の技術サポート担当者です。"
                                                "利用可能なツールを使用して、製品取扱説明書の内容に基づいて正確で有用な回答を提供してください。"
                                                "質問に関連する情報をツールで検索し、その内容を参考にして回答してください。"
                                                "必要に応じて複数のツールを組み合わせて使用することができます。"),
                                               ("placeholder", "{chat_history}"),
                                               ("human", "{input}"),
                                               ("placeholder", "{agent_scratchpad}")])
    # ツール呼び出しエージェントを作成
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=demo_mode)

    if demo_mode:
        print("   エージェントの構築が完了しました")

    intermediate_steps.append({
        "step": 2,
        "action": "エージェント構築完了",
        "details": f"ツール数: {len(tools)}, プロンプトテンプレート設定完了"
    })

    # 3. 質問実行
    if demo_mode:
        print(f"\n質問: {user_query}")
        print("-" * 70)

    # エージェントで実行
    response = agent_executor.invoke({"input": user_query})
    final_answer = response["output"]

    # 実際のプロンプトを構築（エージェントが使用する基本的なプロンプト）
    actual_prompt = f"""あなたは製品「Auto-Welder V3」の技術サポート担当者です。
利用可能なツールを使用して、製品取扱説明書の内容に基づいて正確で有用な回答を提供してください。
質問に関連する情報をツールで検索し、その内容を参考にして回答してください。

質問: {user_query}"""

    intermediate_steps.append({
        "step": 3,
        "action": "エージェント実行完了",
        "details": "LLMエージェントが質問に対する回答を生成しました"
    })

    if demo_mode:
        print("\n" + "=" * 70)
        print("最終回答:")
        print(final_answer)
        print("=" * 70)

    return {
        "response": final_answer,
        "intermediate_steps": intermediate_steps,
        "actual_prompt": actual_prompt
    }


def main():
    """メイン関数 - 直接実行用"""

    async def run():
        knowledge_file = Path(__file__).parent.parent.parent / "data" / "knowledge.txt"
        return await process_rag_plus_function_calling("エラーコードE-404の対処法は？",
                                                       knowledge_file,
                                                       demo_mode=True)

    return asyncio.run(run())


if __name__ == "__main__":
    main()
