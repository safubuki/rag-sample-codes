"""
RAGエンジンの実装
5つの異なる処理モードに対応
"""

import asyncio
import os
import time
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

import structlog
from dotenv import load_dotenv
from env_utils import (check_google_cloud_auth, create_vertex_ai_llm, get_google_cloud_project,
                       get_google_credentials, setup_environment)
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import tool
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import ChatVertexAI

# 環境変数を読み込み
setup_environment()

logger = structlog.get_logger()


class ExecutionMode(Enum):
    LLM_ONLY = "llm_only"
    PROMPT_STUFFING = "prompt_stuffing"
    RAG_ONLY = "rag_only"
    FUNCTION_CALLING = "function_calling"
    RAG_FUNCTION_CALLING = "rag_function_calling"


class BaseRAGEngine(ABC):
    """RAGエンジンの基底クラス"""

    def __init__(self, knowledge_path: Path):
        self.knowledge_path = knowledge_path

        # Google Cloud プロジェクトIDを取得
        project_id = get_google_cloud_project()
        if not project_id:
            logger.warning("GOOGLE_CLOUD_PROJECT環境変数が設定されていません。デフォルトプロジェクトを使用します。")

        # 認証状態をチェック
        auth_available = check_google_cloud_auth()

        try:
            # Vertex AI LLMを初期化（共通関数を使用）
            self.llm = create_vertex_ai_llm()
            logger.info("Vertex AI LLMの初期化が成功しました")
        except Exception as e:
            logger.error(f"Vertex AI LLMの初期化に失敗しました: {e}")
            logger.info("認証設定を確認してください")
            # エラーを再発生させて呼び出し元で適切にハンドリング
            raise

    @abstractmethod
    async def process_async(self, query: str, demo_mode: bool = False) -> Dict[str, Any]:
        """非同期でクエリを処理"""
        pass

    async def _demo_delay(self, demo_mode: bool, delay: float = 0.5):
        """デモモード用の遅延"""
        if demo_mode:
            await asyncio.sleep(delay)


class LLMOnlyEngine(BaseRAGEngine):
    """実装1: LLM単体利用"""

    async def process_async(self, query: str, demo_mode: bool = False) -> Dict[str, Any]:
        logger.info("LLM Only processing started", query=query)

        intermediate_steps = [{
            "step": "initialize",
            "description": "LLMを初期化",
            "timestamp": time.time()
        }]

        await self._demo_delay(demo_mode, 1.0)

        intermediate_steps.append({
            "step": "llm_invoke",
            "description": "LLMに直接クエリを送信",
            "timestamp": time.time()
        })

        response = self.llm.invoke(query)

        await self._demo_delay(demo_mode, 0.5)

        intermediate_steps.append({
            "step": "complete",
            "description": "処理完了",
            "timestamp": time.time()
        })

        return {"response": response.content, "intermediate_steps": intermediate_steps}


class PromptStuffingEngine(BaseRAGEngine):
    """実装2: プロンプトスタッフィング"""

    async def process_async(self, query: str, demo_mode: bool = False) -> Dict[str, Any]:
        logger.info("Prompt Stuffing processing started", query=query)

        intermediate_steps = [{
            "step": "initialize",
            "description": "エンジンを初期化",
            "timestamp": time.time()
        }]

        await self._demo_delay(demo_mode, 0.5)

        # knowledge.txtの全内容を読み込み
        with open(self.knowledge_path, "r", encoding="utf-8") as f:
            knowledge_content = f.read()

        intermediate_steps.append({
            "step": "load_knowledge",
            "description": f"ナレッジファイルを読み込み ({len(knowledge_content)}文字)",
            "data": {
                "content_length": len(knowledge_content)
            },
            "timestamp": time.time()
        })

        await self._demo_delay(demo_mode, 1.0)

        # プロンプト作成
        prompt = f"""以下の製品取扱説明書を参考にして、質問に答えてください。

=== 製品取扱説明書 ===
{knowledge_content}

=== 質問 ===
{query}

=== 回答 ===
製品取扱説明書の内容に基づいて、正確な情報を提供してください。"""

        intermediate_steps.append({
            "step": "create_prompt",
            "description": "ナレッジ情報を含むプロンプトを作成",
            "data": {
                "prompt_length": len(prompt)
            },
            "timestamp": time.time()
        })

        await self._demo_delay(demo_mode, 1.0)

        response = self.llm.invoke(prompt)

        intermediate_steps.append({
            "step": "complete",
            "description": "処理完了",
            "timestamp": time.time()
        })

        return {"response": response.content, "intermediate_steps": intermediate_steps}


class RAGOnlyEngine(BaseRAGEngine):
    """実装3: RAGのみ"""

    def __init__(self, knowledge_path: Path):
        super().__init__(knowledge_path)
        self.retriever = None
        self.rag_chain = None

    async def _setup_rag(self, demo_mode: bool = False) -> List[Dict]:
        """RAGシステムのセットアップ"""
        intermediate_steps = []

        if self.retriever is not None:
            return intermediate_steps

        # ドキュメント読み込み
        loader = TextLoader(str(self.knowledge_path), encoding="utf-8")
        documents = loader.load()

        intermediate_steps.append({
            "step": "load_documents",
            "description": "ドキュメントを読み込み",
            "data": {
                "document_count": len(documents)
            },
            "timestamp": time.time()
        })

        await self._demo_delay(demo_mode, 1.0)

        # テキスト分割
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500,
                                                       chunk_overlap=50,
                                                       separators=["\n\n", "\n", "。", "、", " ", ""])
        splits = text_splitter.split_documents(documents)

        intermediate_steps.append({
            "step": "split_documents",
            "description": f"ドキュメントを{len(splits)}個のチャンクに分割",
            "data": {
                "chunk_count": len(splits)
            },
            "timestamp": time.time()
        })

        await self._demo_delay(demo_mode, 1.5)

        # ベクトルストア構築
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = FAISS.from_documents(splits, embeddings)
        self.retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        intermediate_steps.append({
            "step": "create_vectorstore",
            "description": "ベクトルストアを構築",
            "data": {
                "embedding_model": "all-MiniLM-L6-v2"
            },
            "timestamp": time.time()
        })

        await self._demo_delay(demo_mode, 1.0)

        # RAGチェーン構築
        prompt_template = ChatPromptTemplate.from_template("""以下のコンテキスト情報を使用して質問に答えてください。
コンテキストに答えが含まれていない場合は、「提供された情報では回答できません」と答えてください。

コンテキスト:
{context}

質問: {question}

回答:""")

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        self.rag_chain = ({
            "context": self.retriever | format_docs,
            "question": RunnablePassthrough()
        } | prompt_template | self.llm | StrOutputParser())

        intermediate_steps.append({
            "step": "setup_rag_chain",
            "description": "RAGチェーンをセットアップ",
            "timestamp": time.time()
        })

        return intermediate_steps

    async def process_async(self, query: str, demo_mode: bool = False) -> Dict[str, Any]:
        logger.info("RAG Only processing started", query=query)

        # RAGセットアップ
        intermediate_steps = await self._setup_rag(demo_mode)

        await self._demo_delay(demo_mode, 0.5)

        # 関連文書検索
        docs = self.retriever.invoke(query)
        retrieved_content = [doc.page_content for doc in docs]

        intermediate_steps.append({
            "step": "retrieve_documents",
            "description": f"{len(docs)}個の関連文書を検索",
            "data": {
                "retrieved_chunks": retrieved_content,
                "chunk_count": len(docs)
            },
            "timestamp": time.time()
        })

        await self._demo_delay(demo_mode, 1.0)

        # RAGチェーン実行
        response = self.rag_chain.invoke(query)

        intermediate_steps.append({
            "step": "complete",
            "description": "RAG処理完了",
            "timestamp": time.time()
        })

        return {"response": response, "intermediate_steps": intermediate_steps}


class FunctionCallingEngine(BaseRAGEngine):
    """実装4: Function Callingのみ"""

    def __init__(self, knowledge_path: Path):
        super().__init__(knowledge_path)
        self.llm_with_tools = None
        self._setup_tools()

    def _setup_tools(self):
        """ツールをセットアップ"""

        @tool
        def search_manual(query: str) -> str:
            """製品取扱説明書内でテキスト検索を行います。
            
            Args:
                query: 検索したいキーワードや文字列
                
            Returns:
                検索結果として見つかった関連する情報
            """
            with open(self.knowledge_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split('\n')
            relevant_lines = []

            for line in lines:
                if query.lower() in line.lower():
                    relevant_lines.append(line.strip())

            if relevant_lines:
                return "\n".join(relevant_lines)
            else:
                return f"'{query}'に関する情報は見つかりませんでした。"

        self.search_manual = search_manual
        self.llm_with_tools = self.llm.bind_tools([search_manual])

    async def process_async(self, query: str, demo_mode: bool = False) -> Dict[str, Any]:
        logger.info("Function Calling processing started", query=query)

        intermediate_steps = [{
            "step": "initialize",
            "description": "Function Callingエンジンを初期化",
            "timestamp": time.time()
        }]

        await self._demo_delay(demo_mode, 0.5)

        # 最初のLLM呼び出し（ツール使用判断）
        response = self.llm_with_tools.invoke(query)

        intermediate_steps.append({
            "step": "llm_tool_decision",
            "description": "LLMがツール使用を判断",
            "data": {
                "has_tool_calls": hasattr(response, 'tool_calls') and bool(response.tool_calls)
            },
            "timestamp": time.time()
        })

        await self._demo_delay(demo_mode, 1.0)

        # ツール呼び出しの処理
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_call = response.tool_calls[0]
            tool_name = tool_call['name']
            tool_args = tool_call['args']

            intermediate_steps.append({
                "step": "tool_execution",
                "description": f"ツール '{tool_name}' を実行",
                "data": {
                    "tool_name": tool_name,
                    "tool_args": tool_args
                },
                "timestamp": time.time()
            })

            await self._demo_delay(demo_mode, 1.0)

            # ツール実行
            tool_result = self.search_manual.invoke(tool_args)

            intermediate_steps.append({
                "step": "tool_result",
                "description": "ツール実行結果を取得",
                "data": {
                    "tool_result":
                        tool_result[:200] + "..." if len(tool_result) > 200 else tool_result
                },
                "timestamp": time.time()
            })

            await self._demo_delay(demo_mode, 1.0)

            # 最終回答生成
            final_prompt = f"""以下のツール実行結果を基に、ユーザーの質問に答えてください。

質問: {query}

ツール実行結果:
{tool_result}

回答:"""

            final_response = self.llm.invoke(final_prompt)
            final_answer = final_response.content
        else:
            final_answer = response.content

        intermediate_steps.append({
            "step": "complete",
            "description": "Function Calling処理完了",
            "timestamp": time.time()
        })

        return {"response": final_answer, "intermediate_steps": intermediate_steps}


class RAGFunctionCallingEngine(BaseRAGEngine):
    """実装5: RAG + Function Calling"""

    def __init__(self, knowledge_path: Path):
        super().__init__(knowledge_path)
        self.retriever = None
        self.agent_executor = None

    async def _setup_rag_agent(self, demo_mode: bool = False) -> List[Dict]:
        """RAGエージェントのセットアップ"""
        intermediate_steps = []

        if self.agent_executor is not None:
            return intermediate_steps

        # RAGシステムのセットアップ
        loader = TextLoader(str(self.knowledge_path), encoding="utf-8")
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500,
                                                       chunk_overlap=50,
                                                       separators=["\n\n", "\n", "。", "、", " ", ""])
        splits = text_splitter.split_documents(documents)

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = FAISS.from_documents(splits, embeddings)
        self.retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        intermediate_steps.append({
            "step": "setup_rag",
            "description": f"RAGシステムをセットアップ（{len(splits)}チャンク）",
            "data": {
                "chunk_count": len(splits)
            },
            "timestamp": time.time()
        })

        await self._demo_delay(demo_mode, 2.0)

        # ツール定義
        @tool
        def search_knowledge_base(query: str) -> str:
            """製品取扱説明書のナレッジベースを高度な意味検索で検索します。
            
            Args:
                query: 検索したい内容を表すクエリ
                
            Returns:
                関連する情報のテキスト
            """
            docs = self.retriever.invoke(query)
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
            return "AW3-2024-001255"

        tools = [search_knowledge_base, get_robot_serial_number]

        # エージェント用プロンプト
        prompt = ChatPromptTemplate.from_messages([("system", "あなたは製品「Auto-Welder V3」の技術サポート担当者です。"
                                                    "利用可能なツールを使用して、ユーザーの質問に正確で有用な回答を提供してください。"
                                                    "必要に応じて複数のツールを組み合わせて使用することができます。"),
                                                   ("placeholder", "{chat_history}"),
                                                   ("human", "{input}"),
                                                   ("placeholder", "{agent_scratchpad}")])

        # エージェント作成
        agent = create_tool_calling_agent(self.llm, tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

        intermediate_steps.append({
            "step": "setup_agent",
            "description": "RAG + Function Callingエージェントをセットアップ",
            "data": {
                "tool_count": len(tools)
            },
            "timestamp": time.time()
        })

        return intermediate_steps

    async def process_async(self, query: str, demo_mode: bool = False) -> Dict[str, Any]:
        logger.info("RAG + Function Calling processing started", query=query)

        # エージェントセットアップ
        intermediate_steps = await self._setup_rag_agent(demo_mode)

        await self._demo_delay(demo_mode, 0.5)

        intermediate_steps.append({
            "step": "agent_execution",
            "description": "エージェントが自律的にツールを選択・実行",
            "timestamp": time.time()
        })

        await self._demo_delay(demo_mode, 1.5)

        # エージェント実行
        response = self.agent_executor.invoke({"input": query})

        intermediate_steps.append({
            "step": "complete",
            "description": "RAG + Function Calling処理完了",
            "timestamp": time.time()
        })

        return {"response": response["output"], "intermediate_steps": intermediate_steps}


class RAGEngineFactory:
    """RAGエンジンのファクトリ"""

    def __init__(self, knowledge_path: Path):
        self.knowledge_path = knowledge_path

    def create_engine(self, mode: ExecutionMode) -> BaseRAGEngine:
        """指定されたモードのエンジンを作成"""
        engines = {
            ExecutionMode.LLM_ONLY: LLMOnlyEngine,
            ExecutionMode.PROMPT_STUFFING: PromptStuffingEngine,
            ExecutionMode.RAG_ONLY: RAGOnlyEngine,
            ExecutionMode.FUNCTION_CALLING: FunctionCallingEngine,
            ExecutionMode.RAG_FUNCTION_CALLING: RAGFunctionCallingEngine,
        }

        engine_class = engines.get(mode)
        if engine_class is None:
            raise ValueError(f"Unknown execution mode: {mode}")

        return engine_class(self.knowledge_path)
