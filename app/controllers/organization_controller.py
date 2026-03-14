"""
组织管理控制器
"""
from flask import request, g
from app.services.organization_service import OrganizationService
from common import log_


class OrganizationController:
    """组织管理控制器"""
    
    def __init__(self):
        self.service = OrganizationService()
    
    def get_organizations(self):
        """获取用户所属的所有组织"""
        try:
            user_id = g.user_id
            orgs = self.service.get_user_organizations(user_id)
            return {"code": "SUCCESS", "message": "获取成功", "data": orgs}, 200
        except Exception as e:
            log_.error(f"获取组织列表失败: {e}")
            return {"code": "ERROR", "message": str(e), "data": None}, 500
    
    def get_organization(self, org_id):
        """获取组织详情"""
        try:
            user_id = g.user_id
            org = self.service.get_organization(org_id, user_id)
            if not org:
                return {"code": "NOT_FOUND", "message": "组织不存在", "data": None}, 404
            return {"code": "SUCCESS", "message": "获取成功", "data": org}, 200
        except Exception as e:
            log_.error(f"获取组织详情失败: {e}")
            return {"code": "ERROR", "message": str(e), "data": None}, 500
    
    def create_organization(self):
        """创建组织"""
        try:
            user_id = g.user_id
            data = request.get_json()
            
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            
            if not name:
                return {"code": "PARAM_ERROR", "message": "组织名称不能为空", "data": None}, 400
            
            result = self.service.create_organization(name, description, user_id)
            return {"code": "SUCCESS", "message": "组织创建成功", "data": result}, 200
        except Exception as e:
            log_.error(f"创建组织失败: {e}")
            return {"code": "ERROR", "message": str(e), "data": None}, 500
    
    def update_organization(self, org_id):
        """更新组织信息"""
        try:
            user_id = g.user_id
            data = request.get_json()
            
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            
            if not name:
                return {"code": "PARAM_ERROR", "message": "组织名称不能为空", "data": None}, 400
            
            self.service.update_organization(org_id, name, description, user_id)
            return {"code": "SUCCESS", "message": "组织信息更新成功", "data": None}, 200
        except PermissionError as e:
            return {"code": "FORBIDDEN", "message": str(e), "data": None}, 403
        except Exception as e:
            log_.error(f"更新组织失败: {e}")
            return {"code": "ERROR", "message": str(e), "data": None}, 500
    
    def dissolve_organization(self, org_id):
        """解散组织"""
        try:
            user_id = g.user_id
            self.service.dissolve_organization(org_id, user_id)
            return {"code": "SUCCESS", "message": "组织已解散", "data": None}, 200
        except PermissionError as e:
            return {"code": "FORBIDDEN", "message": str(e), "data": None}, 403
        except Exception as e:
            log_.error(f"解散组织失败: {e}")
            return {"code": "ERROR", "message": str(e), "data": None}, 500
    
    def get_members(self, org_id):
        """获取组织成员列表"""
        try:
            user_id = g.user_id
            members = self.service.get_members(org_id, user_id)
            return {"code": "SUCCESS", "message": "获取成功", "data": members}, 200
        except PermissionError as e:
            return {"code": "FORBIDDEN", "message": str(e), "data": None}, 403
        except Exception as e:
            log_.error(f"获取成员列表失败: {e}")
            return {"code": "ERROR", "message": str(e), "data": None}, 500
    
    def remove_member(self, org_id, member_user_id):
        """移除成员"""
        try:
            user_id = g.user_id
            self.service.remove_member(org_id, member_user_id, user_id)
            return {"code": "SUCCESS", "message": "成员已移除", "data": None}, 200
        except PermissionError as e:
            return {"code": "FORBIDDEN", "message": str(e), "data": None}, 403
        except ValueError as e:
            return {"code": "PARAM_ERROR", "message": str(e), "data": None}, 400
        except Exception as e:
            log_.error(f"移除成员失败: {e}")
            return {"code": "ERROR", "message": str(e), "data": None}, 500
    
    def leave_organization(self, org_id):
        """退出组织"""
        try:
            user_id = g.user_id
            self.service.leave_organization(org_id, user_id)
            return {"code": "SUCCESS", "message": "已退出组织", "data": None}, 200
        except ValueError as e:
            return {"code": "PARAM_ERROR", "message": str(e), "data": None}, 400
        except Exception as e:
            log_.error(f"退出组织失败: {e}")
            return {"code": "ERROR", "message": str(e), "data": None}, 500
    
    def set_member_role(self, org_id, member_user_id):
        """设置成员角色"""
        try:
            user_id = g.user_id
            data = request.get_json()
            role = data.get('role')
            
            if role not in ('admin', 'member'):
                return {"code": "PARAM_ERROR", "message": "无效的角色", "data": None}, 400
            
            self.service.set_member_role(org_id, member_user_id, role, user_id)
            return {"code": "SUCCESS", "message": "角色设置成功", "data": None}, 200
        except PermissionError as e:
            return {"code": "FORBIDDEN", "message": str(e), "data": None}, 403
        except ValueError as e:
            return {"code": "PARAM_ERROR", "message": str(e), "data": None}, 400
        except Exception as e:
            log_.error(f"设置角色失败: {e}")
            return {"code": "ERROR", "message": str(e), "data": None}, 500
    
    def create_invite(self, org_id):
        """创建邀请链接"""
        try:
            user_id = g.user_id
            data = request.get_json() or {}
            expires_days = data.get('expires_days', 7)
            
            result = self.service.create_invite(org_id, user_id, expires_days)
            return {"code": "SUCCESS", "message": "邀请链接创建成功", "data": result}, 200
        except PermissionError as e:
            return {"code": "FORBIDDEN", "message": str(e), "data": None}, 403
        except Exception as e:
            log_.error(f"创建邀请失败: {e}")
            return {"code": "ERROR", "message": str(e), "data": None}, 500
    
    def get_invite_info(self, invite_code):
        """获取邀请信息（无需登录）"""
        try:
            info = self.service.get_invite_info(invite_code)
            if not info:
                return {"code": "NOT_FOUND", "message": "邀请链接无效", "data": None}, 404
            return {"code": "SUCCESS", "message": "获取成功", "data": info}, 200
        except Exception as e:
            log_.error(f"获取邀请信息失败: {e}")
            return {"code": "ERROR", "message": str(e), "data": None}, 500
    
    def accept_invite(self, invite_code):
        """接受邀请加入组织"""
        try:
            user_id = g.user_id
            result = self.service.accept_invite(invite_code, user_id)
            return {"code": "SUCCESS", "message": "成功加入组织", "data": result}, 200
        except ValueError as e:
            return {"code": "PARAM_ERROR", "message": str(e), "data": None}, 400
        except Exception as e:
            log_.error(f"接受邀请失败: {e}")
            return {"code": "ERROR", "message": str(e), "data": None}, 500


# 创建控制器实例
org_controller = OrganizationController()
