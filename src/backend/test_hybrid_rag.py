"""
ハイブリッド検索RAGシステムのテストスクリプト
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run_rag_advanced import process_rag_advanced
from run_rag_only import process_rag_only


async def test_queries():
    """さまざまなタイプのクエリでテスト"""
    test_queries = [
        # 短いクエリ（クエリ拡張なし）
        "ソフトウェア設定",
        "メンテナンス",
        "エラー",

        # エラーコード（キーワード検索で高精度）
        "E-404",
        "E-201",

        # 長い詳細なクエリ（クエリ拡張なし）
        "ロボットの定期的なメンテナンス手順について詳しく教えてください",

        # 中程度のクエリ（クエリ拡張あり）
        "バッテリーの問題",
    ]

    print("=" * 80)
    print("ハイブリッド検索RAGシステムテスト")
    print("=" * 80)

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 テスト {i}: 「{query}」")
        print("-" * 50)

        # 知識ベースのパス（絶対パスで確実に指定）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        knowledge_path = os.path.join(current_dir, "..", "..", "data", "knowledge.txt")
        knowledge_path = os.path.abspath(knowledge_path)

        # RAG Onlyでテスト
        print("\n📝 RAG Only結果:")
        try:
            result_only = await process_rag_only(query, knowledge_path)
            response = result_only["response"]
            print(f"回答長: {len(response)} 文字")
            print(f"回答: {response[:200]}..." if len(response) > 200 else f"回答: {response}")
        except Exception as e:
            print(f"エラー: {e}")

        # Advanced RAGでテスト
        print("\n🚀 Advanced RAG結果:")
        try:
            result_advanced = await process_rag_advanced(query, knowledge_path)
            response = result_advanced["response"]
            stats = result_advanced["advanced_rag_stats"]
            print(f"回答長: {len(response)} 文字")
            print(f"回答: {response[:200]}..." if len(response) > 200 else f"回答: {response}")
            print(f"統計: クエリ拡張={stats.get('query_expansion_applied', False)}, "
                  f"候補数={stats.get('initial_candidates', 0)}, "
                  f"最終チャンク数={stats.get('final_chunks', 0)}")
        except Exception as e:
            print(f"エラー: {e}")

        print("\n" + "=" * 50)


if __name__ == "__main__":
    asyncio.run(test_queries())
