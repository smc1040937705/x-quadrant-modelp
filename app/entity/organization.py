"""
组织管理相关实体模型
"""
from datetime import datetime
from app.dao.mapper import BaseEntity


class Organization(BaseEntity):
    """组织实体类，对应数据库 dodo_organizations 表"""
    
    _table_name = 'dodo_organizations'
    _primary_key = 'id'
    
    def __init__(self, id=None, name=None, description=None, created_by=None,
                 created_at=None, updated_at=None, **kwargs):
        self.id = id
        self.name = name
        self.description = description
        self.created_by = created_by
        self.created_at = created_at
        self.updated_at = updated_at
        for key, value in kwargs.items():
            setattr(self, key, value)


class OrganizationMember(BaseEntity):
    """组织成员实体类，对应数据库 dodo_organization_members 表"""
    
    _table_name = 'dodo_organization_members'
    _primary_key = 'id'
    
    def __init__(self, id=None, org_id=None, user_id=None, role=None,
                 joined_at=None, **kwargs):
        self.id = id
        self.org_id = org_id
        self.user_id = user_id
        self.role = role or 'member'  # 'owner', 'member'
        self.joined_at = joined_at
        for key, value in kwargs.items():
            setattr(self, key, value)


class OrganizationInvite(BaseEntity):
    """组织邀请实体类，对应数据库 dodo_organization_invites 表"""
    
    _table_name = 'dodo_organization_invites'
    _primary_key = 'id'
    
    def __init__(self, id=None, org_id=None, invite_code=None, created_by=None,
                 expires_at=None, used_count=None, created_at=None, **kwargs):
        self.id = id
        self.org_id = org_id
        self.invite_code = invite_code
        self.created_by = created_by
        self.expires_at = expires_at
        self.used_count = used_count if used_count is not None else 0
        self.created_at = created_at
        for key, value in kwargs.items():
            setattr(self, key, value)
