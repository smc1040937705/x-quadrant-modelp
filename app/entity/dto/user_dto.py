"""
用户数据传输对象 - 接收前端请求参数
"""
from typing import Optional
from common.error_codes import ParameterError


class UserUpdateDTO:
    """用户更新请求参数"""
    
    def __init__(self, email: Optional[str] = None, phone: Optional[str] = None):
        self.email = email
        self.phone = phone
    
    def validate(self):
        """参数校验"""
        if self.email and '@' not in self.email:
            raise ParameterError(msg="邮箱格式不正确")
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        """从请求数据创建"""
        return cls(
            email=data.get('email'),
            phone=data.get('phone')
        )
