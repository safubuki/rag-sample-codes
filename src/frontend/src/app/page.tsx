'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { Send, Settings, FileText, Download, Loader2, Database, Play, CheckCircle, ChevronDown, ChevronUp, Eye, EyeOff } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';

interface ProcessingMode {
  value: string;
  label: string;
  description: string;
  color: string;
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
  { value: 'llm_only', label: 'LLM単体', description: '外部情報なしでLLMのみ', color: 'bg-gray-100 text-gray-800 border-gray-300' },
  { value: 'prompt_stuffing', label: 'プロンプトスタッフィング', description: '全情報をプロンプトに埋め込み', color: 'bg-blue-100 text-blue-800 border-blue-300' },
  { value: 'rag_only', label: 'RAGのみ', description: 'ベクトル検索による情報取得', color: 'bg-green-100 text-green-800 border-green-300' },
  { value: 'function_calling', label: 'Function Calling', description: 'LLMによる動的ツール利用', color: 'bg-purple-100 text-purple-800 border-purple-300' },
  { value: 'rag_function_calling', label: 'RAG + Function Calling', description: 'RAGとFunction Callingの組み合わせ（推奨）', color: 'bg-amber-100 text-amber-800 border-amber-300' }
];

export default function Home() {
  const [query, setQuery] = useState('');
  const [selectedMode, setSelectedMode] = useState('rag_function_calling');
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
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [showIntermediateSteps, setShowIntermediateSteps] = useState(false);
  const [showLogs, setShowLogs] = useState(false);

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
    setShowIntermediateSteps(true);

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
      fetchLogFiles();
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

  const selectedModeData = MODES.find(mode => mode.value === selectedMode);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Toaster position="top-right" />
      
      {/* ヘッダー */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-6 py-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            LLM情報提供手法比較システム
          </h1>
          <p className="text-gray-600 text-lg">
            5つの異なるLLM情報提供手法を比較・検証するシステム
          </p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        
        {/* メイン処理エリア */}
        <div className="space-y-6">
          
          {/* 1. モード選択 - 最重要 */}
          <div className="bg-white rounded-xl shadow-lg border p-6">
            <div className="flex items-center mb-6">
              <div className="bg-blue-100 p-3 rounded-lg mr-4">
                <Settings className="text-blue-600" size={24} />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">処理モードの選択</h2>
                <p className="text-gray-600">使用する情報提供手法を選択してください</p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {MODES.map((mode) => (
                <label key={mode.value} className={`cursor-pointer group ${
                  mode.value === 'rag_function_calling' ? 'md:col-span-2 lg:col-span-2' : ''
                }`}>
                  <div className={`relative p-4 rounded-xl border-2 transition-all duration-200 h-20 flex items-center ${
                    selectedMode === mode.value 
                      ? `${mode.color} border-opacity-100 shadow-md scale-[1.02]` 
                      : 'bg-gray-50 border-gray-200 hover:border-gray-300 hover:shadow-sm'
                  }`}>
                    <input
                      type="radio"
                      name="mode"
                      value={mode.value}
                      checked={selectedMode === mode.value}
                      onChange={(e) => setSelectedMode(e.target.value)}
                      className="absolute top-3 right-3"
                    />
                    <div className="pr-8 flex-1">
                      <div className="font-semibold text-sm mb-1 flex items-center">
                        {mode.label}
                        {mode.value === 'rag_function_calling' && (
                          <span className="ml-2 text-xs font-medium bg-amber-600 text-white px-2 py-1 rounded-full">推奨</span>
                        )}
                      </div>
                      <div className="text-xs opacity-75">{mode.description}</div>
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* 2. 質問入力 - 重要 */}
          <div className="bg-white rounded-xl shadow-lg border p-6">
            <div className="flex items-center mb-4">
              <div className="bg-green-100 p-3 rounded-lg mr-4">
                <Send className="text-green-600" size={24} />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">質問を入力</h2>
                <p className="text-gray-600">知りたいことを自然な言葉で入力してください</p>
              </div>
            </div>
            
            <div className="space-y-4">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="例: エラーコードE-404の対処法を教えてください"
                className="w-full h-24 p-4 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
                disabled={isProcessing}
              />
              
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-500">
                  選択中: <span className={`px-2 py-1 rounded text-xs font-medium ${selectedModeData?.color}`}>
                    {selectedModeData?.label}
                  </span>
                </div>
                
                <button
                  onClick={processQuery}
                  disabled={isProcessing || !query.trim()}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-3 px-8 rounded-lg flex items-center font-semibold text-lg transition-all duration-200 shadow-lg hover:shadow-xl disabled:shadow-none"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="mr-3 animate-spin" size={20} />
                      処理中...
                    </>
                  ) : (
                    <>
                      <Send className="mr-3" size={20} />
                      実行する
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* 3. 実行ステータス - 処理中に重要 */}
          {(isProcessing || result) && (
            <div className="bg-white rounded-xl shadow-lg border p-6">
              <div className="flex items-center mb-4">
                <div className="bg-purple-100 p-3 rounded-lg mr-4">
                  <Play className="text-purple-600" size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">実行ステータス</h2>
                  <p className="text-gray-600">{currentStep}</p>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                
                <div className="flex justify-between text-sm text-gray-600">
                  <span>進捗: {progress.toFixed(0)}%</span>
                  {executionTime > 0 && (
                    <span>実行時間: {executionTime.toFixed(2)}秒</span>
                  )}
                </div>

                {/* トークン数表示 */}
                {tokenCounts.total > 0 && (
                  <div className="grid grid-cols-3 gap-4 mt-4">
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{tokenCounts.input.toLocaleString()}</div>
                      <div className="text-xs text-blue-600 opacity-75">入力トークン</div>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{tokenCounts.output.toLocaleString()}</div>
                      <div className="text-xs text-green-600 opacity-75">出力トークン</div>
                    </div>
                    <div className="text-center p-3 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">{tokenCounts.total.toLocaleString()}</div>
                      <div className="text-xs text-purple-600 opacity-75">合計トークン</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 4. 処理結果 - 完了時に最重要 */}
          {result && (
            <div className="bg-white rounded-xl shadow-lg border p-6">
              <div className="flex items-center mb-4">
                <div className="bg-green-100 p-3 rounded-lg mr-4">
                  <CheckCircle className="text-green-600" size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">処理結果</h2>
                  <p className="text-gray-600">AIが生成した回答です</p>
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg p-6 border-l-4 border-blue-500">
                <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">{result}</div>
              </div>
            </div>
          )}
        </div>

        {/* 詳細情報・中間ステップ（折りたたみ） */}
        {intermediateSteps.length > 0 && (
          <div className="bg-white rounded-xl shadow border">
            <button
              onClick={() => setShowIntermediateSteps(!showIntermediateSteps)}
              className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center">
                <Database className="mr-3 text-gray-500" size={20} />
                <span className="font-medium text-gray-900">中間処理ステップを表示</span>
                <span className="ml-2 text-sm text-gray-500">({intermediateSteps.length}件)</span>
              </div>
              {showIntermediateSteps ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </button>
            
            {showIntermediateSteps && (
              <div className="border-t p-4">
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {intermediateSteps.map((step, index) => (
                    <div key={index} className="border-l-4 border-blue-300 pl-4 py-2 bg-blue-50 rounded-r">
                      <div className="font-medium text-sm text-blue-900">{step.step}</div>
                      <div className="text-xs text-blue-700 mt-1 font-mono">
                        {JSON.stringify(step.data, null, 2).substring(0, 150)}...
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 高度な設定（折りたたみ） */}
        <div className="bg-white rounded-xl shadow border">
          <button
            onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
            className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center">
              <Settings className="mr-3 text-gray-500" size={20} />
              <span className="font-medium text-gray-700">高度な設定</span>
            </div>
            {showAdvancedOptions ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
          
          {showAdvancedOptions && (
            <div className="border-t p-6 space-y-6">
              {/* デモモード */}
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">デモモード</h4>
                  <p className="text-sm text-gray-600">プレゼンテーション用に処理を遅延表示</p>
                </div>
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={demoMode}
                    onChange={(e) => setDemoMode(e.target.checked)}
                    className="sr-only"
                  />
                  <div className={`relative w-11 h-6 rounded-full transition-colors ${
                    demoMode ? 'bg-blue-600' : 'bg-gray-300'
                  }`}>
                    <div className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                      demoMode ? 'translate-x-5' : 'translate-x-0'
                    }`}></div>
                  </div>
                </label>
              </div>

              {/* ナレッジベース編集 */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h4 className="font-medium text-gray-900">ナレッジベース</h4>
                    <p className="text-sm text-gray-600">AIが参照する知識データを編集</p>
                  </div>
                  <button
                    onClick={() => setShowKnowledgeEditor(!showKnowledgeEditor)}
                    className="flex items-center text-blue-600 hover:text-blue-700 font-medium"
                  >
                    <FileText className="mr-2" size={16} />
                    {showKnowledgeEditor ? '閉じる' : '編集'}
                  </button>
                </div>
                
                {showKnowledgeEditor && (
                  <div className="space-y-4">
                    <textarea
                      value={knowledgeContent}
                      onChange={(e) => setKnowledgeContent(e.target.value)}
                      className="w-full h-48 p-3 border border-gray-300 rounded-lg resize-none font-mono text-sm"
                      placeholder="ナレッジベースの内容を入力..."
                    />
                    <button
                      onClick={saveKnowledge}
                      className="bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg font-medium"
                    >
                      保存
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* 実行ログ（折りたたみ） */}
        <div className="bg-white rounded-xl shadow border">
          <button
            onClick={() => {
              setShowLogs(!showLogs);
              if (!showLogs) fetchLogFiles();
            }}
            className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center">
              <Download className="mr-3 text-gray-500" size={20} />
              <span className="font-medium text-gray-700">実行ログ</span>
              <span className="ml-2 text-sm text-gray-500">({logFiles.length}件)</span>
            </div>
            {showLogs ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
          
          {showLogs && (
            <div className="border-t p-4">
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {logFiles.length > 0 ? (
                  logFiles.map((file, index) => (
                    <button
                      key={index}
                      onClick={() => downloadLog(file)}
                      className="w-full text-left text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 p-2 rounded transition-colors"
                    >
                      {file}
                    </button>
                  ))
                ) : (
                  <div className="text-gray-400 text-sm text-center py-4">
                    ログファイルがありません
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
