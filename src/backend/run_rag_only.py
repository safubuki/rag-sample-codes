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

    # テキスト分割
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500,
                                                   chunk_overlap=50,
                                                   separators=["\n\n", "\n", "。", "、", " ", ""])
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
    # チャンク数が少ない場合は、検索結果を1つに制限
    max_chunks = min(1, len(splits))  # 最大でも1つのチャンクのみ取得
    retriever = vectorstore.as_retriever(search_kwargs={"k": max_chunks})

    # 3. 検索実行
    retrieved_docs = retriever.get_relevant_documents(query)
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    intermediate_steps.append({
        "step": "retrieve",
        "description": f"関連する{len(retrieved_docs)}個のチャンクを検索",
        "timestamp": time.time()
    })

    if demo_mode:
        await asyncio.sleep(1.0)

    # 4. プロンプト作成とRAGチェーン構築
    prompt_template = ChatPromptTemplate.from_template(
        "以下のコンテキスト情報を使用して質問に答えてください。\n"
        "コンテキストに答えが含まれていない場合は、「提供された情報では回答できません」と答えてください。\n\n"
        "コンテキスト:\n{context}\n\n"
        "質問: {question}\n\n"
        "回答:")

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
