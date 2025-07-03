# RAG実装ベストプラクティスガイド

このドキュメントでは、RAGシステムの実装時に役立つベストプラクティス、設計原則、トラブルシューティング手法、継続的改善のためのフレームワークを詳しく解説します。

## 実装時のベストプラクティス

### RAGシステム設計の原則

#### チャンキング戦略

> **💡 学習ポイント**  
> チャンキングはRAGシステムの根幹となる技術で、文書をどのように分割するかが検索品質に直結します。単純な文字数分割ではなく、文書の構造と内容を理解した戦略的な分割が重要です。

**適切なチャンクサイズの選択**

> **📚 背景**  
> チャンクサイズは「情報の完結性」と「検索の精度」のバランスを決定します。小さすぎると文脈が失われ、大きすぎると無関係な情報が混入してしまいます。文書タイプごとに最適化することで、各用途に応じた最高の性能を実現できます。

```python
# 文書の性質に応じたチャンクサイズの調整
class ChunkingConfig:
    # 技術文書・マニュアル: 詳細な手順を含むため大きめ
    TECHNICAL_DOC = {"chunk_size": 800, "chunk_overlap": 150}
    
    # FAQ・Q&A: 一問一答形式のため中程度
    FAQ_DOC = {"chunk_size": 400, "chunk_overlap": 100}
    
    # チャット・対話ログ: 短いやり取りのため小さめ
    CHAT_LOG = {"chunk_size": 200, "chunk_overlap": 50}

def get_chunking_config(doc_type: str) -> dict:
    """文書タイプに応じた最適なチャンク設定を返す"""
    configs = {
        "technical": ChunkingConfig.TECHNICAL_DOC,
        "faq": ChunkingConfig.FAQ_DOC,
        "chat": ChunkingConfig.CHAT_LOG
    }
    return configs.get(doc_type, ChunkingConfig.TECHNICAL_DOC)
```

**意味的な分割ポイントの活用**

> **🎯 なぜ重要か**  
> 機械的な文字数分割ではなく、文書の論理構造（見出し、段落、文）に沿って分割することで、意味的な一貫性を保ちながら検索精度を向上させることができます。特にMarkdown形式の技術文書では、階層構造を活用した分割が効果的です。

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

def create_smart_splitter(chunk_size: int = 800, chunk_overlap: int = 150):
    """意味的な境界を考慮したテキストスプリッターを作成"""
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # 分割の優先順位: セクション → 段落 → 文 → 単語 → 文字
        separators=[
            "\n## ",      # Markdownセクション
            "\n### ",     # Markdownサブセクション
            "\n\n",       # 段落
            "\n",         # 改行
            "。",         # 日本語の文末
            ".",          # 英語の文末
            "！",         # 感嘆符
            "!",
            "？",         # 疑問符
            "?",
            " ",          # スペース
            ""            # 文字レベル
        ],
        length_function=len,
        is_separator_regex=False
    )
```

#### 検索精度の向上

**ハイブリッド検索の実装**

> **🚀 実践のメリット**  
> 単一の検索手法に依存せず、ベクトル検索とキーワード検索を組み合わせることで、それぞれの弱点を補完し合います。ベクトル検索は意味的類似性に強く、キーワード検索は固有名詞や専門用語に強いという特性を活用できます。

```python
from typing import List, Dict
import numpy as np

def hybrid_search(
    query: str, 
    vector_store, 
    keyword_weights: Dict[str, float] = None,
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3,
    k: int = 5
) -> List:
    """ベクトル検索とキーワード検索を組み合わせた検索"""
    
    # ベクトル検索
    vector_results = vector_store.similarity_search_with_score(query, k=k*2)
    
    # キーワード検索（簡易実装）
    keyword_results = keyword_search(query, vector_store, k=k*2)
    
    # スコアの正規化と統合
    combined_results = {}
    
    # ベクトル検索結果の処理
    for doc, score in vector_results:
        doc_id = doc.metadata.get('id', hash(doc.page_content))
        combined_results[doc_id] = {
            'doc': doc,
            'vector_score': 1 - score,  # 距離を類似度に変換
            'keyword_score': 0
        }
    
    # キーワード検索結果の処理
    for doc, score in keyword_results:
        doc_id = doc.metadata.get('id', hash(doc.page_content))
        if doc_id in combined_results:
            combined_results[doc_id]['keyword_score'] = score
        else:
            combined_results[doc_id] = {
                'doc': doc,
                'vector_score': 0,
                'keyword_score': score
            }
    
    # 統合スコアの計算
    for doc_id, data in combined_results.items():
        data['combined_score'] = (
            vector_weight * data['vector_score'] + 
            keyword_weight * data['keyword_score']
        )
    
    # スコア順にソート
    sorted_results = sorted(
        combined_results.values(),
        key=lambda x: x['combined_score'],
        reverse=True
    )
    
    return [result['doc'] for result in sorted_results[:k]]
```

**クエリ拡張とフィルタリング**

> **🔍 技術的な価値**  
> ユーザーの検索クエリを解析・拡張することで、検索の網羅性と精度を同時に向上させることができます。日本語の同義語展開、時間的制約の自動検出、カテゴリ分類などにより、より適切な文書を特定できます。

```python
import re
from datetime import datetime, timedelta

def enhance_query(query: str, context: Dict = None) -> Dict:
    """クエリを拡張・強化する"""
    
    enhanced = {
        'original_query': query,
        'expanded_queries': [],
        'filters': {},
        'query_type': 'general'
    }
    
    # 時間的なクエリの検出
    if re.search(r'最新|今日|昨日|今週|今月', query):
        enhanced['query_type'] = 'temporal'
        enhanced['filters']['date_range'] = {
            'start': datetime.now() - timedelta(days=30),
            'end': datetime.now()
        }
    
    # 特定カテゴリの検出
    category_keywords = {
        'maintenance': ['メンテナンス', '保守', '点検', '整備'],
        'trouble': ['トラブル', '問題', '不具合', 'エラー'],
        'procedure': ['手順', '方法', 'やり方', '操作']
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in query for keyword in keywords):
            enhanced['filters']['category'] = category
            enhanced['query_type'] = category
            break
    
    # 同義語展開
    synonyms = {
        'メンテナンス': ['保守', '点検', '整備', 'maintenance'],
        'トラブル': ['問題', '不具合', 'エラー', 'trouble', 'issue'],
        '手順': ['方法', 'やり方', '操作', 'procedure', 'steps']
    }
    
    for word, syns in synonyms.items():
        if word in query:
            enhanced['expanded_queries'].extend([
                query.replace(word, syn) for syn in syns
            ])
    
    return enhanced
```

#### プロンプト設計のベストプラクティス

**段階的なプロンプト構築**

> **🎭 プロンプトエンジニアリングの原則**  
> 効果的なプロンプトは単なる指示文ではなく、LLMが最適な回答を生成するための「ガイドライン」です。役割定義、文脈提供、出力形式の指定を構造化することで、一貫性のある高品質な回答を得ることができます。

```python
class PromptBuilder:
    """段階的にプロンプトを構築するクラス"""
    
    def __init__(self):
        self.system_prompt = ""
        self.context_prompt = ""
        self.query_prompt = ""
        self.formatting_prompt = ""
    
    def set_system_role(self, domain: str = "general"):
        """システムロールを設定"""
        roles = {
            "technical": "あなたは技術サポートの専門家です。",
            "maintenance": "あなたは設備保守の専門家です。",
            "general": "あなたは知識豊富なアシスタントです。"
        }
        self.system_prompt = roles.get(domain, roles["general"])
        return self
    
    def add_context(self, documents: List, max_context_length: int = 2000):
        """コンテキスト情報を追加"""
        context_parts = []
        current_length = 0
        
        for doc in documents:
            content = doc.page_content
            if current_length + len(content) > max_context_length:
                break
            context_parts.append(content)
            current_length += len(content)
        
        if context_parts:
            self.context_prompt = (
                "\n以下の情報を参考にしてください：\n\n" +
                "\n---\n".join(context_parts)
            )
        return self
    
    def set_query(self, query: str, query_type: str = "general"):
        """クエリと回答形式を設定"""
        formatting_rules = {
            "technical": "\n\n具体的な手順がある場合は、番号付きリストで回答してください。",
            "maintenance": "\n\n安全上の注意点がある場合は、必ず最初に記載してください。",
            "general": "\n\n簡潔で分かりやすく回答してください。"
        }
        
        self.query_prompt = f"\n\n質問: {query}"
        self.formatting_prompt = formatting_rules.get(query_type, formatting_rules["general"])
        return self
    
    def build(self) -> str:
        """最終的なプロンプトを構築"""
        return (
            self.system_prompt +
            self.context_prompt +
            self.query_prompt +
            self.formatting_prompt
        ).strip()

# 使用例
def create_optimized_prompt(query: str, documents: List, query_type: str = "general") -> str:
    """最適化されたプロンプトを作成"""
    return (
        PromptBuilder()
        .set_system_role(query_type)
        .add_context(documents)
        .set_query(query, query_type)
        .build()
    )
```

### エラーハンドリングとログ戦略

#### 堅牢なエラーハンドリング

```python
import logging
from typing import Optional, Union
from functools import wraps
import time
import traceback

class RAGError(Exception):
    """RAGシステム固有のエラー"""
    pass

class RetryableError(RAGError):
    """再試行可能なエラー"""
    pass

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """失敗時に自動リトライするデコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RetryableError as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = delay * (2 ** attempt)  # 指数バックオフ
                        logging.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {wait_time:.1f}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logging.error(f"All {max_retries + 1} attempts failed")
                except Exception as e:
                    # 再試行不可能なエラーは即座に発生
                    logging.error(f"Non-retryable error: {e}")
                    raise
            
            raise last_exception
        return wrapper
    return decorator

@retry_on_failure(max_retries=3)
def generate_response_with_retry(prompt: str, model_client) -> str:
    """LLM応答生成（リトライ機能付き）"""
    try:
        response = model_client.generate_response(prompt)
        if not response or len(response.strip()) < 10:
            raise RetryableError("Empty or too short response")
        return response
    except ConnectionError as e:
        raise RetryableError(f"Connection failed: {e}")
    except ValueError as e:
        raise RAGError(f"Invalid input: {e}")  # 再試行不可
```

#### 構造化ログの実装

```python
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

class StructuredLogger:
    """構造化ログ用のロガー"""
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # フォーマッターの設定
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # ファイルハンドラー（指定された場合）
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log_query(self, query: str, query_type: str, user_id: str = None):
        """クエリログ"""
        log_data = {
            "event": "query_received",
            "timestamp": datetime.now().isoformat(),
            "query_length": len(query),
            "query_type": query_type,
            "user_id": user_id or "anonymous"
        }
        self.logger.info(f"QUERY: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_retrieval(self, retrieved_docs: List, query: str, retrieval_time: float):
        """検索結果ログ"""
        log_data = {
            "event": "documents_retrieved",
            "timestamp": datetime.now().isoformat(),
            "doc_count": len(retrieved_docs),
            "retrieval_time_ms": round(retrieval_time * 1000, 2),
            "doc_lengths": [len(doc.page_content) for doc in retrieved_docs[:3]]  # 上位3件のみ
        }
        self.logger.info(f"RETRIEVAL: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_generation(self, prompt_length: int, response_length: int, generation_time: float):
        """生成結果ログ"""
        log_data = {
            "event": "response_generated",
            "timestamp": datetime.now().isoformat(),
            "prompt_length": prompt_length,
            "response_length": response_length,
            "generation_time_ms": round(generation_time * 1000, 2),
            "tokens_per_second": round(response_length / max(generation_time, 0.001), 2)
        }
        self.logger.info(f"GENERATION: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """エラーログ"""
        log_data = {
            "event": "error_occurred",
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        self.logger.error(f"ERROR: {json.dumps(log_data, ensure_ascii=False)}")
        self.logger.debug(f"Traceback: {traceback.format_exc()}")
```

### 環境設定とセキュリティ

#### 環境依存設定の管理

```python
import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    """設定クラス"""
    # Google Cloud設定
    google_cloud_project: str
    google_cloud_region: str = "us-central1"
    google_application_credentials: Optional[str] = None
    
    # RAG設定
    chunk_size: int = 800
    chunk_overlap: int = 150
    max_retrieved_docs: int = 5
    
    # LLM設定
    model_name: str = "gemini-1.5-pro"
    max_tokens: int = 1000
    temperature: float = 0.1
    
    # システム設定
    debug_mode: bool = False
    log_level: str = "INFO"
    max_query_length: int = 1000
    
    @classmethod
    def from_env(cls) -> "Config":
        """環境変数から設定を読み込み"""
        return cls(
            google_cloud_project=os.getenv("GOOGLE_CLOUD_PROJECT", ""),
            google_cloud_region=os.getenv("GOOGLE_CLOUD_REGION", "us-central1"),
            google_application_credentials=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            
            chunk_size=int(os.getenv("CHUNK_SIZE", "800")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "150")),
            max_retrieved_docs=int(os.getenv("MAX_RETRIEVED_DOCS", "5")),
            
            model_name=os.getenv("MODEL_NAME", "gemini-1.5-pro"),
            max_tokens=int(os.getenv("MAX_TOKENS", "1000")),
            temperature=float(os.getenv("TEMPERATURE", "0.1")),
            
            debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_query_length=int(os.getenv("MAX_QUERY_LENGTH", "1000"))
        )
    
    def validate(self) -> List[str]:
        """設定の妥当性チェック"""
        errors = []
        
        if not self.google_cloud_project:
            errors.append("GOOGLE_CLOUD_PROJECT is required")
        
        if self.google_application_credentials:
            if not Path(self.google_application_credentials).exists():
                errors.append(f"Credentials file not found: {self.google_application_credentials}")
        
        if self.chunk_size <= 0:
            errors.append("chunk_size must be positive")
        
        if self.chunk_overlap >= self.chunk_size:
            errors.append("chunk_overlap must be less than chunk_size")
        
        if self.max_retrieved_docs <= 0:
            errors.append("max_retrieved_docs must be positive")
        
        return errors
```

#### セキュリティ対策

```python
import hashlib
import secrets
from typing import Dict, List
import re

class SecurityManager:
    """セキュリティ管理クラス"""
    
    def __init__(self):
        self.sensitive_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}-\d{4}-\d{4}\b',  # 電話番号
            r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b',  # クレジットカード番号
            r'password\s*[:=]\s*\S+',  # パスワード
            r'api[_-]?key\s*[:=]\s*\S+',  # APIキー
        ]
    
    def sanitize_query(self, query: str) -> str:
        """クエリから機密情報を除去"""
        sanitized = query
        
        for pattern in self.sensitive_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def hash_user_id(self, user_id: str) -> str:
        """ユーザーIDをハッシュ化"""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def validate_input_length(self, text: str, max_length: int = 1000) -> bool:
        """入力長の検証"""
        return len(text) <= max_length
    
    def check_malicious_patterns(self, text: str) -> List[str]:
        """悪意のあるパターンをチェック"""
        warnings = []
        
        # SQLインジェクション的なパターン
        sql_patterns = [
            r'(union|select|insert|update|delete|drop)\s+',
            r'--',
            r'/\*.*\*/',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                warnings.append(f"Potential SQL injection pattern detected")
                break
        
        # スクリプト実行的なパターン
        script_patterns = [
            r'<script',
            r'javascript:',
            r'eval\s*\(',
        ]
        
        for pattern in script_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                warnings.append(f"Potential script injection pattern detected")
                break
        
        return warnings

def secure_query_handler(query: str, user_id: str = None) -> Dict:
    """セキュアなクエリ処理"""
    security = SecurityManager()
    
    # セキュリティチェック
    warnings = security.check_malicious_patterns(query)
    if warnings:
        return {
            "error": "Security validation failed",
            "warnings": warnings
        }
    
    # 入力長チェック
    if not security.validate_input_length(query):
        return {
            "error": "Query too long",
            "max_length": 1000
        }
    
    # 機密情報の除去
    sanitized_query = security.sanitize_query(query)
    
    # ユーザーIDのハッシュ化
    hashed_user_id = security.hash_user_id(user_id) if user_id else None
    
    return {
        "sanitized_query": sanitized_query,
        "user_hash": hashed_user_id,
        "original_length": len(query),
        "sanitized_length": len(sanitized_query)
    }
```

### パフォーマンス最適化

#### キャッシュ戦略

```python
import functools
import hashlib
import json
import time
from typing import Any, Dict, Optional
import redis

class CacheManager:
    """キャッシュ管理クラス"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.memory_cache = {}
        self.cache_stats = {"hits": 0, "misses": 0}
    
    def _get_cache_key(self, query: str, context_hash: str = None) -> str:
        """キャッシュキーを生成"""
        key_data = {
            "query": query.lower().strip(),
            "context": context_hash or ""
        }
        key_string = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """キャッシュから値を取得"""
        # Redisキャッシュを確認
        if self.redis_client:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    self.cache_stats["hits"] += 1
                    return json.loads(cached)
            except:
                pass
        
        # メモリキャッシュを確認
        if key in self.memory_cache:
            cache_entry = self.memory_cache[key]
            if time.time() - cache_entry["timestamp"] < 3600:  # 1時間有効
                self.cache_stats["hits"] += 1
                return cache_entry["data"]
            else:
                del self.memory_cache[key]
        
        self.cache_stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """キャッシュに値を設定"""
        # Redisキャッシュに保存
        if self.redis_client:
            try:
                self.redis_client.setex(
                    key, 
                    ttl, 
                    json.dumps(value, ensure_ascii=False)
                )
            except:
                pass
        
        # メモリキャッシュに保存
        self.memory_cache[key] = {
            "data": value,
            "timestamp": time.time()
        }
    
    def get_stats(self) -> Dict:
        """キャッシュ統計を取得"""
        total = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total if total > 0 else 0
        
        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate": round(hit_rate, 3),
            "memory_cache_size": len(self.memory_cache)
        }

def cached_response(cache_manager: CacheManager, ttl: int = 3600):
    """レスポンスキャッシュデコレータ"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # キャッシュキーを生成
            cache_key = cache_manager._get_cache_key(
                str(args) + str(kwargs)
            )
            
            # キャッシュから取得を試行
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                return cached_result
            
            # 関数を実行
            result = func(*args, **kwargs)
            
            # 結果をキャッシュ
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
```

#### バッチ処理とパイプライン化

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any

class BatchProcessor:
    """バッチ処理管理クラス"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    def process_documents_parallel(
        self, 
        documents: List[str], 
        process_func: Callable,
        batch_size: int = 10
    ) -> List[Any]:
        """文書を並列処理"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # バッチに分割
            batches = [
                documents[i:i + batch_size] 
                for i in range(0, len(documents), batch_size)
            ]
            
            # 各バッチを並列実行
            future_to_batch = {
                executor.submit(process_func, batch): batch 
                for batch in batches
            }
            
            for future in as_completed(future_to_batch):
                try:
                    batch_result = future.result()
                    results.extend(batch_result)
                except Exception as e:
                    logging.error(f"Batch processing failed: {e}")
        
        return results
    
    async def async_pipeline(
        self, 
        data: Any, 
        processors: List[Callable]
    ) -> Any:
        """非同期パイプライン処理"""
        result = data
        
        for processor in processors:
            if asyncio.iscoroutinefunction(processor):
                result = await processor(result)
            else:
                result = processor(result)
        
        return result

# 使用例
async def optimized_rag_pipeline(query: str, documents: List[str]) -> str:
    """最適化されたRAGパイプライン"""
    batch_processor = BatchProcessor()
    
    # 並列処理でエンベディング生成
    async def create_embeddings(docs):
        return await asyncio.to_thread(
            batch_processor.process_documents_parallel,
            docs,
            lambda batch: [embed_document(doc) for doc in batch]
        )
    
    # 非同期パイプライン
    processors = [
        lambda x: preprocess_documents(x),
        create_embeddings,
        lambda x: search_similar_documents(query, x),
        lambda x: generate_response(query, x)
    ]
    
    return await batch_processor.async_pipeline(documents, processors)
```

### デプロイメントと本番運用

#### 段階的デプロイメント戦略

```python
from enum import Enum
from typing import Dict, List
import random

class DeploymentStage(Enum):
    DEVELOPMENT = "dev"
    STAGING = "staging"
    CANARY = "canary"
    PRODUCTION = "prod"

class FeatureFlags:
    """機能フラグ管理"""
    
    def __init__(self):
        self.flags = {
            "hybrid_search": {
                "dev": True,
                "staging": True,
                "canary": 0.1,  # 10%のトラフィック
                "prod": False
            },
            "advanced_chunking": {
                "dev": True,
                "staging": True,
                "canary": 0.05,  # 5%のトラフィック
                "prod": False
            },
            "response_caching": {
                "dev": True,
                "staging": True,
                "canary": 1.0,
                "prod": True
            }
        }
    
    def is_enabled(self, feature: str, stage: DeploymentStage, user_id: str = None) -> bool:
        """機能が有効かチェック"""
        if feature not in self.flags:
            return False
        
        flag_value = self.flags[feature].get(stage.value, False)
        
        # ブール値の場合
        if isinstance(flag_value, bool):
            return flag_value
        
        # 割合の場合（カナリアデプロイメント）
        if isinstance(flag_value, float):
            if user_id:
                # ユーザーIDベースの一貫した判定
                user_hash = hash(user_id) % 100
                return user_hash < (flag_value * 100)
            else:
                # ランダム判定
                return random.random() < flag_value
        
        return False

class HealthChecker:
    """ヘルスチェック管理"""
    
    def __init__(self):
        self.checks = {}
    
    def register_check(self, name: str, check_func: Callable) -> None:
        """ヘルスチェック関数を登録"""
        self.checks[name] = check_func
    
    def run_checks(self) -> Dict[str, Any]:
        """全ヘルスチェックを実行"""
        results = {
            "status": "healthy",
            "checks": {},
            "timestamp": datetime.now().isoformat()
        }
        
        for name, check_func in self.checks.items():
            try:
                start_time = time.time()
                result = check_func()
                duration = time.time() - start_time
                
                results["checks"][name] = {
                    "status": "pass" if result else "fail",
                    "duration_ms": round(duration * 1000, 2),
                    "details": result if isinstance(result, dict) else {}
                }
                
                if not result:
                    results["status"] = "unhealthy"
                    
            except Exception as e:
                results["checks"][name] = {
                    "status": "error",
                    "error": str(e)
                }
                results["status"] = "unhealthy"
        
        return results

# ヘルスチェック関数の例
def check_vector_store() -> bool:
    """ベクトルストアの接続チェック"""
    try:
        # 実際のベクトルストア接続テスト
        return True
    except:
        return False

def check_llm_service() -> bool:
    """LLMサービスの接続チェック"""
    try:
        # 実際のLLMサービス接続テスト
        return True
    except:
        return False

# 使用例
def setup_health_checks() -> HealthChecker:
    """ヘルスチェックのセットアップ"""
    health_checker = HealthChecker()
    health_checker.register_check("vector_store", check_vector_store)
    health_checker.register_check("llm_service", check_llm_service)
    
    return health_checker
```

### 監視とメトリクス

#### 主要KPIの定義と測定

```python
from dataclasses import dataclass
from typing import Dict, List
import time
from datetime import datetime, timedelta

@dataclass
class RAGMetrics:
    """RAGシステムのメトリクス"""
    
    # パフォーマンスメトリクス
    query_latency: float = 0.0          # クエリ応答時間（秒）
    retrieval_latency: float = 0.0      # 検索時間（秒）
    generation_latency: float = 0.0     # 生成時間（秒）
    
    # 品質メトリクス
    retrieval_precision: float = 0.0    # 検索精度
    answer_relevance: float = 0.0       # 回答関連性
    answer_completeness: float = 0.0    # 回答完全性
    
    # システムメトリクス
    cpu_usage: float = 0.0              # CPU使用率
    memory_usage: float = 0.0           # メモリ使用率
    cache_hit_rate: float = 0.0         # キャッシュヒット率
    
    # ビジネスメトリクス
    user_satisfaction: float = 0.0      # ユーザー満足度
    query_success_rate: float = 0.0     # クエリ成功率
    daily_active_users: int = 0         # 日次アクティブユーザー

class MetricsCollector:
    """メトリクス収集クラス"""
    
    def __init__(self):
        self.metrics_history = []
        self.current_metrics = RAGMetrics()
    
    def start_timer(self) -> float:
        """タイマー開始"""
        return time.time()
    
    def end_timer(self, start_time: float) -> float:
        """タイマー終了・経過時間を返す"""
        return time.time() - start_time
    
    def record_query_metrics(self, 
                           retrieval_time: float,
                           generation_time: float,
                           doc_count: int,
                           query_success: bool):
        """クエリメトリクスを記録"""
        total_time = retrieval_time + generation_time
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "query_latency": total_time,
            "retrieval_latency": retrieval_time,
            "generation_latency": generation_time,
            "retrieved_doc_count": doc_count,
            "query_success": query_success
        }
        
        self.metrics_history.append(metrics)
    
    def get_daily_summary(self, date: datetime = None) -> Dict:
        """日次サマリーを取得"""
        if date is None:
            date = datetime.now()
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        daily_metrics = [
            m for m in self.metrics_history
            if start_of_day <= datetime.fromisoformat(m["timestamp"]) < end_of_day
        ]
        
        if not daily_metrics:
            return {"date": date.date().isoformat(), "no_data": True}
        
        return {
            "date": date.date().isoformat(),
            "total_queries": len(daily_metrics),
            "avg_latency": sum(m["query_latency"] for m in daily_metrics) / len(daily_metrics),
            "success_rate": sum(1 for m in daily_metrics if m["query_success"]) / len(daily_metrics),
            "avg_retrieval_time": sum(m["retrieval_latency"] for m in daily_metrics) / len(daily_metrics),
            "avg_generation_time": sum(m["generation_latency"] for m in daily_metrics) / len(daily_metrics),
            "min_latency": min(m["query_latency"] for m in daily_metrics),
            "max_latency": max(m["query_latency"] for m in daily_metrics),
            "p95_latency": self._calculate_percentile(
                [m["query_latency"] for m in daily_metrics], 95
            )
        }
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """パーセンタイル値を計算"""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
```

### 継続的改善のための学習ポイント

> **📈 継続的改善の重要性**  
> RAGシステムは「作って終わり」ではなく、継続的な改善が品質向上の鍵となります。実際のユーザーフィードバック、性能メトリクス、システムログを活用して、段階的に精度を向上させていくことが重要です。

#### プロジェクトで得られた知見

**チャンキング戦略の重要性**

> **🔧 実践から学んだ教訓**  
> 文書の性質を理解せずに一律的なチャンクサイズを適用すると、検索精度が大きく低下します。技術文書、FAQ、対話ログなど、それぞれの特性に合わせた最適化が必要です。

- 単純な文字数分割よりも、意味的な境界（セクション、段落）を考慮した分割が効果的
- 日本語文書では、句読点や改行を適切に活用することで検索精度が向上
- チャンクサイズは文書の性質に応じて調整が必要（技術文書: 800文字、FAQ: 400文字）

**ハイブリッド検索の効果**

> **⚖️ バランスの重要性**  
> 単一の検索手法では捉えきれない多様な検索ニーズに対応するため、複数の手法を組み合わせることで検索の「死角」を減らすことができます。

- ベクトル検索（意味的類似性）とキーワード検索（語彙的一致）の組み合わせ
- 特にメンテナンス関連のクエリでは、キーワードマッチングが重要
- 重み付け（ベクトル70%、キーワード30%）により精度が向上

**プロンプト設計のベストプラクティス**

> **📝 構造化アプローチの価値**  
> LLMに対する指示を体系的に構造化することで、出力の一貫性と品質を大幅に向上させることができます。プロンプトの各要素が果たす役割を理解することが重要です。

- システムロール、コンテキスト、クエリ、フォーマット指示の段階的な構築
- コンテキスト長の制限を考慮した動的な文書選択
- クエリタイプに応じた回答フォーマットの指定

**ログとデバッグの重要性**

> **🔍 見える化による改善サイクル**  
> システムの動作を詳細に記録・分析することで、問題の早期発見と継続的な改善が可能になります。特にRAGシステムでは、どの文書が選ばれ、どのような回答が生成されたかの追跡が重要です。

- 構造化ログ（JSON形式）により分析が容易
- 実際のLLMプロンプト、取得文書、応答時間の記録
- エラー発生時の詳細な情報収集

#### 今後の改善方向

**検索精度の向上**

> **🎯 次世代検索技術の方向性**  
> 静的な検索アルゴリズムから、ユーザーの行動やフィードバックを学習する動的なシステムへの進化が重要です。ドメイン固有の同義語辞書、クエリの意図理解、文脈に応じた結果ランキングなどの技術が鍵となります。

```python
# より高度なクエリ拡張
def advanced_query_expansion(query: str) -> List[str]:
    """同義語、関連語を用いたクエリ拡張"""
    expanded_queries = [query]
    
    # 同義語辞書の活用
    synonyms = load_domain_synonyms()
    for word, syns in synonyms.items():
        if word in query:
            for syn in syns:
                expanded_queries.append(query.replace(word, syn))
    
    return expanded_queries

# リランキングの実装
def rerank_results(query: str, initial_results: List) -> List:
    """より精密なモデルで検索結果を再評価"""
    # Cross-encoderやより大きなモデルを使用
    pass
```

**マルチモーダル対応**

> **🖼️ 情報の多様性への対応**  
> 現代のナレッジベースには文字情報だけでなく、図表、画像、動画なども含まれます。これらの情報を統合的に検索・活用できるシステムの構築により、より豊富で正確な回答の提供が可能になります。

```python
# 画像・図表を含む文書の処理
def process_multimodal_document(doc_path: str) -> Dict:
    """画像とテキストを統合した文書処理"""
    return {
        "text_chunks": extract_text_chunks(doc_path),
        "image_descriptions": extract_and_describe_images(doc_path),
        "table_data": extract_structured_tables(doc_path)
    }
```

**リアルタイム学習**

> **🔄 自己改善システムの実現**  
> ユーザーの行動データやフィードバックから継続的に学習し、システム自体が成長していく仕組みの構築が重要です。これにより、使えば使うほど精度が向上するRAGシステムを実現できます。

```python
# ユーザーフィードバックからの学習
class FeedbackLearning:
    def collect_feedback(self, query: str, response: str, rating: int):
        """ユーザーフィードバックを収集"""
        pass
    
    def update_retrieval_weights(self):
        """フィードバックに基づき検索重みを調整"""
        pass
```

#### 開発チーム向けのベストプラクティス

**コードレビューのチェックポイント**

> **👥 品質保証の重要性**  
> RAGシステムは複数の技術要素が連携する複雑なシステムです。各コンポーネントの品質を確保し、統合時の問題を未然に防ぐためのレビュープロセスが重要です。

- [ ] エラーハンドリングが適切に実装されているか
- [ ] ログが十分な情報を含んでいるか
- [ ] 機密情報がログに出力されていないか
- [ ] パフォーマンスの考慮がされているか
- [ ] テストケースが追加されているか

**開発環境のセットアップ**

> **🔧 開発効率化の基盤**  
> 開発チーム全体で一貫した環境を構築することで、環境差異による問題を防ぎ、効率的な開発を実現できます。特にRAGシステムでは、LLM API、ベクトルDB、Webアプリケーションなど複数のサービスの連携が必要です。

```bash
# 開発用の設定
cp .env.example .env.dev
# DEBUG_MODE=true を設定

# テスト用のデータ準備
python scripts/create_test_data.py

# 品質チェック
pre-commit install
black src/
flake8 src/
pytest tests/
```

**本番デプロイ前のチェックリスト**

> **🚀 本番運用への準備**  
> RAGシステムを本番環境で安定運用するためには、開発環境での動作確認だけでは不十分です。セキュリティ、パフォーマンス、監視、エラーハンドリングなど、本番特有の要件に対する十分な準備が必要です。

- [ ] 全テストがパスしているか
- [ ] 機密情報が環境変数で管理されているか
- [ ] ログレベルが適切に設定されているか
- [ ] ヘルスチェックエンドポイントが動作するか
- [ ] 監視・アラートが設定されているか
- [ ] ロールバック手順が確認されているか

---

## まとめ

このRAGベストプラクティスガイドでは、実際のプロダクション環境でRAGシステムを構築・運用するために必要な知識と手法を包括的に解説しました。技術的な実装だけでなく、エラーハンドリング、セキュリティ、パフォーマンス最適化、継続的改善まで含めることで、堅牢で拡張性の高いRAGシステムの構築に役立つリソースとなっています。

RAG技術は急速に進歩している分野ですが、ここで示した基本的な原則と実装パターンは、今後の発展にも対応できる堅固な基盤となるはずです。
