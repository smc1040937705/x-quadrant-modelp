"""
组织管理服务层
"""
import secrets
from datetime import datetime, timedelta, timezone
from app.dao.organization_dao import OrganizationDAO, OrganizationMemberDAO, OrganizationInviteDAO
from app.entity.organization import Organization, OrganizationMember, OrganizationInvite
from common import log_


class OrganizationService:
    """组织管理服务"""
    
    def __init__(self):
        self.org_dao = OrganizationDAO()
        self.member_dao = OrganizationMemberDAO()
        self.invite_dao = OrganizationInviteDAO()
    
    def get_user_organizations(self, user_id):
        """获取用户所属的所有组织"""
        try:
            orgs = self.org_dao.find_by_user(user_id)
            return [self._format_org(org) for org in orgs]
        except Exception as e:
            log_.error(f"获取用户组织列表失败: {e}")
            raise
    
    def get_organization(self, org_id, user_id):
        """获取组织详情"""
        try:
            org = self.org_dao.find_by_id_with_role(org_id, user_id)
            if not org:
                return None
            return self._format_org(org)
        except Exception as e:
            log_.error(f"获取组织详情失败: {e}")
            raise
    
    def create_organization(self, name, description, user_id):
        """创建组织"""
        try:
            # 创建组织
            org = Organization(
                name=name,
                description=description,
                created_by=user_id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            org_id = self.org_dao.insert(org)
            
            # 添加创建者为所有者
            member = OrganizationMember(
                org_id=org_id,
                user_id=user_id,
                role='owner',
                joined_at=datetime.now()
            )
            self.member_dao.insert(member)
            
            return {'id': org_id, 'name': name}
        except Exception as e:
            log_.error(f"创建组织失败: {e}")
            raise
    
    def update_organization(self, org_id, name, description, user_id):
        """更新组织信息"""
        try:
            # 检查权限
            if not self._check_owner_permission(org_id, user_id):
                raise PermissionError("无权编辑此组织")
            
            org = Organization(
                id=org_id,
                name=name,
                description=description,
                updated_at=datetime.now()
            )
            self.org_dao.update(org)
            return True
        except Exception as e:
            log_.error(f"更新组织失败: {e}")
            raise
    
    def dissolve_organization(self, org_id, user_id):
        """解散组织"""
        try:
            # 检查是否为所有者
            member = self.member_dao.find_by_org_and_user(org_id, user_id)
            if not member or member.get('role') != 'owner':
                raise PermissionError("只有组织创建者才能解散组织")
            
            self.org_dao.delete(org_id)
            return True
        except Exception as e:
            log_.error(f"解散组织失败: {e}")
            raise
    
    def get_members(self, org_id, user_id):
        """获取组织成员列表"""
        try:
            # 检查是否为成员
            if not self._check_member(org_id, user_id):
                raise PermissionError("您不是此组织的成员")
            
            members = self.member_dao.find_by_org(org_id)
            return [self._format_member(m) for m in members]
        except Exception as e:
            log_.error(f"获取组织成员失败: {e}")
            raise
    
    def remove_member(self, org_id, target_user_id, user_id):
        """移除成员"""
        try:
            # 检查权限
            if not self._check_owner_permission(org_id, user_id):
                raise PermissionError("无权移除成员")
            
            # 不能移除所有者
            target_member = self.member_dao.find_by_org_and_user(org_id, target_user_id)
            if target_member and target_member.get('role') == 'owner':
                raise ValueError("无法移除组织创建者")
            
            self.member_dao.delete_by_org_and_user(org_id, target_user_id)
            return True
        except Exception as e:
            log_.error(f"移除成员失败: {e}")
            raise
    
    def leave_organization(self, org_id, user_id):
        """退出组织"""
        try:
            member = self.member_dao.find_by_org_and_user(org_id, user_id)
            if not member:
                raise ValueError("您不是此组织的成员")
            
            if member.get('role') == 'owner':
                raise ValueError("组织创建者无法退出，请先转让或解散组织")
            
            self.member_dao.delete_by_org_and_user(org_id, user_id)
            return True
        except Exception as e:
            log_.error(f"退出组织失败: {e}")
            raise
    
    def set_member_role(self, org_id, target_user_id, role, user_id):
        """设置成员角色"""
        try:
            # 检查权限（只有所有者可以设置管理员）
            member = self.member_dao.find_by_org_and_user(org_id, user_id)
            if not member or member.get('role') != 'owner':
                raise PermissionError("只有组织创建者才能设置管理员")
            
            # 不能修改所有者角色
            target_member = self.member_dao.find_by_org_and_user(org_id, target_user_id)
            if target_member and target_member.get('role') == 'owner':
                raise ValueError("无法修改组织创建者的角色")
            
            self.member_dao.update_role(org_id, target_user_id, role)
            return True
        except Exception as e:
            log_.error(f"设置成员角色失败: {e}")
            raise
    
    def create_invite(self, org_id, user_id, expires_days=7):
        """创建邀请链接"""
        try:
            # 检查是否为成员（所有成员都可以邀请）
            if not self._check_member(org_id, user_id):
                raise PermissionError("您不是此组织的成员")
            
            invite_code = secrets.token_urlsafe(16)
            expires_at = None
            if expires_days > 0:
                expires_at = datetime.now() + timedelta(days=expires_days)
            
            invite = OrganizationInvite(
                org_id=org_id,
                invite_code=invite_code,
                created_by=user_id,
                expires_at=expires_at,
                created_at=datetime.now()
            )
            self.invite_dao.insert(invite)
            
            log_.info(f"创建邀请链接成功: code={invite_code}, org_id={org_id}")
            return {'invite_code': invite_code, 'expires_at': expires_at}
        except Exception as e:
            log_.error(f"创建邀请链接失败: {e}")
            raise
    
    def get_invite_info(self, invite_code):
        """获取邀请信息"""
        try:
            log_.debug(f"查询邀请码: {invite_code}")
            invite = self.invite_dao.find_by_code(invite_code)
            log_.debug(f"查询结果: {invite}")
            if not invite:
                return None
            
            # 检查是否过期
            expires_at = invite.get('expires_at')
            if expires_at:
                # 处理时区问题：如果数据库返回的是offset-aware，转换为offset-naive
                if expires_at.tzinfo is not None:
                    expires_at = expires_at.replace(tzinfo=None)
                if expires_at < datetime.now():
                    return {'expired': True, 'org_name': invite.get('org_name')}
            
            return {
                'org_id': invite['org_id'],
                'org_name': invite.get('org_name'),
                'inviter_name': invite.get('inviter_name'),
                'expired': False
            }
        except Exception as e:
            log_.error(f"获取邀请信息失败: {e}")
            raise
    
    def accept_invite(self, invite_code, user_id):
        """接受邀请加入组织"""
        try:
            invite = self.invite_dao.find_by_code(invite_code)
            if not invite:
                raise ValueError("邀请链接无效")
            
            # 检查是否过期
            expires_at = invite.get('expires_at')
            if expires_at:
                if expires_at.tzinfo is not None:
                    expires_at = expires_at.replace(tzinfo=None)
                if expires_at < datetime.now():
                    raise ValueError("邀请链接已过期")
            
            org_id = invite['org_id']
            
            # 检查是否已是成员
            existing = self.member_dao.find_by_org_and_user(org_id, user_id)
            if existing:
                raise ValueError("您已是该组织成员")
            
            # 添加成员
            member = OrganizationMember(
                org_id=org_id,
                user_id=user_id,
                role='member',
                joined_at=datetime.now()
            )
            self.member_dao.insert(member)
            
            # 更新邀请使用次数
            self.invite_dao.increment_used_count(invite['id'])
            
            return {'org_id': org_id, 'org_name': invite.get('org_name')}
        except Exception as e:
            log_.error(f"接受邀请失败: {e}")
            raise
    
    def _check_member(self, org_id, user_id):
        """检查是否为组织成员"""
        member = self.member_dao.find_by_org_and_user(org_id, user_id)
        return member is not None
    
    def _check_owner_permission(self, org_id, user_id):
        """检查是否为组织创建者"""
        member = self.member_dao.find_by_org_and_user(org_id, user_id)
        return member and member.get('role') == 'owner'
    
    def _format_org(self, org):
        """格式化组织数据"""
        return {
            'id': org.get('id'),
            'name': org.get('name'),
            'description': org.get('description'),
            'created_by': org.get('created_by'),
            'created_at': org.get('created_at').isoformat() if org.get('created_at') else None,
            'role': org.get('user_role'),
            'member_count': org.get('member_count', 0)
        }
    
    def _format_member(self, member):
        """格式化成员数据"""
        return {
            'id': member.get('id'),
            'user_id': member.get('user_id'),
            'nickname': member.get('nickname'),
            'avatar': member.get('avatar'),
            'email': member.get('email'),
            'role': member.get('role'),
            'joined_at': member.get('joined_at').isoformat() if member.get('joined_at') else None
        }
