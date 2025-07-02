"""
RAG比較システム - バックエンドAPI
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import structlog
import tiktoken
import uvicorn
from env_utils import get_google_cloud_project, setup_environment
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from logger_config import setup_logging
from pydantic import BaseModel
from rag_engines import ExecutionMode, RAGEngineFactory

# 環境変数を読み込み
setup_environment()

# Google Cloud Project設定の確認
project_id = get_google_cloud_project()
if not project_id:
    print("警告: GOOGLE_CLOUD_PROJECT環境変数が設定されていません。")
    print("以下のいずれかの方法でプロジェクトIDを設定してください:")
    print("1. .envファイルでGOOGLE_CLOUD_PROJECT=your-project-idを設定")
    print("2. 環境変数を設定: set GOOGLE_CLOUD_PROJECT=your-project-id (Windows)")
    print("3. gcloud config set project your-project-id")
    # 実行は継続（デフォルトプロジェクトがある場合は動作する可能性がある）

# ログ設定
setup_logging()
logger = structlog.get_logger()

app = FastAPI(title="RAG比較システム API", description="LLMに外部情報を与える5つの手法を比較するシステム", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.jsのデフォルトポート
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データディレクトリ
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# ディレクトリ作成
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


class ProcessingMode(str, Enum):
    LLM_ONLY = "llm_only"
    PROMPT_STUFFING = "prompt_stuffing"
    RAG_ONLY = "rag_only"
    FUNCTION_CALLING = "function_calling"
    RAG_FUNCTION_CALLING = "rag_function_calling"


class ProcessRequest(BaseModel):
    query: str
    mode: ProcessingMode
    demo_mode: bool = False


class ProcessResponse(BaseModel):
    result: str
    execution_time: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    intermediate_steps: List[Dict]
    log_file: str


class StatusResponse(BaseModel):
    status: str
    current_step: Optional[str] = None
    progress: float = 0.0
    intermediate_data: Optional[Dict] = None


class KnowledgeContent(BaseModel):
    content: str


# トークンカウンター
def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """テキストのトークン数をカウント"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except:
        # フォールバック: 文字数の1/4を概算トークン数とする
        return len(text) // 4


@app.get("/")
async def root():
    return {"message": "RAG比較システム API", "version": "1.0.0"}


@app.get("/knowledge", response_class=FileResponse)
async def get_knowledge_file():
    """knowledge.txtファイルをダウンロード"""
    knowledge_path = DATA_DIR / "knowledge.txt"
    if not knowledge_path.exists():
        raise HTTPException(status_code=404, detail="Knowledge file not found")

    return FileResponse(path=knowledge_path, filename="knowledge.txt", media_type="text/plain")


# ファイルアップロード用エンドポイント（必要な場合は有効化）
# @app.post("/knowledge")
# async def upload_knowledge_file(file: UploadFile = File(...)):
#     """knowledge.txtファイルをアップロード（ファイルアップロード用）"""
#     if file.filename != "knowledge.txt":
#         raise HTTPException(status_code=400, detail="File must be named 'knowledge.txt'")
#
#     knowledge_path = DATA_DIR / "knowledge.txt"
#
#     try:
#         content = await file.read()
#         with open(knowledge_path, "wb") as f:
#             f.write(content)
#
#         logger.info("Knowledge file uploaded", filename=file.filename, size=len(content))
#         return {"message": "Knowledge file uploaded successfully"}
#
#     except Exception as e:
#         logger.error("Failed to upload knowledge file", error=str(e))
#         raise HTTPException(status_code=500, detail=str(e))


@app.get("/knowledge/content")
async def get_knowledge_content():
    """knowledge.txtファイルの内容を取得"""
    knowledge_path = DATA_DIR / "knowledge.txt"
    if not knowledge_path.exists():
        raise HTTPException(status_code=404, detail="Knowledge file not found")

    try:
        with open(knowledge_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        logger.error("Failed to read knowledge file", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/knowledge")
async def update_knowledge_content(request: KnowledgeContent):
    """knowledge.txtファイルの内容を更新"""
    knowledge_path = DATA_DIR / "knowledge.txt"

    try:
        with open(knowledge_path, "w", encoding="utf-8") as f:
            f.write(request.content)

        logger.info("Knowledge content updated", size=len(request.content))
        return {"message": "Knowledge content updated successfully"}

    except Exception as e:
        logger.error("Failed to update knowledge content", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process", response_model=ProcessResponse)
async def process_query(request: ProcessRequest):
    """クエリを処理して結果を返す"""
    start_time = time.time()

    # ログファイル名生成
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    log_filename = f"{timestamp}_llm-rag-exp.jsonl"
    log_path = LOGS_DIR / log_filename

    # 入力トークン数計算
    input_tokens = count_tokens(request.query)

    logger.info("Processing started",
                query=request.query,
                mode=request.mode,
                demo_mode=request.demo_mode,
                input_tokens=input_tokens)

    try:
        # RAGエンジン作成
        engine_factory = RAGEngineFactory(DATA_DIR / "knowledge.txt")

        mode_mapping = {
            ProcessingMode.LLM_ONLY: ExecutionMode.LLM_ONLY,
            ProcessingMode.PROMPT_STUFFING: ExecutionMode.PROMPT_STUFFING,
            ProcessingMode.RAG_ONLY: ExecutionMode.RAG_ONLY,
            ProcessingMode.FUNCTION_CALLING: ExecutionMode.FUNCTION_CALLING,
            ProcessingMode.RAG_FUNCTION_CALLING: ExecutionMode.RAG_FUNCTION_CALLING,
        }

        engine = engine_factory.create_engine(mode_mapping[request.mode])

        # デモモードの場合は遅延を入れる
        if request.demo_mode:
            await asyncio.sleep(1.0)  # 初期遅延

        # 処理実行
        result = await engine.process_async(request.query, demo_mode=request.demo_mode)

        execution_time = time.time() - start_time

        # 出力トークン数計算
        output_tokens = count_tokens(result["response"])
        total_tokens = input_tokens + output_tokens

        # ログ出力
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "execution_mode": request.mode,
            "query": request.query,
            "response": result["response"],
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "execution_time": execution_time,
            "intermediate_steps": result.get("intermediate_steps", []),
            "demo_mode": request.demo_mode,
            "status": "success",
            "error_message": None
        }

        # JSONLファイルに保存
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        logger.info("Processing completed",
                    execution_time=execution_time,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens)

        return ProcessResponse(result=result["response"],
                               execution_time=execution_time,
                               input_tokens=input_tokens,
                               output_tokens=output_tokens,
                               total_tokens=total_tokens,
                               intermediate_steps=result.get("intermediate_steps", []),
                               log_file=log_filename)

    except Exception as e:
        error_message = str(e)
        execution_time = time.time() - start_time

        # エラーログを記録
        error_log_entry = {
            "timestamp": datetime.now().isoformat(),
            "execution_mode": request.mode,
            "query": request.query,
            "response": "",
            "input_tokens": input_tokens,
            "output_tokens": 0,
            "total_tokens": input_tokens,
            "execution_time": execution_time,
            "intermediate_steps": [],
            "demo_mode": request.demo_mode,
            "status": "error",
            "error_message": error_message
        }

        # エラーログもファイルに保存
        error_log_filename = f"{timestamp}_{request.mode.value}-error.jsonl"
        error_log_path = LOGS_DIR / error_log_filename
        with open(error_log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(error_log_entry, ensure_ascii=False) + "\n")

        logger.error("Processing failed", error=error_message)

        # Google Cloud認証関連のエラーの場合、より詳細な情報を提供
        if "DefaultCredentialsError" in error_message or "was not found" in error_message:
            detailed_error = (f"Google Cloud認証エラー: {error_message}\n\n"
                              "解決方法:\n"
                              "1. サービスアカウントキーを設定:\n"
                              "   - .envファイルでGOOGLE_APPLICATION_CREDENTIALS=path/to/key.jsonを設定\n"
                              "2. gcloud CLIで認証:\n"
                              "   - gcloud auth application-default login\n"
                              "3. プロジェクトIDを確認:\n"
                              "   - .envファイルでGOOGLE_CLOUD_PROJECT=your-project-idを設定")
            raise HTTPException(status_code=500, detail=detailed_error)

        raise HTTPException(status_code=500, detail=error_message)


@app.get("/logs")
async def list_logs():
    """ログファイル一覧と詳細情報を取得"""
    try:
        log_details = []
        for log_file in LOGS_DIR.glob("*.jsonl"):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    log_content = json.loads(f.read().strip())

                    log_details.append({
                        "filename":
                            log_file.name,
                        "timestamp":
                            log_content.get("timestamp", ""),
                        "execution_mode":
                            log_content.get("execution_mode", ""),
                        "status":
                            log_content.get("status", "unknown"),
                        "execution_time":
                            log_content.get("execution_time", 0),
                        "total_tokens":
                            log_content.get("total_tokens", 0),
                        "error_message":
                            log_content.get("error_message"),
                        "query":
                            log_content.get("query", "")[:100] +
                            ("..." if len(log_content.get("query", "")) > 100 else "")
                    })
            except Exception as e:
                # ログファイルの読み込みに失敗した場合もリストに含める
                log_details.append({
                    "filename": log_file.name,
                    "timestamp": "",
                    "execution_mode": "",
                    "status": "error",
                    "execution_time": 0,
                    "total_tokens": 0,
                    "error_message": f"ログファイルの読み込みに失敗: {str(e)}",
                    "query": ""
                })

        return {"logs": sorted(log_details, key=lambda x: x["timestamp"], reverse=True)}

    except Exception as e:
        logger.error("Failed to list logs", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs/{filename}")
async def get_log_file(filename: str):
    """特定のログファイルを取得"""
    log_path = LOGS_DIR / filename

    if not log_path.exists():
        raise HTTPException(status_code=404, detail="Log file not found")

    return FileResponse(path=log_path, filename=filename, media_type="application/json")


@app.delete("/logs/{filename}")
async def delete_log_file(filename: str):
    """特定のログファイルを削除"""
    try:
        log_path = LOGS_DIR / filename
        if not log_path.exists():
            raise HTTPException(status_code=404, detail="ログファイルが見つかりません")

        log_path.unlink()
        logger.info(f"ログファイルを削除しました: {filename}")
        return {"message": f"ログファイル '{filename}' を削除しました"}

    except Exception as e:
        logger.error("Failed to delete log file", error=str(e), filename=filename)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/logs")
async def delete_all_logs():
    """すべてのログファイルを削除"""
    try:
        deleted_count = 0
        for log_file in LOGS_DIR.glob("*.jsonl"):
            log_file.unlink()
            deleted_count += 1

        logger.info(f"すべてのログファイルを削除しました: {deleted_count}件")
        return {"message": f"{deleted_count}件のログファイルを削除しました"}

    except Exception as e:
        logger.error("Failed to delete all logs", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/status")
async def check_auth_status():
    """Google Cloud認証状況を確認"""
    from env_utils import check_google_cloud_auth

    try:
        auth_available = check_google_cloud_auth()
        project_id = get_google_cloud_project()

        return {
            "authenticated": auth_available,
            "project_id": project_id,
            "status": "認証済み" if auth_available else "認証が必要",
            "message": "Vertex AIを使用できます" if auth_available else "認証設定が必要です"
        }
    except Exception as e:
        return {
            "authenticated": False,
            "project_id": None,
            "status": "エラー",
            "message": f"認証チェック中にエラーが発生しました: {str(e)}"
        }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
