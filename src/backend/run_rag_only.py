"""
実装3：RAGのみ (run_rag_only.py)
目的: 現代的なRAGアーキテクチャの基本形を実装する。
"""

from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import ChatVertexAI


def main():
    print("=== 実装3: RAGのみ ===")

    # 1. ナレッジベース準備
    print("1. ナレッジベースを準備中...")
    loader = TextLoader("knowledge.txt", encoding="utf-8")
    documents = loader.load()

    # テキスト分割
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500,
                                                   chunk_overlap=50,
                                                   separators=["\n\n", "\n", "。", "、", " ", ""])
    splits = text_splitter.split_documents(documents)
    print(f"   ドキュメントを{len(splits)}個のチャンクに分割しました")

    # 2. ベクトルストア構築
    print("2. ベクトルストアを構築中...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(splits, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    print("   ベクトルストアの構築が完了しました")

    # 3. RAGチェーン構築
    print("3. RAGチェーンを構築中...")
    llm = ChatVertexAI(model_name="gemini-2.5-flash", temperature=0.1)

    prompt_template = ChatPromptTemplate.from_template("""以下のコンテキスト情報を使用して質問に答えてください。
コンテキストに答えが含まれていない場合は、「提供された情報では回答できません」と答えてください。

コンテキスト:
{context}

質問: {question}

回答:""")

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # LCELを使用してチェーンを構築
    rag_chain = ({
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    } | prompt_template | llm | StrOutputParser())
    print("   RAGチェーンの構築が完了しました")

    # 4. 質問実行
    question = "エラーコードE-404の対処法は？"
    print(f"\n質問: {question}")
    print("-" * 50)

    # RAGチェーンで実行
    response = rag_chain.invoke(question)

    print("回答:")
    print(response)
    print("-" * 50)


if __name__ == "__main__":
    main()
