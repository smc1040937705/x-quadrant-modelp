"""
DTO (Data Transfer Object) - 数据传输对象
用于接收Controller层的请求参数，并进行校验
"""
from .user_dto import UserUpdateDTO
from .bot_dto import BotCreateDTO, BotUpdateDTO
from .chat_dto import ChatMessageDTO
from .knowledge_dto import KnowledgeBaseCreateDTO, KnowledgeBaseUpdateDTO

__all__ = [
    'UserUpdateDTO',
    'BotCreateDTO',
    'BotUpdateDTO',
    'ChatMessageDTO',
    'KnowledgeBaseCreateDTO',
    'KnowledgeBaseUpdateDTO',
]
