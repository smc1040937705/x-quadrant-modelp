"""
知识库数据传输对象 - 接收前端请求参数
"""
from typing import Optional
from common.error_codes import ParameterError


class KnowledgeBaseCreateDTO:
    """创建知识库请求参数"""
    
    VALID_STRATEGIES = {'fixed', 'semantic', 'sentence'}
    
    def __init__(self, name: str, description: Optional[str] = None,
                 chunking_strategy: Optional[str] = None,
                 chunk_size: Optional[int] = None,
                 chunk_overlap: Optional[int] = None):
        self.name = name
        self.description = description or ""
        self.chunking_strategy = chunking_strategy or 'fixed'
        self.chunk_size = chunk_size if chunk_size is not None else 1000
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else 200
    
    def validate(self):
        """参数校验"""
        if not self.name:
            raise ParameterError(msg="知识库名称不能为空")
        if len(self.name) > 100:
            raise ParameterError(msg="知识库名称不能超过100个字符")
        if self.chunking_strategy not in self.VALID_STRATEGIES:
            raise ParameterError(msg=f"分块策略不支持，可选值: {', '.join(self.VALID_STRATEGIES)}")
        if self.chunk_size < 100 or self.chunk_size > 10000:
            raise ParameterError(msg="分块大小必须在100-10000之间")
        if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
            raise ParameterError(msg="分块重叠必须大于等于0且小于分块大小")
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        """从请求数据创建"""
        chunk_size = data.get('chunk_size')
        chunk_overlap = data.get('chunk_overlap')
        if chunk_size is not None:
            chunk_size = int(chunk_size)
        if chunk_overlap is not None:
            chunk_overlap = int(chunk_overlap)
        return cls(
            name=data.get('name'),
            description=data.get('description'),
            chunking_strategy=data.get('chunking_strategy'),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )


class KnowledgeBaseUpdateDTO:
    """更新知识库请求参数"""
    
    VALID_STRATEGIES = {'fixed', 'semantic', 'sentence'}
    
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None,
                 chunking_strategy: Optional[str] = None,
                 chunk_size: Optional[int] = None,
                 chunk_overlap: Optional[int] = None):
        self.name = name
        self.description = description
        self.chunking_strategy = chunking_strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def validate(self):
        """参数校验"""
        if self.name and len(self.name) > 100:
            raise ParameterError(msg="知识库名称不能超过100个字符")
        if self.chunking_strategy is not None and self.chunking_strategy not in self.VALID_STRATEGIES:
            raise ParameterError(msg=f"分块策略不支持，可选值: {', '.join(self.VALID_STRATEGIES)}")
        if self.chunk_size is not None and (self.chunk_size < 100 or self.chunk_size > 10000):
            raise ParameterError(msg="分块大小必须在100-10000之间")
        if self.chunk_overlap is not None and self.chunk_size is not None:
            if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
                raise ParameterError(msg="分块重叠必须大于等于0且小于分块大小")
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        """从请求数据创建"""
        chunk_size = data.get('chunk_size')
        chunk_overlap = data.get('chunk_overlap')
        if chunk_size is not None:
            chunk_size = int(chunk_size)
        if chunk_overlap is not None:
            chunk_overlap = int(chunk_overlap)
        return cls(
            name=data.get('name'),
            description=data.get('description'),
            chunking_strategy=data.get('chunking_strategy'),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
