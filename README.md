# LLM情報提供手法比較システム

このプロジェクトは、LLMに外部情報を与えるための**5つの主要手法を統一環境で比較・検証**できる**フルスタックWebアプリケーション**です。

## 🎯 背景と目的

現代のLLMアプリケーション開発において、外部情報の提供方法は成功の鍵となります。本システムでは以下の5つの主要アプローチを実装し、同一条件での比較を可能にしています：

1. **LLM単体利用**: ベースライン確認
2. **プロンプトスタッフィング**: 全情報埋め込み
3. **RAGのみ**: ベクトル検索による効率的検索
4. **Function Calling**: LLMの自律的ツール利用
5. **RAG + Function Calling**: 複合アプローチ（推奨）

各手法の**効率性・精度・柔軟性**を定量的・定性的に比較し、実用的な知見を得ることができます。

## ✨ 主な特徴

- **統一環境での比較**: 同一データ・同一質問での公正な比較
- **フルスタックWebアプリ**: PythonのFastAPIバックエンド + Next.jsフロントエンド
- **リアルタイム処理**: 処理状況・中間生成物をリアルタイム表示
- **詳細な分析機能**: トークン数・処理時間・実行ログの詳細表示
- **デモモード**: プレゼンテーション用の遅延表示機能
- **編集可能KB**: ブラウザ上でナレッジベースを直接編集可能

## 🚀 クイックスタート

### 前提条件

- Python 3.10以上
- Node.js 18以上
- Google Cloud Project（Vertex AI API有効化）

### 最短設定手順

1. **Google Cloud設定**: [Google Cloud Console](https://console.cloud.google.com/)でプロジェクト作成・Vertex AI API有効化
2. **認証設定**: プロジェクトルートに`.env`ファイル作成し、`GOOGLE_CLOUD_PROJECT=your-project-id`を記載
3. **代替認証**: または`gcloud auth application-default login`でログイン

### インストール・実行

```bash
# 1. プロジェクトIDを設定（必須）
echo "GOOGLE_CLOUD_PROJECT=your-actual-project-id" > .env

# 2. バックエンド環境構築
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r src/backend/requirements.txt

# 2. フロントエンド環境構築
cd src/frontend
npm install

# 3. 実行（2つのターミナルで同時実行）
# ターミナル1: バックエンド
python src/backend/main.py

# ターミナル2: フロントエンド
cd src/frontend
npm run dev
```

### アクセス

- **フロントエンド**: <http://localhost:3000>
- **バックエンドAPI**: <http://localhost:8000>
- **API仕様書**: <http://localhost:8000/docs>

### 使用方法

1. 処理モードを選択（5つの手法から）
2. 質問を入力（例: 「エラーコードE-404の対処法は？」）
3. 実行ボタンをクリック
4. 結果・トークン数・処理時間を確認
5. 必要に応じてログをダウンロード

## 🔧 5つの手法の概要

### 手法1: LLM単体利用（ベースライン）

**外部情報なし**でLLMの内蔵知識のみを活用。最もシンプルで高速ですが、知識の範囲と鮮度に制限があります。

### 手法2: プロンプトスタッフィング

**全情報をプロンプトに埋め込み**。確実で理解しやすい手法ですが、大量データではトークン消費が課題となります。

### 手法3: RAGのみ

**ベクトル検索による関連情報取得**。効率的で拡張性が高く、現代的なRAGアーキテクチャの基本形です。

### 手法4: Function Callingのみ

**LLMの自律的ツール選択・実行**。動的で柔軟な情報検索が可能ですが、ツール設計の品質に依存します。

### 手法5: RAG + Function Calling（推奨）

**RAGとFunction Callingの組み合わせ**。最も柔軟で実用的ですが、複雑性が増加します。

## 🏗️ システムアーキテクチャ

### 全体システムアーキテクチャ

```mermaid
graph TD
    Frontend[🖥️ Next.js Frontend<br/>TypeScript + Tailwind CSS<br/>Port: 3000] 
    Backend[⚡ FastAPI Backend<br/>Python + LangChain<br/>Port: 8000]
    
    Frontend -.->|HTTP API| Backend
    Backend -.->|JSON Response| Frontend
    
    Backend --> Controller{🔄 RAG Engines<br/>制御レイヤー<br/>5つの手法を切り替え}
    
    Controller -->|手法に応じて選択| LLM[🤖 Vertex AI<br/>Gemini 2.5 Flash]
    Controller -->|RAG系で使用| Vector[🗄️ FAISS<br/>Vector Store]
    Controller -->|RAG系で使用| Embed[🔤 HuggingFace<br/>Embeddings]
    Controller -->|Function Calling系で使用| Tools[🔧 LangChain<br/>Function Tools]
    Controller -->|手法5で使用| Agent[🎯 LangChain<br/>Agent Executor]
    
    Tools -.->|RAG機能として| Vector
    Tools -.->|RAG機能として| Embed
    Agent -.->|ツール管理| Tools
    Agent -.->|LLM呼び出し| LLM
    
    Backend --> Storage[(📁 File System)]
    Storage --> KB[📚 knowledge.txt]
    Storage --> Logs[📊 Execution Logs]
    
    Tools -.->|データアクセス| KB
    
    style Frontend fill:#e8f5e8,color:#000
    style Backend fill:#fff3e0,color:#000
    style Controller fill:#f0f4c3,color:#000,stroke:#666,stroke-width:3px
    style LLM fill:#e1f5fe,color:#000
    style Vector fill:#e8eaf6,color:#000
    style Embed fill:#f1f8e9,color:#000
    style Tools fill:#fff8e1,color:#000
    style Agent fill:#ffebee,color:#000
    style KB fill:#fce4ec,color:#000
    style Logs fill:#f3e5f5,color:#000
    style Storage fill:#e0f2e1,color:#000
```

### 構成要素の説明

| 要素 | 役割 | 技術詳細 |
|------|------|----------|
| 🖥️ **Next.js Frontend** | ユーザーインターフェース | TypeScript + Tailwind CSS、レスポンシブデザイン |
| ⚡ **FastAPI Backend** | API サーバー | Python、LangChain統合、CORS対応 |
| 🔄 **RAG Engines（制御レイヤー）** | 手法切り替え制御 | 5つの情報提供パターンを統一的に管理・実行 |
| 🤖 **Vertex AI LLM** | 言語モデル | Google Gemini 2.5 Flash、テキスト生成 |
| 🗄️ **FAISS Vector Store** | ベクトルデータベース | 高速類似検索、文書の埋め込み保存 |
| 🔤 **HuggingFace Embeddings** | テキスト埋め込み | sentence-transformers、ベクトル変換 |
| 🔧 **Function Tools** | 動的ツール実行 | LangChainツール、Knowledge Base検索 |
| 🎯 **Agent Executor** | 複数ツール管理 | LangChainエージェント、戦略的実行 |
| 📚 **knowledge.txt** | ナレッジベース | 製品取扱説明書、共通データソース |
| 📊 **Execution Logs** | 実行ログ | JSONL形式、詳細な処理履歴 |

### 手法別システム構成図（静的な関係性）

各情報提供手法の静的な構成要素と関係性を可視化：

#### 手法1: LLM単体利用

```mermaid
graph LR
    User[👤 ユーザー] --> UI[🖥️ WebUI]
    UI --> API[⚡ FastAPI]
    API --> LLM[🤖 Gemini LLM]
    LLM --> API
    API --> UI
    UI --> User
    
    style LLM fill:#e1f5fe,color:#000
    style User fill:#f3e5f5,color:#000
    style UI fill:#e8f5e8,color:#000
    style API fill:#fff3e0,color:#000
```

**特徴**: 最もシンプルな構成。外部情報源は一切使用せず、LLMの内蔵知識のみで回答を生成します。処理速度は最も高速ですが、知識の範囲が限定的です。

#### 手法2: プロンプトスタッフィング

```mermaid
graph LR
    User[👤 ユーザー] --> UI[🖥️ WebUI]
    UI --> API[⚡ FastAPI]
    API --> KB[📚 Knowledge Base]
    KB --> API
    API --> LLM[🤖 Gemini LLM]
    LLM --> API
    API --> UI
    UI --> User
    
    style LLM fill:#e1f5fe,color:#000
    style KB fill:#fce4ec,color:#000
    style User fill:#f3e5f5,color:#000
    style UI fill:#e8f5e8,color:#000
    style API fill:#fff3e0,color:#000
```

**特徴**: Knowledge Baseから全データを読み込み、質問と一緒にプロンプトに埋め込みます。確実で理解しやすい手法ですが、データ量が多い場合はトークン消費量が大きくなります。

#### 手法3: RAGのみ

```mermaid
graph LR
    User[👤 ユーザー] --> UI[🖥️ WebUI]
    UI --> API[⚡ FastAPI]
    API --> Embed[🔤 Embeddings]
    Embed --> VectorDB[(🗄️ Vector Store)]
    VectorDB --> API
    API --> LLM[🤖 Gemini LLM]
    LLM --> API
    API --> UI
    UI --> User
    
    style LLM fill:#e1f5fe,color:#000
    style VectorDB fill:#e8eaf6,color:#000
    style Embed fill:#f1f8e9,color:#000
    style User fill:#f3e5f5,color:#000
    style UI fill:#e8f5e8,color:#000
    style API fill:#fff3e0,color:#000
```

**特徴**: 質問をEmbeddingsでベクトル化し、Vector Storeから関連性の高い文書を検索して回答に活用します。効率的で拡張性が高く、現代的なRAGの基本形です。

#### 手法4: Function Callingのみ

```mermaid
graph LR
    User[👤 ユーザー] --> UI[🖥️ WebUI]
    UI --> API[⚡ FastAPI]
    API --> LLM[🤖 Gemini LLM]
    LLM --> Tools[🔧 Function Tools]
    Tools --> KB[📚 Knowledge Base]
    KB --> Tools
    Tools --> LLM
    LLM --> API
    API --> UI
    UI --> User
    
    style LLM fill:#e1f5fe,color:#000
    style Tools fill:#fff8e1,color:#000
    style KB fill:#fce4ec,color:#000
    style User fill:#f3e5f5,color:#000
    style UI fill:#e8f5e8,color:#000
    style API fill:#fff3e0,color:#000
```

**特徴**: LLMが自律的にFunction Toolsを選択・実行してKnowledge Baseから必要な情報を取得します。LLMの判断力を活用した動的な情報検索が可能です。

#### 手法5: RAG + Function Calling（推奨）

```mermaid
graph LR
    User[👤 ユーザー] --> UI[🖥️ WebUI]
    UI --> API[⚡ FastAPI]
    API --> Agent[🎯 Agent Executor]
    Agent --> LLM[🤖 Gemini LLM]
    LLM --> Agent
    Agent --> Tools[🔧 Function Tools]
    Tools --> Embed[🔤 Embeddings]
    Tools --> VectorDB[(🗄️ Vector Store)]
    Tools --> KB[📚 Knowledge Base]
    Embed --> VectorDB
    VectorDB --> Tools
    KB --> Tools
    Tools --> Agent
    Agent --> API
    API --> UI
    UI --> User
    
    style LLM fill:#e1f5fe,color:#000
    style Agent fill:#ffebee,color:#000
    style Tools fill:#fff8e1,color:#000
    style VectorDB fill:#e8eaf6,color:#000
    style Embed fill:#f1f8e9,color:#000
    style KB fill:#fce4ec,color:#000
    style User fill:#f3e5f5,color:#000
    style UI fill:#e8f5e8,color:#000
    style API fill:#fff3e0,color:#000
```

**特徴**: Agent ExecutorがLLMとFunction Toolsをオーケストレーションし、必要に応じてRAG検索（Embeddings + Vector Store）と直接的なKnowledge Base検索の両方を活用します。最も柔軟で高度な情報検索が可能な推奨手法です。

## 📊 手法別動的フロー（シーケンス図）

静的な構成図の理解に続いて、各手法の動的な処理フローをシーケンス図で説明します：

### 手法1シーケンス: LLM単体利用

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant UI as WebUI
    participant API as FastAPI
    participant LLM as Gemini LLM
    
    User->>UI: 質問入力
    UI->>API: POST /process (llm_only)
    API->>LLM: 質問をそのまま送信
    LLM->>API: 回答生成
    API->>UI: 結果返却
    UI->>User: 回答表示
    
    Note over LLM: 外部情報なし<br/>内蔵知識のみ
```

### 手法2シーケンス: プロンプトスタッフィング

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant UI as WebUI
    participant API as FastAPI
    participant KB as Knowledge Base
    participant LLM as Gemini LLM
    
    User->>UI: 質問入力
    UI->>API: POST /process (prompt_stuffing)
    API->>KB: 全データ読み込み
    KB->>API: knowledge.txt全文
    API->>LLM: 質問+全情報を結合送信
    LLM->>API: 回答生成
    API->>UI: 結果返却
    UI->>User: 回答表示
    
    Note over KB,LLM: 全情報を<br/>プロンプトに埋め込み
```

### 手法3シーケンス: RAGのみ

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant UI as WebUI
    participant API as FastAPI
    participant VectorDB as Vector Store
    participant Embed as Embeddings
    participant LLM as Gemini LLM
    
    User->>UI: 質問入力
    UI->>API: POST /process (rag_only)
    API->>Embed: 質問をベクトル化
    Embed->>API: 質問ベクトル
    API->>VectorDB: 類似検索
    VectorDB->>API: 関連文書
    API->>LLM: 質問+関連文書
    LLM->>API: 回答生成
    API->>UI: 結果返却
    UI->>User: 回答表示
    
    Note over VectorDB: FAISS<br/>ベクトル検索
```

### 手法4シーケンス: Function Callingのみ

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant UI as WebUI
    participant API as FastAPI
    participant LLM as Gemini LLM
    participant Tools as Function Tools
    participant KB as Knowledge Base
    
    User->>UI: 質問入力
    UI->>API: POST /process (function_calling)
    API->>LLM: 質問+利用可能ツール情報
    LLM->>API: ツール使用判断
    API->>Tools: 指定ツール実行
    Tools->>KB: データ検索
    KB->>Tools: 検索結果
    Tools->>API: ツール実行結果
    API->>LLM: ツール結果+質問
    LLM->>API: 回答生成
    API->>UI: 結果返却
    UI->>User: 回答表示
    
    Note over LLM,Tools: LLMが自律的に<br/>ツール選択・実行
```

### 手法5シーケンス: RAG + Function Calling

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant UI as WebUI
    participant API as FastAPI
    participant Agent as Agent Executor
    participant VectorDB as Vector Store
    participant Tools as Function Tools
    participant LLM as Gemini LLM
    participant KB as Knowledge Base
    participant Embed as Embeddings
    
    User->>UI: 質問入力
    UI->>API: POST /process (rag_function_calling)
    API->>Agent: 質問+利用可能ツール
    Agent->>LLM: 戦略立案
    
    alt RAG検索が必要な場合
        LLM->>Agent: RAG検索指示
        Agent->>Tools: RAGツール実行
        Tools->>Embed: 質問をベクトル化
        Embed->>Tools: 質問ベクトル
        Tools->>VectorDB: ベクトル検索
        VectorDB->>Tools: 関連文書
        Tools->>Agent: RAG検索結果
    end
    
    alt 直接検索が必要な場合
        LLM->>Agent: 直接検索指示
        Agent->>Tools: 検索ツール実行
        Tools->>KB: データ検索
        KB->>Tools: 検索結果
        Tools->>Agent: 直接検索結果
    end
    
    Agent->>LLM: 検索結果+質問
    LLM->>Agent: 最終回答
    Agent->>API: 結果
    API->>UI: 結果返却
    UI->>User: 回答表示
    
    Note over Agent: 複数ツールを<br/>組み合わせ活用<br/>状況に応じて選択
```

## 🔍 手法比較表

| 要素 | 手法1 LLM単体 | 手法2 スタッフィング | 手法3 RAG | 手法4 Function Calling | 手法5 RAG+FC |
|------|:---:|:---:|:---:|:---:|:---:|
| **LLM** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Knowledge Base** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Vector Store** | ❌ | ❌ | ✅ | ❌ | ✅ |
| **Embeddings** | ❌ | ❌ | ✅ | ❌ | ✅ |
| **Function Tools** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Agent Executor** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **自律判断** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **効率性** | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **精度** | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **柔軟性** | ⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

### 📝 評価指標の説明

#### 🤖 自律判断
**定義**: LLMが状況に応じて適切なツールや検索手法を自動選択する能力

- **❌ なし**: 事前に決められた処理のみ実行
- **✅ あり**: LLMが動的にツール選択・実行戦略を決定

**読み手の判断基準**: 
- **自律判断が重要な場合**: 多様な質問に対応、予期しない情報ニーズへの対応
- **自律判断が不要な場合**: 決まったパターンの質問、予測可能な処理フロー

#### ⚡ 効率性（処理速度・リソース消費）
**定義**: レスポンス時間とトークン消費量のバランス

- **⭐⭐⭐ 高**: 高速レスポンス、少ないトークン消費
- **⭐⭐ 中**: 中程度の処理時間、適度なリソース使用
- **⭐ 低**: 処理時間が長い、大量のトークン消費

**読み手の判断基準**:
- **高効率が重要**: リアルタイム応答、大量処理、コスト重視
- **効率性より精度**: 複雑な分析、高品質な回答が必要

#### 🎯 精度（回答の正確性・関連性）
**定義**: 質問に対する回答の正確性と情報の関連性

- **⭐⭐⭐ 高**: 外部情報を活用した正確で詳細な回答
- **⭐⭐ 中**: 関連情報は取得できるが、情報選択に課題
- **⭐ 低**: 限定的な知識による曖昧または不正確な回答

**読み手の判断基準**:
- **高精度が必要**: 専門的な質問、事実確認、正確性が重要な業務
- **精度より速度**: 概要把握、ブレインストーミング、一般的な質問

#### 🔧 柔軟性（適応性・拡張性）
**定義**: 多様な質問や新しい要求に対する対応能力

- **⭐⭐⭐ 高**: 複数の検索手法、動的な戦略変更、多様な情報源に対応
- **⭐⭐ 中**: 限定的だが複数の情報取得手法を利用
- **⭐ 低**: 固定的な処理、単一の情報源に依存

**読み手の判断基準**:
- **高柔軟性が重要**: 多様な業務、予期しない質問、将来の拡張性
- **柔軟性より安定性**: 定型的な業務、予測可能な質問パターン

### 💡 手法選択のガイドライン

| 用途・要件 | 推奨手法 | 理由 |
|------------|----------|------|
| **プロトタイプ・検証** | 手法1 LLM単体 | 最速実装、基本性能確認 |
| **小規模データ・確実性重視** | 手法2 スタッフィング | シンプル、確実、理解しやすい |
| **大規模データ・効率重視** | 手法3 RAG | 高効率、拡張性、現代的手法 |
| **動的・多様な要求** | 手法4 Function Calling | 柔軟性、自律性、カスタマイズ性 |
| **本格運用・最高品質** | 手法5 RAG+FC | 総合力、実用性、将来性 |

## 🔧 技術詳細

### 使用技術

#### バックエンド

- **フレームワーク**: FastAPI
- **LLM**: Google Vertex AI (gemini-2.5-flash)
- **RAGライブラリ**: LangChain
- **ベクトル検索**: FAISS
- **埋め込みモデル**: sentence-transformers/all-MiniLM-L6-v2
- **エージェント**: LangChain AgentExecutor
- **ログ**: structlog

#### フロントエンド

- **フレームワーク**: Next.js 15 (React 19)
- **スタイリング**: Tailwind CSS
- **HTTP通信**: Axios
- **UI**: Lucide React Icons
- **通知**: React Hot Toast
- **言語**: TypeScript

### プロジェクト構成

```bash
rag-sample-codes/
├── .gitignore                       # Git除外設定
├── LICENSE                          # MITライセンス
├── README.md                        # このファイル
├── data/
│   └── knowledge.txt               # 製品取扱説明書（共通データ）
├── logs/                           # 実行ログファイル保存先
├── src/
│   ├── backend/                    # Python FastAPI バックエンド
│   │   ├── main.py                # FastAPI アプリケーション本体
│   │   ├── rag_engines.py         # 5つのRAGエンジン実装
│   │   ├── logger_config.py       # ログ設定
│   │   ├── requirements.txt       # Python依存パッケージ
│   │   ├── run_llm_only.py       # 既存実装1: LLM単体利用
│   │   ├── run_prompt_stuffing.py # 既存実装2: プロンプトスタッフィング
│   │   ├── run_rag_only.py        # 既存実装3: RAGのみ
│   │   ├── run_function_calling_only.py # 既存実装4: Function Calling
│   │   └── run_rag_plus_fancall.py # 既存実装5: RAG + Function Calling
│   └── frontend/                   # Next.js フロントエンド
│       ├── src/app/page.tsx       # メインUI
│       ├── package.json           # Node.js依存パッケージ
│       └── ... (その他Next.jsファイル)
└── .venv/                          # Python仮想環境
```

### Webアプリケーション機能

- **直感的なUI**: モダンなレスポンシブWebインターフェース
- **モード切替**: 5つの情報提供手法を簡単に切り替え可能
- **リアルタイム実行ステータス**: 処理の進行状況と中間生成物を表示
- **デモモード**: プレゼンテーション用の遅延表示機能
- **トークン使用量表示**: 入力・出力・総トークン数の詳細表示
- **ナレッジベース編集**: ブラウザ上でknowledge.txtを直接編集可能
- **実行ログ**: JSONL形式での詳細ログ自動生成・ダウンロード機能

### 各手法の実装詳細

#### 1. LLM単体利用

- **目的**: 外部情報を一切与えなかった場合のベースライン確認
- **特徴**: 純粋なLLMの知識のみで回答
- **モデル**: gemini-2.5-flash

#### 2. プロンプトスタッフィング

- **目的**: LLMのコンテキストウィンドウを活用した全情報埋め込み
- **特徴**: knowledge.txtの全内容をプロンプトに含める
- **利点**: シンプルで確実
- **欠点**: トークン消費量が多い

#### 3. RAGのみ

- **目的**: 現代的なRAGアーキテクチャの基本形
- **特徴**:
  - ベクトル検索による関連情報の取得
  - FAISS + HuggingFace Embeddings
  - LCELチェーンによる処理
- **利点**: 効率的で拡張性が高い

#### 4. Function Callingのみ

- **目的**: LLMの自律的ツール利用能力の検証
- **特徴**:
  - `@tool`デコレーターによるツール定義
  - LLMの自律的なツール選択
- **利点**: 柔軟で動的な情報取得

#### 5. RAG + Function Calling ⭐推奨⭐

- **目的**: RAG検索とツール利用の組み合わせによる最高度な構成
- **特徴**:
  - AgentExecutorによる複数ツールの管理
  - RAGをツール化した高度な検索
  - verbose=Trueで思考プロセスが見える
- **利点**: 最も柔軟で実用的

### テストクエリ

すべての実装で共通のテストクエリを使用できます：

「エラーコードE-404の対処法は？」

このクエリは、knowledge.txtに含まれる具体的な情報（E-404エラーの対処法）を問うものです。

### 期待される結果の比較

1. **LLM単体**: 一般的な知識に基づく曖昧な回答
2. **プロンプトスタッフィング**: 完全で正確な回答（トークン消費大）
3. **RAGのみ**: 関連性の高い正確な回答
4. **Function Calling**: ツール使用による動的な情報検索
5. **RAG + Function Calling**: 最も柔軟で実用的な回答

## ✍🏻詳細セットアップと使用方法

### 1. 前提条件

- Python 3.10以上
- Node.js 18以上
- Google Cloud Projectの設定（Vertex AI APIの有効化）
- Google Cloud認証の設定

### 2. Google Cloud設定

#### 2.1 Google Cloud Projectの作成・設定

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成するか、既存のプロジェクトを選択
3. **Vertex AI API**を有効化:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

#### 2.2 認証設定

以下のいずれかの方法で認証を設定してください：

**方法A: サービスアカウントキー（推奨）**
1. Google Cloud Consoleで「IAM & Admin」→「Service Accounts」に移動
2. 新しいサービスアカウントを作成（ロール: Vertex AI User）
3. キーファイル（JSON）をダウンロード
4. 環境変数を設定:
   ```bash
   # Windows PowerShell
   $env:GOOGLE_APPLICATION_CREDENTIALS="path\to\your\service-account-key.json"
   $env:GOOGLE_CLOUD_PROJECT="your-project-id"
   
   # Linux/Mac
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   ```

**方法B: gcloud CLIによる認証**
```bash
# Google Cloud CLIをインストール後
gcloud auth application-default login
gcloud config set project your-project-id
```

#### 2.3 環境変数設定ファイル

プロジェクトルートに`.env`ファイルを作成:
```bash
# .envファイルを作成
cp .env.example .env
```

`.env`ファイルを編集して、実際の値を設定:
```bash
GOOGLE_CLOUD_PROJECT=your-actual-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
GOOGLE_CLOUD_REGION=us-central1
```

### 3. インストール手順

#### バックエンド（Python）

```bash
# 仮想環境作成・有効化
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 依存関係インストール
pip install -r src/backend/requirements.txt
```

#### フロントエンド（Node.js）

```bash
cd src/frontend
npm install
```

### 3. 実行方法

#### 開発サーバー起動

```bash
# バックエンド起動（ターミナル1）
python src/backend/main.py

# フロントエンド起動（ターミナル2）  
cd src/frontend
npm run dev
```

#### アプリケーションへのアクセス

- **フロントエンド**: <http://localhost:3000>
- **バックエンドAPI**: <http://localhost:8000>
- **API仕様書**: <http://localhost:8000/docs>

### 4. 使用方法

1. ブラウザで <http://localhost:3000> にアクセス
2. 処理モードを選択（5つのパターンから選択）
3. 質問を入力（例: 「エラーコードE-404の対処法は？」）
4. 「送信」ボタンをクリック
5. リアルタイムで処理状況・結果・トークン数を確認
6. 必要に応じてナレッジベースを編集
7. 実行ログをダウンロード

## 📊 ログフォーマット

実行ログは`logs/`フォルダに`YYYYMMDDHHMMSS_llm-rag-exp.jsonl`形式で保存されます：

```json
{
  "timestamp": "2025-07-02T15:30:45.123456",
  "execution_mode": "rag_function_calling",
  "query": "エラーコードE-404の対処法は？",
  "response": "...",
  "input_tokens": 150,
  "output_tokens": 200,
  "total_tokens": 350,
  "execution_time": 3.45,
  "intermediate_steps": [...],
  "demo_mode": false
}
```

## 🎓 学習ポイント

- RAGの基本的な仕組みとメリット
- Function Callingの自律性と柔軟性
- プロンプトスタッフィングのシンプルさと制限
- LLM単体の限界
- RAG + Function Callingの組み合わせによる相乗効果
- フルスタックWebアプリケーション開発
- API設計とフロントエンド・バックエンド連携

## 💡 次のステップ

このシステムを基に、以下の拡張が可能です：

- 複数のデータソースへの対応
- より高度なツールの追加
- ストリーミング対応
- マルチターン会話の実装
- 評価メトリクスの追加
- 認証・権限管理
- デプロイメント対応

## �️ トラブルシューティング

### Google Cloud関連エラー

**エラー**: `Unable to find your project. Please provide a project ID...`

**原因**: Google CloudのプロジェクトIDが設定されていません。

**対処法**:
1. `.env`ファイルにプロジェクトIDを設定:
   ```bash
   GOOGLE_CLOUD_PROJECT=your-actual-project-id
   ```
2. または環境変数を設定:
   ```bash
   # Windows
   set GOOGLE_CLOUD_PROJECT=your-project-id
   # Linux/Mac
   export GOOGLE_CLOUD_PROJECT=your-project-id
   ```

**エラー**: `File turtle-ai-project-bbe3c41d9409.json was not found.` または `DefaultCredentialsError`

**原因**: Google Cloud認証情報が設定されていません。

**対処法**:

1. **サービスアカウントキーを使用する場合**:
   ```bash
   # キーファイルをダウンロード後、.envファイルに追加
   GOOGLE_APPLICATION_CREDENTIALS=C:/path/to/your/service-account-key.json
   ```

2. **gcloud CLIを使用する場合** (推奨):
   ```bash
   # Google Cloud CLIをインストール後
   gcloud auth application-default login
   gcloud config set project your-project-id
   ```

3. **認証状況の確認**:
   ```bash
   # ブラウザまたはcurlで確認
   curl http://localhost:8000/auth/status
   ```

**エラー**: `Authentication failed` または `Credentials not found`

**対処法**:
1. サービスアカウントキーを使用する場合:
   ```bash
   set GOOGLE_APPLICATION_CREDENTIALS=path\to\service-account-key.json
   ```
2. gcloud認証を使用する場合:
   ```bash
   gcloud auth application-default login
   ```

### その他のエラー

- **バックエンドが起動しない**: `pip install -r src/backend/requirements.txt`で依存関係を再インストール
- **フロントエンドが起動しない**: `npm install`で依存関係を再インストール
- **ナレッジベースが見つからない**: `data/knowledge.txt`ファイルが存在することを確認

## �📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

---

**重要**: このプロジェクトを実行するには、Google Cloud ProjectでのVertex AI API有効化と適切な認証設定が必要です。上記のクイックスタートガイドに従って設定を行ってください。
