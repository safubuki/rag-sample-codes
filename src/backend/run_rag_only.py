"""
実装3：RAGのみ (run_rag_only.py)
目的: 現代的なRAGアーキテクチャの基本形を実装する。
"""

import asyncio
import re
import time
from pathlib import Path
from typing import Any, Dict, List

from env_utils import create_vertex_ai_llm, setup_environment
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# 環境変数を読み込み
setup_environment()


def _hybrid_retrieval(query: str, splits: List[Document], retriever) -> List[Document]:
    """ハイブリッド検索：ベクトル検索とキーワード検索を組み合わせる"""

    # 1. ベクトル検索
    vector_docs = retriever.get_relevant_documents(query)

    # 2. キーワード検索の実行
    keyword_docs = []

    # エラーコード検索（E-XXX形式）
    error_codes = re.findall(r'E-\d+', query)
    if error_codes:
        for doc in splits:
            for error_code in error_codes:
                if error_code in doc.page_content:
                    keyword_docs.append(doc)
                    break

    # メンテナンス関連キーワード検索
    maintenance_keywords = ["メンテナンス", "定期", "保守", "点検", "交換", "清掃"]
    is_maintenance_query = any(keyword in query for keyword in maintenance_keywords)
    if is_maintenance_query:
        for doc in splits:
            if any(keyword in doc.page_content for keyword in maintenance_keywords):
                keyword_docs.append(doc)

    # 一般的なキーワード検索（クエリの重要な単語）
    query_words = [word for word in query.split() if len(word) > 2]
    for doc in splits:
        for word in query_words:
            if word in doc.page_content:
                keyword_docs.append(doc)
                break

    # 3. 結果の統合と重複除去
    combined_docs = []
    seen_content = set()

    # ベクトル検索結果を優先（関連性が高い）
    for doc in vector_docs:
        if doc.page_content not in seen_content:
            combined_docs.append(doc)
            seen_content.add(doc.page_content)

    # キーワード検索結果を追加（重複を除く）
    for doc in keyword_docs:
        if doc.page_content not in seen_content:
            combined_docs.append(doc)
            seen_content.add(doc.page_content)

    # 最大チャンク数に制限
    max_chunks = 5
    return combined_docs[:max_chunks]


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

    # 3. ハイブリッド検索実行
    retrieved_docs = _hybrid_retrieval(query, splits, retriever)

    context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    # デバッグ情報を追加
    search_debug_info = f"ハイブリッド検索で取得されたチャンク: {len(retrieved_docs)}個"
    if retrieved_docs:
        search_debug_info += f", 最初のチャンク内容の一部: {retrieved_docs[0].page_content[:100]}..."

    intermediate_steps.append({
        "step": "hybrid_retrieval",
        "description": f"ハイブリッド検索で{len(retrieved_docs)}個のチャンクを取得",
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
    knowledge_path = Path("../../data/knowledge.txt")

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
