"""
文档分块器模块
提供多种文档分块策略：fixed（固定长度）、semantic（语义分块）、sentence（句子分块）
"""
from abc import ABC, abstractmethod
from typing import List
from langchain.schema import Document
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    SentenceTransformersTokenTextSplitter,
    TextSplitter
)

from common import log_

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


class BaseChunker(ABC):
    """
    文档分块器抽象基类
    所有具体的分块器都需要继承此类并实现chunk方法
    """
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size if chunk_size is not None else DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else DEFAULT_CHUNK_OVERLAP
    
    @abstractmethod
    def chunk(self, documents: List[Document]) -> List[Document]:
        """
        将文档分割为小块
        Args:
            documents: 文档对象列表
            
        Returns:
            List[Document]: 分割后的文档块列表
        """
        pass


class FixedChunker(BaseChunker):
    """
    固定长度分块器
    使用RecursiveCharacterTextSplitter按字符数分割
    """
    
    def chunk(self, documents: List[Document]) -> List[Document]:
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            return text_splitter.split_documents(documents)
        except Exception as e:
            log_.error(f"固定长度分块失败: {str(e)}")
            raise


class SemanticChunker(BaseChunker):
    """
    语义分块器
    基于语义相似度分割文档
    """
    
    def chunk(self, documents: List[Document]) -> List[Document]:
        try:
            try:
                from langchain_experimental.text_splitter import SemanticChunker
                from langchain.embeddings import HuggingFaceEmbeddings
                
                embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
                
                text_splitter = SemanticChunker(
                    embeddings,
                    chunk_size=self.chunk_size
                )
                return text_splitter.split_documents(documents)
            except ImportError:
                log_.warning("未安装langchain_experimental，使用固定长度分块作为替代")
                return FixedChunker(self.chunk_size, self.chunk_overlap).chunk(documents)
        except Exception as e:
            log_.error(f"语义分块失败: {str(e)}，使用固定长度分块作为替代")
            return FixedChunker(self.chunk_size, self.chunk_overlap).chunk(documents)


class SentenceChunker(BaseChunker):
    """
    句子分块器
    基于句子边界分割文档
    """
    
    def chunk(self, documents: List[Document]) -> List[Document]:
        try:
            import nltk
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt')
            
            combined_text = ""
            for doc in documents:
                combined_text += doc.page_content + "\n\n"
            
            sentences = nltk.sent_tokenize(combined_text)
            
            chunks = []
            current_chunk = ""
            current_chars = 0
            
            for sentence in sentences:
                sentence_len = len(sentence)
                
                if current_chars + sentence_len > self.chunk_size and current_chunk:
                    chunks.append(Document(page_content=current_chunk.strip()))
                    overlap_text = ""
                    overlap_chars = 0
                    sentences_list = nltk.sent_tokenize(current_chunk)
                    for s in reversed(sentences_list):
                        if overlap_chars + len(s) <= self.chunk_overlap:
                            overlap_text = s + " " + overlap_text
                            overlap_chars += len(s) + 1
                        else:
                            break
                    current_chunk = overlap_text
                    current_chars = overlap_chars
                
                current_chunk += sentence + " "
                current_chars += sentence_len + 1
            
            if current_chunk.strip():
                chunks.append(Document(page_content=current_chunk.strip()))
            
            return chunks
        except Exception as e:
            log_.error(f"句子分块失败: {str(e)}，使用固定长度分块作为替代")
            return FixedChunker(self.chunk_size, self.chunk_overlap).chunk(documents)


def get_chunker(strategy: str = 'fixed', chunk_size: int = None, chunk_overlap: int = None) -> BaseChunker:
    """
    根据策略获取分块器实例
    
    Args:
        strategy: 分块策略 ('fixed', 'semantic', 'sentence')
        chunk_size: 块大小
        chunk_overlap: 块重叠大小
        
    Returns:
        BaseChunker: 分块器实例
    """
    strategy = strategy.lower() if strategy else 'fixed'
    
    chunkers = {
        'fixed': FixedChunker,
        'semantic': SemanticChunker,
        'sentence': SentenceChunker
    }
    
    chunker_class = chunkers.get(strategy, FixedChunker)
    return chunker_class(chunk_size, chunk_overlap)


def split_document_with_strategy(docs: List[Document], strategy: str = 'fixed', 
                                 chunk_size: int = None, chunk_overlap: int = None) -> List[Document]:
    """
    使用指定策略分割文档
    
    Args:
        docs: 文档对象列表
        strategy: 分块策略 ('fixed', 'semantic', 'sentence')
        chunk_size: 块大小
        chunk_overlap: 块重叠大小
        
    Returns:
        List[Document]: 分割后的文档块列表
    """
    chunker = get_chunker(strategy, chunk_size, chunk_overlap)
    return chunker.chunk(docs)
