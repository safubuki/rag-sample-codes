'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { Send, Settings, FileText, Download, Loader2, Database, Play, CheckCircle } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';

interface ProcessingMode {
  value: string;
  label: string;
  description: string;
}

interface IntermediateStep {
  step: string;
  data: any;
  timestamp: string;
}

interface ProcessResponse {
  result: string;
  execution_time: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  intermediate_steps: IntermediateStep[];
  log_file: string;
}

const MODES: ProcessingMode[] = [
  { value: 'llm_only', label: 'LLM単体', description: '外部情報なしでLLMのみ' },
  { value: 'prompt_stuffing', label: 'プロンプトスタッフィング', description: '全情報をプロンプトに埋め込み' },
  { value: 'rag_only', label: 'RAGのみ', description: 'ベクトル検索による情報取得' },
  { value: 'function_calling', label: 'Function Calling', description: 'LLMによる動的ツール利用' },
  { value: 'rag_function_calling', label: 'RAG + Function Calling', description: 'RAGとFunction Callingの組み合わせ' }
];

export default function Home() {
  const [query, setQuery] = useState('');
  const [selectedMode, setSelectedMode] = useState('llm_only');
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState('');
  const [knowledgeContent, setKnowledgeContent] = useState('');
  const [showKnowledgeEditor, setShowKnowledgeEditor] = useState(false);
  const [executionTime, setExecutionTime] = useState(0);
  const [tokenCounts, setTokenCounts] = useState({ input: 0, output: 0, total: 0 });
  const [intermediateSteps, setIntermediateSteps] = useState<IntermediateStep[]>([]);
  const [currentStep, setCurrentStep] = useState('');
  const [progress, setProgress] = useState(0);
  const [demoMode, setDemoMode] = useState(false);
  const [logFiles, setLogFiles] = useState<string[]>([]);

  // knowledge.txtの内容を取得
  const fetchKnowledge = async () => {
    try {
      const response = await axios.get('http://localhost:8000/knowledge/content');
      setKnowledgeContent(response.data.content);
    } catch (error) {
      toast.error('ナレッジファイルの取得に失敗しました');
    }
  };

  // ログファイル一覧を取得
  const fetchLogFiles = async () => {
    try {
      const response = await axios.get('http://localhost:8000/logs');
      setLogFiles(response.data.files);
    } catch (error) {
      console.error('ログファイル一覧の取得に失敗:', error);
    }
  };

  useEffect(() => {
    fetchKnowledge();
    fetchLogFiles();
  }, []);

  // knowledge.txtを保存
  const saveKnowledge = async () => {
    try {
      await axios.put('http://localhost:8000/knowledge', { content: knowledgeContent });
      toast.success('ナレッジファイルを保存しました');
      setShowKnowledgeEditor(false);
    } catch (error) {
      toast.error('ナレッジファイルの保存に失敗しました');
    }
  };

  // クエリを処理
  const processQuery = async () => {
    if (!query.trim()) {
      toast.error('質問を入力してください');
      return;
    }

    setIsProcessing(true);
    setResult('');
    setIntermediateSteps([]);
    setCurrentStep('処理を開始しています...');
    setProgress(0);

    try {
      const response = await axios.post<ProcessResponse>('http://localhost:8000/process', {
        query: query.trim(),
        mode: selectedMode,
        demo_mode: demoMode
      });

      setResult(response.data.result);
      setExecutionTime(response.data.execution_time);
      setTokenCounts({
        input: response.data.input_tokens,
        output: response.data.output_tokens,
        total: response.data.total_tokens
      });
      setIntermediateSteps(response.data.intermediate_steps);
      setCurrentStep('完了');
      setProgress(100);
      
      toast.success('処理が完了しました');
      fetchLogFiles(); // ログファイル一覧を更新
    } catch (error) {
      toast.error('処理中にエラーが発生しました');
      setCurrentStep('エラー');
    } finally {
      setIsProcessing(false);
    }
  };

  // ログファイルをダウンロード
  const downloadLog = async (filename: string) => {
    try {
      const response = await axios.get(`http://localhost:8000/logs/${filename}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('ログファイルのダウンロードに失敗しました');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <Toaster position="top-right" />
      
      <div className="max-w-7xl mx-auto">
        {/* ヘッダー */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            RAG比較システム
          </h1>
          <p className="text-gray-600">
            5つの異なるLLM情報提供手法を比較・検証
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左パネル: 入力とモード選択 */}
          <div className="lg:col-span-1 space-y-6">
            {/* モード選択 */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <Settings className="mr-2" size={20} />
                処理モード
              </h3>
              <div className="space-y-3">
                {MODES.map((mode) => (
                  <label key={mode.value} className="flex items-start space-x-3 cursor-pointer">
                    <input
                      type="radio"
                      name="mode"
                      value={mode.value}
                      checked={selectedMode === mode.value}
                      onChange={(e) => setSelectedMode(e.target.value)}
                      className="mt-1"
                    />
                    <div>
                      <div className="font-medium text-sm">{mode.label}</div>
                      <div className="text-xs text-gray-500">{mode.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* 質問入力 */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4">質問入力</h3>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="質問を入力してください（例: エラーコードE-404の対処法は？）"
                className="w-full h-32 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                onClick={processQuery}
                disabled={isProcessing}
                className="w-full mt-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-2 px-4 rounded-lg flex items-center justify-center"
              >
                {isProcessing ? (
                  <Loader2 className="mr-2 animate-spin" size={16} />
                ) : (
                  <Send className="mr-2" size={16} />
                )}
                {isProcessing ? '処理中...' : '送信'}
              </button>
            </div>

            {/* デモモード */}
            <div className="bg-white rounded-lg shadow-md p-4">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={demoMode}
                  onChange={(e) => setDemoMode(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm text-gray-600">デモモード（遅延表示）</span>
              </label>
            </div>
          </div>

          {/* 中央パネル: 結果表示 */}
          <div className="lg:col-span-1 space-y-6">
            {/* 実行ステータス */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <Play className="mr-2" size={20} />
                実行ステータス
              </h3>
              <div className="space-y-3">
                <div className="text-sm text-gray-600">{currentStep}</div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                {executionTime > 0 && (
                  <div className="text-sm text-gray-500">
                    実行時間: {executionTime.toFixed(2)}秒
                  </div>
                )}
              </div>
            </div>

            {/* トークン数 */}
            {tokenCounts.total > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-4">トークン使用量</h3>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-blue-600">{tokenCounts.input}</div>
                    <div className="text-xs text-gray-500">入力</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">{tokenCounts.output}</div>
                    <div className="text-xs text-gray-500">出力</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-600">{tokenCounts.total}</div>
                    <div className="text-xs text-gray-500">合計</div>
                  </div>
                </div>
              </div>
            )}

            {/* 中間生成物 */}
            {intermediateSteps.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <Database className="mr-2" size={20} />
                  中間生成物
                </h3>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {intermediateSteps.map((step, index) => (
                    <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                      <div className="font-medium text-sm">{step.step}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {JSON.stringify(step.data, null, 2).substring(0, 100)}...
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 右パネル: 結果とナレッジ */}
          <div className="lg:col-span-1 space-y-6">
            {/* 結果表示 */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <CheckCircle className="mr-2" size={20} />
                処理結果
              </h3>
              <div className="bg-gray-50 rounded-lg p-4 min-h-64">
                {result ? (
                  <div className="whitespace-pre-wrap text-sm">{result}</div>
                ) : (
                  <div className="text-gray-400 text-center">結果がここに表示されます</div>
                )}
              </div>
            </div>

            {/* ナレッジファイル */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center">
                  <FileText className="mr-2" size={20} />
                  ナレッジベース
                </h3>
                <button
                  onClick={() => setShowKnowledgeEditor(!showKnowledgeEditor)}
                  className="text-blue-600 hover:text-blue-700 text-sm"
                >
                  {showKnowledgeEditor ? '閉じる' : '編集'}
                </button>
              </div>
              
              {showKnowledgeEditor ? (
                <div className="space-y-4">
                  <textarea
                    value={knowledgeContent}
                    onChange={(e) => setKnowledgeContent(e.target.value)}
                    className="w-full h-64 p-3 border border-gray-300 rounded-lg resize-none font-mono text-sm"
                  />
                  <button
                    onClick={saveKnowledge}
                    className="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg"
                  >
                    保存
                  </button>
                </div>
              ) : (
                <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                  <pre className="text-xs whitespace-pre-wrap">
                    {knowledgeContent || 'ナレッジファイルが読み込まれていません'}
                  </pre>
                </div>
              )}
            </div>

            {/* ログファイル */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <Download className="mr-2" size={20} />
                実行ログ
              </h3>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {logFiles.length > 0 ? (
                  logFiles.map((file, index) => (
                    <button
                      key={index}
                      onClick={() => downloadLog(file)}
                      className="w-full text-left text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 p-2 rounded"
                    >
                      {file}
                    </button>
                  ))
                ) : (
                  <div className="text-gray-400 text-sm">ログファイルがありません</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
