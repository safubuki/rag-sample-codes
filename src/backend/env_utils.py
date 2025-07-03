"""
環境設定用のユーティリティモジュール
プロジェクトルートを自動検出して.envファイルを読み込む
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def find_project_root(current_path: Optional[Path] = None) -> Path:
    """
    プロジェクトルートを自動検出する
    
    Args:
        current_path: 検索開始パス（デフォルトは現在のファイルの場所）
        
    Returns:
        プロジェクトルートのPath
        
    Raises:
        FileNotFoundError: プロジェクトルートが見つからない場合
    """
    if current_path is None:
        # 実行中のスクリプトから相対的に検索
        current_path = Path.cwd()

    # 特定のマーカーファイルを探してプロジェクトルートを判定
    markers = [".env", ".env.example", "README.md", ".git"]

    path = current_path.absolute()
    for parent in [path] + list(path.parents):
        if any((parent / marker).exists() for marker in markers):
            return parent

    # 見つからない場合はcwdから3階層上を試行
    fallback_path = Path.cwd().parent.parent
    if fallback_path.exists():
        return fallback_path

    # 最終的にcwdを返す
    return Path.cwd()


def setup_environment():
    """
    環境変数を設定する
    プロジェクトルートの.envファイルを自動検出して読み込む
    """
    try:
        project_root = find_project_root()
        env_path = project_root / '.env'

        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            print(f"環境変数をロードしました: {env_path}")
        else:
            print(f"警告: .envファイルが見つかりません: {env_path}")
            # フォールバック: デフォルトのload_dotenv()を試行
            load_dotenv()

    except Exception as e:
        print(f"環境変数の読み込みでエラーが発生しました: {e}")
        # フォールバック: デフォルトのload_dotenv()を試行
        load_dotenv()


def get_google_cloud_project() -> Optional[str]:
    """
    Google CloudプロジェクトIDを取得する
    
    Returns:
        プロジェクトID（見つからない場合はNone）
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("警告: GOOGLE_CLOUD_PROJECT環境変数が設定されていません。")
        print("以下のいずれかの方法でプロジェクトIDを設定してください:")
        print("1. .envファイルでGOOGLE_CLOUD_PROJECT=your-project-idを設定")
        print("2. 環境変数を設定: set GOOGLE_CLOUD_PROJECT=your-project-id (Windows)")
        print("3. gcloud config set project your-project-id")
        print("\n認証についても以下のいずれかが必要です:")
        print("A. サービスアカウントキー: GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json")
        print("B. gcloud認証: gcloud auth application-default login")
        print("C. Google Cloud Shell環境での実行")
    return project_id


def get_google_credentials():
    """
    Google Cloud認証情報を取得する
    
    Returns:
        Google Cloud認証情報またはNone
    """
    from google.oauth2 import service_account

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if credentials_path and Path(credentials_path).exists():
        try:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=["https://www.googleapis.com/auth/cloud-platform"])
            print(f"✅ サービスアカウントキーを読み込みました: {credentials_path}")
            return credentials
        except Exception as e:
            print(f"❌ サービスアカウントキーの読み込みに失敗しました: {e}")
            print(f"ファイルパス: {credentials_path}")
            print("ファイルが存在し、適切なJSONフォーマットかどうか確認してください。")
            return None
    elif credentials_path:
        print(f"❌ サービスアカウントキーファイルが見つかりません: {credentials_path}")
        print("GOOGLE_APPLICATION_CREDENTIALSで指定されたパスを確認してください。")
        return None

    # 環境変数が設定されていない場合はデフォルト認証を試行
    print("ℹ️ デフォルト認証を使用します")
    return None


def check_google_cloud_auth() -> bool:
    """
    Google Cloud認証の状態をチェックする
    
    Returns:
        認証が設定されているかどうか
    """
    # Google Cloud Shell環境チェック
    if os.getenv("GOOGLE_CLOUD_SHELL"):
        print("✅ Google Cloud Shell環境で実行中")
        return True

    # サービスアカウントキーのチェック
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path and Path(credentials_path).exists():
        print(f"✅ サービスアカウントキーが設定されています: {credentials_path}")
        return True

    # gcloud認証の確認
    try:
        import subprocess
        result = subprocess.run(["gcloud", "auth", "list", "--filter=status:ACTIVE"],
                                capture_output=True,
                                text=True,
                                timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            print("✅ gcloud認証が設定されています")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    print("❌ Google Cloud認証が設定されていません")
    print("\n🔧 認証設定方法:")
    print("方法1: サービスアカウントキー")
    print("  1. Google Cloud Consoleで「IAM & Admin」→「Service Accounts」")
    print("  2. サービスアカウントを作成（ロール: Vertex AI User）")
    print("  3. キーファイル（JSON）をダウンロード")
    print("  4. .envファイルに追加: GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json")
    print("\n方法2: gcloud CLI認証")
    print("  1. Google Cloud CLIをインストール")
    print("  2. 実行: gcloud auth application-default login")
    print("  3. 実行: gcloud config set project your-project-id")
    print("\n方法3: 環境変数での認証")
    print("  set GOOGLE_APPLICATION_CREDENTIALS=path\\to\\key.json")

    return False


def create_mock_llm_if_needed():
    """
    認証が設定されていない場合のモックLLM設定
    """
    if not check_google_cloud_auth():
        print("\n⚠️  実際のVertex AIを使用するには認証が必要です")
        print("🔄 デモ用にモックレスポンスを使用することもできます")
        print("   .envファイルでUSE_MOCK_LLM=trueに設定してください")
        return True
    return False


def create_vertex_ai_llm(model_name: str = "gemini-2.5-flash", temperature: float = 0.1):
    """
    Vertex AI LLMを適切に初期化する共通関数
    
    Args:
        model_name: 使用するモデル名
        temperature: 温度パラメータ
        
    Returns:
        初期化されたChatVertexAIインスタンス
    """
    from langchain_google_vertexai import ChatVertexAI

    project_id = get_google_cloud_project()
    credentials = get_google_credentials()

    try:
        if credentials:
            # 明示的にクレデンシャルを指定
            llm = ChatVertexAI(model_name=model_name,
                               temperature=temperature,
                               project=project_id,
                               credentials=credentials)
        else:
            # デフォルト認証を使用
            llm = ChatVertexAI(model_name=model_name, temperature=temperature, project=project_id)

        print(f"✅ Vertex AI LLM ({model_name}) の初期化が成功しました")
        return llm

    except Exception as e:
        print(f"❌ Vertex AI LLMの初期化に失敗しました: {e}")
        print("認証設定を確認してください:")
        print(f"  - GOOGLE_CLOUD_PROJECT: {project_id}")
        print(f"  - GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
        raise
