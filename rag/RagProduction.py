from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chroma import Chroma


"""
Production-level RAG system for identifying files in codebase
"""

class RAGPipeline:
    def __init__(self):
        self.embeddings = OllamaEmbeddings("embeddinggemma")
        self.vectorstore = Chroma.collection()
