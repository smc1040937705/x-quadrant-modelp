"""
组织管理数据访问层
"""
from app.dao.base_dao import BaseDAO
from app.entity.organization import Organization, OrganizationMember, OrganizationInvite
from common import log_
from common.db_utils import get_db_connection


class OrganizationDAO(BaseDAO):
    """组织数据访问对象"""
    
    def insert(self, org):
        """插入组织"""
        sql = """
            INSERT INTO dodo_organizations (name, description, created_by, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """
        return self.execute_insert_returning(sql, (org.name, org.description, org.created_by, org.created_at, org.updated_at))
    
    def update(self, org):
        """更新组织"""
        sql = "UPDATE dodo_organizations SET name = %s, description = %s, updated_at = %s WHERE id = %s"
        return self.execute_update(sql, (org.name, org.description, org.updated_at, org.id))
    
    def delete(self, org_id):
        """删除组织"""
        sql = "DELETE FROM dodo_organizations WHERE id = %s"
        return self.execute_update(sql, (org_id,))
    
    def find_by_user(self, user_id):
        """查询用户所属的所有组织"""
        sql = """
            SELECT o.*, om.role as user_role, 
                   (SELECT COUNT(*) FROM dodo_organization_members WHERE org_id = o.id) as member_count
            FROM dodo_organizations o
            JOIN dodo_organization_members om ON o.id = om.org_id
            WHERE om.user_id = %s
            ORDER BY o.created_at DESC
        """
        return self.execute_query(sql, (user_id,))
    
    def find_by_id_with_role(self, org_id, user_id):
        """查询组织详情（包含用户角色）"""
        sql = """
            SELECT o.*, om.role as user_role
            FROM dodo_organizations o
            LEFT JOIN dodo_organization_members om ON o.id = om.org_id AND om.user_id = %s
            WHERE o.id = %s
        """
        results = self.execute_query(sql, (user_id, org_id))
        return results[0] if results else None


class OrganizationMemberDAO(BaseDAO):
    """组织成员数据访问对象"""
    
    def insert(self, member):
        """插入组织成员"""
        sql = """
            INSERT INTO dodo_organization_members (org_id, user_id, role, joined_at)
            VALUES (%s, %s, %s, %s) RETURNING id
        """
        return self.execute_insert_returning(sql, (member.org_id, member.user_id, member.role, member.joined_at))
    
    def find_by_org(self, org_id):
        """查询组织的所有成员"""
        sql = """
            SELECT om.*, u.nickname, u.avatar, u.email
            FROM dodo_organization_members om
            JOIN dodo_users u ON om.user_id = u.id
            WHERE om.org_id = %s
            ORDER BY 
                CASE om.role 
                    WHEN 'owner' THEN 1 
                    WHEN 'admin' THEN 2 
                    ELSE 3 
                END,
                om.joined_at ASC
        """
        return self.execute_query(sql, (org_id,))
    
    def find_by_org_and_user(self, org_id, user_id):
        """查询用户在组织中的成员记录"""
        sql = """
            SELECT * FROM dodo_organization_members
            WHERE org_id = %s AND user_id = %s
        """
        results = self.execute_query(sql, (org_id, user_id))
        return results[0] if results else None
    
    def find_orgs_by_user(self, user_id):
        """查询用户所属的所有组织（包含角色信息）"""
        sql = """
            SELECT om.org_id, om.role, o.name, o.description, o.created_at
            FROM dodo_organization_members om
            JOIN dodo_organizations o ON om.org_id = o.id
            WHERE om.user_id = %s
            ORDER BY om.joined_at DESC
        """
        return self.execute_query(sql, (user_id,))
    
    def count_by_org(self, org_id):
        """统计组织成员数量"""
        sql = "SELECT COUNT(*) as count FROM dodo_organization_members WHERE org_id = %s"
        result = self.execute_query(sql, (org_id,))
        return result[0]['count'] if result else 0
    
    def delete_by_org_and_user(self, org_id, user_id):
        """删除组织成员"""
        sql = "DELETE FROM dodo_organization_members WHERE org_id = %s AND user_id = %s"
        return self.execute_update(sql, (org_id, user_id))
    
    def update_role(self, org_id, user_id, role):
        """更新成员角色"""
        sql = "UPDATE dodo_organization_members SET role = %s WHERE org_id = %s AND user_id = %s"
        return self.execute_update(sql, (role, org_id, user_id))


class OrganizationInviteDAO(BaseDAO):
    """组织邀请数据访问对象"""
    
    def insert(self, invite):
        """插入邀请"""
        sql = """
            INSERT INTO dodo_organization_invites (org_id, invite_code, created_by, expires_at, used_count, created_at)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """
        return self.execute_insert_returning(sql, (invite.org_id, invite.invite_code, invite.created_by, invite.expires_at, invite.used_count, invite.created_at))
    
    def find_by_code(self, invite_code):
        """根据邀请码查询邀请信息"""
        sql = """
            SELECT i.*, o.name as org_name, u.nickname as inviter_name
            FROM dodo_organization_invites i
            JOIN dodo_organizations o ON i.org_id = o.id
            JOIN dodo_users u ON i.created_by = u.id
            WHERE i.invite_code = %s
        """
        results = self.execute_query(sql, (invite_code,))
        return results[0] if results else None
    
    def increment_used_count(self, invite_id):
        """增加邀请使用次数"""
        sql = "UPDATE dodo_organization_invites SET used_count = used_count + 1 WHERE id = %s"
        return self.execute_update(sql, (invite_id,))
