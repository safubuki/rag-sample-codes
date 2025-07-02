import asyncio
from pathlib import Path

from run_rag_only import process_rag_only


async def test_improved_rag():
    knowledge_path = Path('../../data/knowledge.txt')

    queries = ['定期メンテナンス情報を教えてください', '500時間ごとのメンテナンス内容は？', 'エラーコードE-404の対処法は？']

    for query in queries:
        print(f'\n=== クエリ: {query} ===')
        result = await process_rag_only(query, knowledge_path)

        # デバッグ情報の確認
        for step in result['intermediate_steps']:
            if step['step'] == 'retrieve':
                print(f"デバッグ情報: {step['debug_info']}")
                break

        print(f'回答: {result["response"]}')
        print('-' * 50)


if __name__ == "__main__":
    asyncio.run(test_improved_rag())
