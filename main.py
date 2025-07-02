"""
メインスクリプト: 5つのRAG手法の比較実行
各種情報提供手法の比較用RAGプロトタイプ群の実行
"""

import sys
import time


def run_prototype(module_name, description):
    """プロトタイプを実行"""
    print("=" * 80)
    print(f"実行中: {description}")
    print("=" * 80)

    try:
        # モジュールを動的にインポートして実行
        module = __import__(module_name)
        module.main()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    print("\n")
    time.sleep(2)  # 次の実行まで少し待機


def main():
    print("🚀 各種情報提供手法の比較用RAGプロトタイプ群を実行します\n")

    prototypes = [("run_llm_only", "実装1: LLM単体利用"), ("run_prompt_stuffing", "実装2: プロンプトスタッフィング"),
                  ("run_rag_only", "実装3: RAGのみ"),
                  ("run_function_calling_only", "実装4: Function Callingのみ"),
                  ("run_rag_plus_fancall", "実装5: RAG + Function Calling")]

    print("実行予定のプロトタイプ:")
    for i, (_, desc) in enumerate(prototypes, 1):
        print(f"  {i}. {desc}")

    print("\n" + "=" * 80)
    print("実行を開始します...")
    print("=" * 80)

    for module_name, description in prototypes:
        run_prototype(module_name, description)

    print("🎉 全てのプロトタイプの実行が完了しました！")
    print("\n📊 結果の比較:")
    print("- 実装1: 外部情報なしのベースライン性能")
    print("- 実装2: 全情報を含む力技アプローチ")
    print("- 実装3: 現代的なRAGの基本形")
    print("- 実装4: LLMの自律的なツール使用")
    print("- 実装5: RAGとFunction Callingの組み合わせ（推奨）")


if __name__ == "__main__":
    main()
