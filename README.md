# 構造化RAG比較システム

このプロジェクトは、LLMに外部情報を与えるための複数の手法を比較・検証する目的で、5つの異なるパターンのRAG実装を提供する**フルスタックWebアプリケーション**です。PythonのFastAPIバックエンドとNext.jsフロントエンドで構築されており、デモモード・実行ログ・トークン数表示などの高度な機能を備えています。

## 📁 プロジェクト構成

```
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

## 🎯 システム機能

### Webアプリケーション機能

- **直感的なUI**: モダンなレスポンシブWebインターフェース
- **モード切替**: 5つのRAGパターンを簡単に切り替え可能
- **リアルタイム実行ステータス**: 処理の進行状況と中間生成物を表示
- **デモモード**: プレゼンテーション用の遅延表示機能
- **トークン使用量表示**: 入力・出力・総トークン数の詳細表示
- **ナレッジベース編集**: ブラウザ上でknowledge.txtを直接編集可能
- **実行ログ**: JSONL形式での詳細ログ自動生成・ダウンロード機能

### 5つのRAG実装パターン

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

## 🚀 セットアップと実行

### 1. 前提条件

- Python 3.10以上
- Node.js 18以上
- Google Cloud Projectの設定（Vertex AI APIの有効化）
- 適切な認証情報の設定

### 2. インストール手順

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

#### アクセス

- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **API仕様書**: http://localhost:8000/docs

### 4. 使用方法

1. ブラウザで http://localhost:3000 にアクセス
2. 処理モードを選択（5つのパターンから選択）
3. 質問を入力（例: 「エラーコードE-404の対処法は？」）
4. 「送信」ボタンをクリック
5. リアルタイムで処理状況・結果・トークン数を確認
6. 必要に応じてナレッジベースを編集
7. 実行ログをダウンロード

## 📊 テストクエリ

すべての実装で共通のテストクエリを使用できます：
**「エラーコードE-404の対処法は？」**

このクエリは、knowledge.txtに含まれる具体的な情報（E-404エラーの対処法）を問うものです。

## 🔧 使用技術

### バックエンド

- **フレームワーク**: FastAPI
- **LLM**: Google Vertex AI (gemini-2.5-flash)
- **RAGライブラリ**: LangChain
- **ベクトル検索**: FAISS
- **埋め込みモデル**: sentence-transformers/all-MiniLM-L6-v2
- **エージェント**: LangChain AgentExecutor
- **ログ**: structlog

### フロントエンド

- **フレームワーク**: Next.js 15 (React 19)
- **スタイリング**: Tailwind CSS
- **HTTP通信**: Axios
- **UI**: Lucide React Icons
- **通知**: React Hot Toast
- **言語**: TypeScript

## 📈 期待される結果の比較

1. **LLM単体**: 一般的な知識に基づく曖昧な回答
2. **プロンプトスタッフィング**: 完全で正確な回答（トークン消費大）
3. **RAGのみ**: 関連性の高い正確な回答
4. **Function Calling**: ツール使用による動的な情報検索
5. **RAG + Function Calling**: 最も柔軟で実用的な回答

## 📁 ログフォーマット

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

## 🏗️ アーキテクチャ

```mermaid
┌─────────────────┐    HTTP API    ┌─────────────────┐
│  Next.js        │ ◄─────────────► │  FastAPI        │
│  Frontend       │    Port 3000   │  Backend        │
│  (TypeScript)   │                │  (Python)       │
└─────────────────┘                └─────────────────┘
                                           │
                                           ▼
                                   ┌─────────────────┐
                                   │  RAG Engines    │
                                   │  - LLM Only     │
                                   │  - Prompt Stuff │
                                   │  - RAG Only     │
                                   │  - Function Call│
                                   │  - RAG + FC     │
                                   └─────────────────┘
                                           │
                                           ▼
                                   ┌─────────────────┐
                                   │  External APIs  │
                                   │  - Vertex AI    │
                                   │  - FAISS        │
                                   │  - HuggingFace  │
                                   └─────────────────┘
```

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

---

**注意**: このプロジェクトを実行するには、Google Cloud Projectでの適切な設定とVertex AI APIの有効化が必要です。
