# 各種情報提供手法の比較用RAGプロトタイプ群

このプロジェクトは、LLMに外部情報を与えるための複数の手法を比較・検証する目的で、5つの異なるパターンのPythonスクリプトを実装しています。最終的な目標は、RAGとFunction Callingを組み合わせた高度なエージェントを構築することですが、その前に各アプローチの長所と短所を理解するため、個別のプロトタイプを作成しています。

## 📁 プロジェクト構成

```
rag-sample-codes/
├── .gitignore                       # Git除外設定
├── LICENSE                          # MITライセンス
├── knowledge.txt                    # 製品取扱説明書（共通データ）
├── requirements.txt                 # 必要なPythonパッケージ
├── main.py                         # 全プロトタイプの実行スクリプト
├── run_llm_only.py                 # 実装1: LLM単体利用
├── run_prompt_stuffing.py          # 実装2: プロンプトスタッフィング
├── run_rag_only.py                 # 実装3: RAGのみ
├── run_function_calling_only.py    # 実装4: Function Callingのみ
├── run_rag_plus_fancall.py         # 実装5: RAG + Function Calling
└── README.md                       # このファイル
```

## 🎯 各実装の目的と特徴

### 実装1: LLM単体利用 (`run_llm_only.py`)
- **目的**: 外部情報を一切与えなかった場合の、LLMの基準（ベースライン）を確認
- **特徴**: 純粋なLLMの知識のみで回答
- **モデル**: gemini-2.5-flash

### 実装2: プロンプトスタッフィング (`run_prompt_stuffing.py`)
- **目的**: LLMの広大なコンテキストウィンドウを使い、力技で全ての情報を与える手法
- **特徴**: knowledge.txtの全内容をプロンプトに埋め込み
- **利点**: シンプルで確実
- **欠点**: トークン消費量が多い

### 実装3: RAGのみ (`run_rag_only.py`)
- **目的**: 現代的なRAGアーキテクチャの基本形を実装
- **特徴**: 
  - ベクトル検索による関連情報の取得
  - FAISS + HuggingFace Embeddings
  - LCELチェーンによる処理
- **利点**: 効率的で拡張性が高い

### 実装4: Function Callingのみ (`run_function_calling_only.py`)
- **目的**: LLMが自律的にツール（関数）を呼び出す挙動の基本を実装
- **特徴**: 
  - `@tool`デコレーターによるツール定義
  - LLMの自律的なツール選択
- **利点**: 柔軟で動的な情報取得

### 実装5: RAG + Function Calling (`run_rag_plus_fancall.py`) ⭐推奨⭐
- **目的**: RAGの強力な検索能力をツール化し、LLMに他のツールと使い分けさせる最高度な構成
- **特徴**: 
  - AgentExecutorによる複数ツールの管理
  - RAGをツール化した高度な検索
  - verbose=Trueで思考プロセスが見える
- **利点**: 最も柔軟で実用的

## 🚀 セットアップと実行

### 1. 前提条件
- Python 3.10以上
- Google Cloud Projectの設定（Vertex AI APIの有効化）
- 適切な認証情報の設定

### 2. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 3. 実行方法

#### 全プロトタイプを順次実行
```bash
python main.py
```

#### 個別実行
```bash
# 実装1: LLM単体利用
python run_llm_only.py

# 実装2: プロンプトスタッフィング  
python run_prompt_stuffing.py

# 実装3: RAGのみ
python run_rag_only.py

# 実装4: Function Callingのみ
python run_function_calling_only.py

# 実装5: RAG + Function Calling（推奨）
python run_rag_plus_fancall.py
```

## 📊 テストクエリ

すべての実装で共通のテストクエリを使用しています：
**「エラーコードE-404の対処法は？」**

このクエリは、knowledge.txtに含まれる具体的な情報（E-404エラーの対処法）を問うものです。

## 🔧 使用技術

- **LLM**: Google Vertex AI (gemini-2.5-flash)
- **フレームワーク**: LangChain
- **ベクトル検索**: FAISS
- **埋め込みモデル**: sentence-transformers/all-MiniLM-L6-v2
- **エージェント**: LangChain AgentExecutor

## 📈 期待される結果の比較

1. **実装1**: 一般的な知識に基づく曖昧な回答
2. **実装2**: 完全で正確な回答（トークン消費大）
3. **実装3**: 関連性の高い正確な回答
4. **実装4**: ツール使用による動的な情報検索
5. **実装5**: 最も柔軟で実用的な回答

## 🎓 学習ポイント

- RAGの基本的な仕組みとメリット
- Function Callingの自律性と柔軟性
- プロンプトスタッフィングのシンプルさと制限
- LLM単体の限界
- RAG + Function Callingの組み合わせによる相乗効果

## 💡 次のステップ

このプロトタイプを基に、以下の拡張が可能です：

- 複数のデータソースへの対応
- より高度なツールの追加
- ストリーミング対応
- マルチターン会話の実装
- 評価メトリクスの追加

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

---

**注意**: このプロジェクトを実行するには、Google Cloud Projectでの適切な設定とVertex AI APIの有効化が必要です。
