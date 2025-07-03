"""
実装4：高度なRAG (run_rag_advanced.py)
目的: Query Expansion、Re-ranking、Context Compressionを実装した高度なRAGアーキテクチャ。
"""

import asyncio
import re
import time
from pathlib import Path
from typing import Any, Dict, List

from env_utils import create_vertex_ai_llm, setup_environment
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.document_transformers import LongContextReorder
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from sentence_transformers import CrossEncoder

# 環境変数を読み込み
setup_environment()

# CrossEncoderを グローバルに初期化してキャッシュ
_cross_encoder = None


def get_cross_encoder():
    """CrossEncoderをシングルトンパターンで取得"""
    global _cross_encoder
    if _cross_encoder is None:
        _cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    return _cross_encoder


async def _generate_queries_optimized(question: str, llm: Any) -> List[str]:
    """最適化されたクエリ拡張（より短いプロンプト）"""
    expansion_prompt = ChatPromptTemplate.from_template("元の質問: {query}\n\n"
                                                        "上記を異なる表現で書き換えた2つの検索クエリを生成してください:\n"
                                                        "1. [クエリ1]\n"
                                                        "2. [クエリ2]")

    chain = expansion_prompt | llm | StrOutputParser()
    result = await chain.ainvoke({"query": question})

    # 結果から追加クエリを抽出
    expanded_queries = [question]  # 元のクエリを含める
    lines = result.strip().split('\n')
    for line in lines:
        # 番号付きリストから抽出
        match = re.match(r'\d+\.\s*(.+)', line.strip())
        if match:
            expanded_queries.append(match.group(1).strip())

    return expanded_queries[:3]  # 元のクエリ + 最大2つの追加クエリ（計3つに削減）


def _rerank_documents_optimized(query: str, documents: List[Any], top_k: int = 4) -> List[Any]:
    """CrossEncoderによる高精度再ランキング（高度RAGの核心機能）"""
    if not documents:
        return documents

    # キャッシュされたCrossEncoderを取得
    reranker = get_cross_encoder()

    # ドキュメント数を制限してパフォーマンス向上
    max_candidates = min(20, len(documents))  # より多くの候補から選択
    documents = documents[:max_candidates]

    # クエリとドキュメントのペアを作成
    query_doc_pairs = []
    for doc in documents:
        content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
        # より多くのコンテンツを使用して精度向上（500→800）
        content = content[:800] if len(content) > 800 else content
        query_doc_pairs.append([query, content])

    # CrossEncoderでスコアを計算（これがベーシック版との違い）
    scores = reranker.predict(query_doc_pairs)

    # スコアでソートして上位を選択
    scored_docs = list(zip(documents, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)

    return [doc for doc, _ in scored_docs[:top_k]]


def _apply_long_context_reorder(documents: List[Any]) -> List[Any]:
    """LongContextReorderを実装：重要なドキュメントを最初と最後に配置"""
    if len(documents) <= 2:
        return documents

    # LongContextReorderの実装
    # 最も重要（最初のドキュメント）を最初に
    # 2番目に重要なドキュメントを最後に
    # 残りは中間に配置（Lost in the Middle対策）
    reordered = [documents[0]]  # 最も重要

    if len(documents) > 2:
        reordered.extend(documents[2:])  # 中間のドキュメント
        reordered.append(documents[1])  # 2番目に重要を最後に

    return reordered


async def process_rag_advanced(query: str,
                               knowledge_path: Path,
                               demo_mode: bool = False,
                               enable_query_expansion: bool = True,
                               enable_reranking: bool = True) -> Dict[str, Any]:
    """高度なRAG処理：Query Expansion + Re-ranking + Context Compression（最適化版）"""

    intermediate_steps = [{
        "step": "initialize",
        "description": "最適化された高度なRAGエンジンを初期化",
        "timestamp": time.time()
    }]

    if demo_mode:
        await asyncio.sleep(0.3)  # デモモード時間短縮

    # LLMを初期化（クエリ拡張で使用）
    llm = create_vertex_ai_llm()

    # 1. ナレッジベース準備
    loader = TextLoader(str(knowledge_path), encoding="utf-8")
    documents = loader.load()

    # テキスト分割
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, chunk_overlap=150, separators=["## ", "\n\n", "\n", "。", "、", " ", ""])
    splits = text_splitter.split_documents(documents)

    intermediate_steps.append({
        "step": "setup_vectorstore",
        "description": f"ドキュメントを{len(splits)}個のチャンクに分割し、ベクトルストアを構築",
        "timestamp": time.time()
    })

    if demo_mode:
        await asyncio.sleep(1.0)

    # 2. ベクトルストア構築（検索数を調整）
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(splits, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 12})  # 再ランキング用に多めに取得

    # 3. クエリ拡張（条件付き最適化版）
    if enable_query_expansion:
        expanded_queries = await _generate_queries_optimized(query, llm)
        intermediate_steps.append({
            "step": "query_expansion",
            "description": f"クエリを{len(expanded_queries)}個に拡張（最適化）",
            "expanded_queries": expanded_queries,
            "timestamp": time.time()
        })
    else:
        expanded_queries = [query]  # 元のクエリのみ
        intermediate_steps.append({
            "step": "query_expansion_skipped",
            "description": "クエリ拡張をスキップ（高速モード）",
            "timestamp": time.time()
        })

    if demo_mode:
        await asyncio.sleep(0.3)

    # 4. 複数クエリでドキュメント検索（検索数を削減）
    all_retrieved_docs = []
    seen_content = set()

    for exp_query in expanded_queries:
        docs = retriever.get_relevant_documents(exp_query)
        for doc in docs:
            # 重複を除去
            if doc.page_content not in seen_content:
                all_retrieved_docs.append(doc)
                seen_content.add(doc.page_content)

    intermediate_steps.append({
        "step": "multi_query_retrieval",
        "description": f"検索で{len(all_retrieved_docs)}個の候補ドキュメントを取得",
        "timestamp": time.time()
    })

    if demo_mode:
        await asyncio.sleep(0.3)

    # 5. CrossEncoderによる再ランキング（これが高度版の核心機能）
    if enable_reranking and len(all_retrieved_docs) > 3:
        reranked_docs = _rerank_documents_optimized(query, all_retrieved_docs, top_k=4)
        intermediate_steps.append({
            "step":
                "reranking",
            "description":
                f"CrossEncoderで{len(all_retrieved_docs)}個から上位{len(reranked_docs)}個を厳選（高度RAG）",
            "timestamp":
                time.time()
        })
    else:
        reranked_docs = all_retrieved_docs[:4]  # 再ランキング無効時は上位4件
        intermediate_steps.append({
            "step": "reranking_skipped",
            "description": f"再ランキングをスキップ、上位{len(reranked_docs)}個を選択（高速モード）",
            "timestamp": time.time()
        })

    if demo_mode:
        await asyncio.sleep(0.3)

    # 6. Long Context Reorder（コンテキスト圧縮）
    final_docs = _apply_long_context_reorder(reranked_docs)
    context = "\n\n".join([doc.page_content for doc in final_docs])

    intermediate_steps.append({
        "step": "context_compression",
        "description": f"最適配置で最終的に{len(final_docs)}個のチャンクを使用",
        "final_chunks_preview": [doc.page_content[:80] + "..." for doc in final_docs[:2]],
        "timestamp": time.time()
    })

    if demo_mode:
        await asyncio.sleep(0.3)

    # 7. プロンプト作成とRAGチェーン構築（短縮版プロンプト）
    prompt_template = ChatPromptTemplate.from_template("以下の製品取扱説明書を参考にして、質問に答えてください。\n\n"
                                                       "=== 製品取扱説明書 ===\n"
                                                       "{context}\n\n"
                                                       "=== 質問 ===\n"
                                                       "{question}\n\n"
                                                       "=== 回答 ===\n"
                                                       "取扱説明書の内容に基づいて、正確な情報を提供してください。")

    # RAGチェーン構築
    rag_chain = ({
        "context": lambda x: context,
        "question": RunnablePassthrough()
    } | prompt_template | llm | StrOutputParser())

    # 最終的なプロンプトを作成（トークン数計算用）
    final_prompt = prompt_template.format(context=context, question=query)

    intermediate_steps.append({
        "step": "generate",
        "description": "最適化されたRAGパイプラインで回答を生成",
        "context_stats": {
            "total_chunks": len(final_docs),
            "total_characters": len(context),
            "expansion_queries_used": len(expanded_queries)
        },
        "timestamp": time.time()
    })

    if demo_mode:
        await asyncio.sleep(0.3)

    # 8. 回答生成
    response = rag_chain.invoke(query)

    intermediate_steps.append({
        "step": "complete",
        "description": "最適化された高度なRAG処理完了",
        "timestamp": time.time()
    })

    return {
        "response": response,
        "intermediate_steps": intermediate_steps,
        "actual_prompt": final_prompt,  # トークン数計算用
        "advanced_rag_stats": {
            "original_query": query,
            "expanded_queries": expanded_queries,
            "initial_candidates": len(all_retrieved_docs),
            "final_chunks": len(final_docs),
            "reranking_applied": enable_reranking and len(all_retrieved_docs) > 3,
            "query_expansion_applied": enable_query_expansion,
            "context_reordering_applied": True,
            "optimization_mode": "high_performance"
        }
    }


def main():
    """直接実行時のテスト用"""
    import asyncio

    # 質問を定義
    question = "エラーコードE-404の対処法は？"
    knowledge_path = Path("knowledge.txt")

    print("=== 実装4: 高度なRAG ===")
    print(f"質問: {question}")
    print("-" * 50)

    # 非同期処理を実行
    result = asyncio.run(process_rag_advanced(question, knowledge_path))

    print("回答:")
    print(result["response"])
    print("-" * 50)
    print("高度なRAG統計:")
    print(result["advanced_rag_stats"])


if __name__ == "__main__":
    main()
