"""
実装3：RAGのみ (run_rag_only.py)
目的: 現代的なRAGアーキテクチャの基本形を実装する。
"""

import asyncio
import time
from pathlib import Path
from typing import Any, Dict

from env_utils import create_vertex_ai_llm, setup_environment
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# 環境変数を読み込み
setup_environment()


async def process_rag_only(query: str,
                           knowledge_path: Path,
                           demo_mode: bool = False) -> Dict[str, Any]:
    """RAG処理"""

    intermediate_steps = [{
        "step": "initialize",
        "description": "RAGエンジンを初期化",
        "timestamp": time.time()
    }]

    if demo_mode:
        await asyncio.sleep(0.5)

    # 1. ナレッジベース準備
    loader = TextLoader(str(knowledge_path), encoding="utf-8")
    documents = loader.load()

    # テキスト分割 - セクション境界を考慮し、より大きなチャンクサイズを使用
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,  # チャンクサイズを大きくしてコンテキストを保持
        chunk_overlap=150,  # オーバーラップを増やして情報の断片化を防ぐ
        separators=["## ", "\n\n", "\n", "。", "、", " ", ""]  # セクションヘッダーを優先
    )
    splits = text_splitter.split_documents(documents)

    intermediate_steps.append({
        "step": "setup_vectorstore",
        "description": f"ドキュメントを{len(splits)}個のチャンクに分割し、ベクトルストアを構築",
        "timestamp": time.time()
    })

    if demo_mode:
        await asyncio.sleep(1.5)

    # 2. ベクトルストア構築
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(splits, embeddings)
    # 検索結果を増やして検索精度を向上（最大5つのチャンクを取得）
    max_chunks = min(5, len(splits))
    retriever = vectorstore.as_retriever(search_kwargs={"k": max_chunks})

    # 3. 検索実行（改良版ハイブリッド検索）
    # ベクトル検索を実行
    retrieved_docs = retriever.get_relevant_documents(query)

    # クエリに「メンテナンス」「定期」などのキーワードが含まれる場合の特別処理
    maintenance_keywords = ["メンテナンス", "定期", "保守", "点検", "交換", "清掃"]
    is_maintenance_query = any(keyword in query for keyword in maintenance_keywords)

    if is_maintenance_query:
        # メンテナンス関連のチャンクを明示的に検索
        maintenance_docs = []
        for doc in splits:
            if any(keyword in doc.page_content for keyword in maintenance_keywords):
                maintenance_docs.append(doc)

        # メンテナンス関連チャンクの中から最も関連性の高いものを追加
        existing_content = {doc.page_content for doc in retrieved_docs}
        for doc in maintenance_docs:
            if doc.page_content not in existing_content:
                retrieved_docs.append(doc)
                if len(retrieved_docs) >= max_chunks:
                    break

    # キーワード検索も実行（特定のエラーコードを探す場合）
    import re
    error_codes = re.findall(r'E-\d+', query)
    if error_codes:
        # エラーコードが含まれるチャンクを明示的に検索
        keyword_docs = []
        for doc in splits:
            for error_code in error_codes:
                if error_code in doc.page_content:
                    keyword_docs.append(doc)
                    break

        # キーワード検索の結果をベクトル検索結果に追加（重複を避ける）
        existing_content = {doc.page_content for doc in retrieved_docs}
        for doc in keyword_docs:
            if doc.page_content not in existing_content:
                retrieved_docs.append(doc)
                if len(retrieved_docs) >= max_chunks:
                    break

    context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    # デバッグ情報を追加
    search_debug_info = f"検索されたチャンク: {len(retrieved_docs)}個"
    if retrieved_docs:
        search_debug_info += f", 最初のチャンク内容の一部: {retrieved_docs[0].page_content[:100]}..."
    if error_codes:
        search_debug_info += f", 検索されたエラーコード: {', '.join(error_codes)}"
    if is_maintenance_query:
        search_debug_info += f", メンテナンス関連クエリとして処理"

    intermediate_steps.append({
        "step": "retrieve",
        "description": f"関連する{len(retrieved_docs)}個のチャンクを検索",
        "debug_info": search_debug_info,
        "retrieved_content_preview": context[:200] + "..." if len(context) > 200 else context,
        "timestamp": time.time()
    })

    if demo_mode:
        await asyncio.sleep(1.0)

    # 4. プロンプト作成とRAGチェーン構築
    prompt_template = ChatPromptTemplate.from_template("以下の製品取扱説明書を参考にして、質問に答えてください。\n\n"
                                                       "=== 製品取扱説明書（関連情報） ===\n"
                                                       "{context}\n\n"
                                                       "=== 質問 ===\n"
                                                       "{question}\n\n"
                                                       "=== 回答 ===\n"
                                                       "製品取扱説明書の内容に基づいて、正確な情報を提供してください。")

    # Vertex AI LLMを初期化
    llm = create_vertex_ai_llm()

    # RAGチェーン構築
    rag_chain = ({
        "context": lambda x: context,
        "question": RunnablePassthrough()
    } | prompt_template | llm | StrOutputParser())

    # 最終的なプロンプトを作成（トークン数計算用）
    final_prompt = prompt_template.format(context=context, question=query)

    intermediate_steps.append({
        "step": "generate",
        "description": "LLMで回答を生成",
        "timestamp": time.time()
    })

    if demo_mode:
        await asyncio.sleep(1.0)

    # 5. 回答生成
    response = rag_chain.invoke(query)

    intermediate_steps.append({"step": "complete", "description": "処理完了", "timestamp": time.time()})

    return {
        "response": response,
        "intermediate_steps": intermediate_steps,
        "actual_prompt": final_prompt  # トークン数計算用に実際のプロンプトを返す
    }


def main():
    """直接実行時のテスト用"""
    import asyncio

    # 質問を定義
    question = "エラーコードE-404の対処法は？"
    knowledge_path = Path("knowledge.txt")

    print("=== 実装3: RAGのみ ===")
    print(f"質問: {question}")
    print("-" * 50)

    # 非同期処理を実行
    result = asyncio.run(process_rag_only(question, knowledge_path))

    print("回答:")
    print(result["response"])
    print("-" * 50)


if __name__ == "__main__":
    main()
