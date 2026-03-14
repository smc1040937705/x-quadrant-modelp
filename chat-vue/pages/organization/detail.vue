<template>
  <app-layout :title="organization.name || '组织详情'">
    <view class="org-detail-container">
      <!-- 加载状态 -->
      <view v-if="loading" class="loading">
        <text>加载中...</text>
      </view>
      
      <template v-else>
        <!-- 组织基本信息 -->
        <view class="info-section">
          <view class="section-header">
            <text class="section-title">组织信息</text>
            <button v-if="isOwner" class="edit-btn" @tap="showEditOrgDialog">编辑</button>
          </view>
          
          <view class="info-card">
            <view class="info-item">
              <text class="info-label">组织名称</text>
              <text class="info-value">{{ organization.name }}</text>
            </view>
            <view class="info-item">
              <text class="info-label">组织描述</text>
              <text class="info-value">{{ organization.description || '暂无描述' }}</text>
            </view>
            <view class="info-item">
              <text class="info-label">创建时间</text>
              <text class="info-value">{{ formatDate(organization.created_at) }}</text>
            </view>
            <view class="info-item">
              <text class="info-label">我的角色</text>
              <view class="role-tag" :class="getRoleClass(myRole)">
                {{ getRoleText(myRole) }}
              </view>
            </view>
          </view>
        </view>
        
        <!-- 成员列表 -->
        <view class="members-section">
          <view class="section-header">
            <text class="section-title">成员列表 ({{ members.length }})</text>
            <button class="invite-btn" @tap="showInviteDialog">邀请成员</button>
          </view>
          
          <view class="members-list">
            <view v-for="member in members" :key="member.id" class="member-item">
              <view class="member-avatar">
                <text class="avatar-text">{{ getAvatarText(member.nickname || member.email) }}</text>
              </view>
              <view class="member-info">
                <text class="member-name">{{ member.nickname || member.email }}</text>
                <text class="member-email" v-if="member.nickname">{{ member.email }}</text>
              </view>
              <view class="member-role" :class="getRoleClass(member.role)">
                {{ getRoleText(member.role) }}
              </view>
              
              <!-- 创建者操作按钮：移除成员 -->
              <view v-if="isOwner && member.user_id !== userInfo.id" class="member-actions">
                <button 
                  class="action-btn remove-btn" 
                  @tap.stop="confirmRemoveMember(member)"
                >
                  移除
                </button>
              </view>
              
              <!-- 普通成员退出按钮 -->
              <view v-if="!isOwner && member.user_id === userInfo.id" class="member-actions">
                <button class="action-btn leave-btn" @tap.stop="confirmLeaveOrg">
                  退出组织
                </button>
              </view>
            </view>
          </view>
        </view>
        
        <!-- 管理员危险操作区 -->
        <view v-if="isOwner" class="danger-section">
          <view class="section-title danger-title">危险操作</view>
          <button class="danger-btn" @tap="confirmDissolveOrg">解散组织</button>
        </view>
      </template>
      
      <!-- 编辑组织弹窗 -->
      <view v-if="showEditOrg" class="dialog" @tap="cancelEditOrg">
        <view class="dialog-content" @tap.stop>
          <text class="dialog-title">编辑组织信息</text>
          
          <view class="form-item">
            <text class="form-label">组织名称 <text class="required">*</text></text>
            <input 
              type="text" 
              v-model="editForm.name"
              placeholder="输入组织名称" 
              maxlength="50"
              class="form-input"
            />
          </view>
          
          <view class="form-item">
            <text class="form-label">组织描述</text>
            <textarea
              v-model="editForm.description"
              placeholder="输入组织描述(选填)" 
              class="form-textarea"
              maxlength="200"
            ></textarea>
          </view>
          
          <view class="dialog-buttons">
            <button class="cancel-btn" @tap="cancelEditOrg">取消</button>
            <button class="confirm-btn" @tap="confirmEditOrg" :disabled="!editForm.name.trim()">保存</button>
          </view>
        </view>
      </view>
      
      <!-- 邀请成员弹窗 -->
      <view v-if="showInvite" class="dialog" @tap="cancelInvite">
        <view class="dialog-content" @tap.stop>
          <text class="dialog-title">邀请成员</text>
          
          <view class="form-item">
            <text class="form-label">邀请链接有效期</text>
            <view class="validity-options">
              <view 
                v-for="option in validityOptions" 
                :key="option.value"
                :class="['validity-option', { active: inviteValidity === option.value }]"
                @tap="inviteValidity = option.value"
              >
                {{ option.label }}
              </view>
            </view>
          </view>
          
          <view v-if="inviteLink" class="invite-link-section">
            <text class="form-label">邀请链接</text>
            <view class="invite-link-box">
              <text class="invite-link-text">{{ inviteLink }}</text>
              <button class="copy-btn" :class="{ 'copied': copied }" @tap="copyInviteLink">
                {{ copied ? '已复制' : '复制' }}
              </button>
            </view>
          </view>
          
          <view class="dialog-buttons">
            <button class="cancel-btn" @tap="cancelInvite">关闭</button>
            <button v-if="!inviteLink" class="confirm-btn" @tap="generateInviteLink" :disabled="generatingLink">
              {{ generatingLink ? '生成中...' : '生成链接' }}
            </button>
          </view>
        </view>
      </view>
      
      <!-- 登录弹窗 -->
      <login-dialog
        v-model:visible="loginVisible"
        @login-success="onLoginSuccess"
        @update:visible="onLoginVisibleChange"
      />
    </view>
  </app-layout>
</template>

<script>
import api from '../../utils/api.js';
import AppLayout from '../../components/layout/AppLayout.vue';
import LoginDialog from '../../components/user/LoginDialog.vue';
import { getCurrentUser } from '../../utils/auth.js';

export default {
  components: {
    AppLayout,
    LoginDialog
  },
  data() {
    return {
      orgId: null,
      organization: {},
      members: [],
      myRole: 'member',
      loading: false,
      showEditOrg: false,
      editForm: {
        name: '',
        description: ''
      },
      showInvite: false,
      inviteValidity: 7,
      inviteLink: '',
      copied: false,
      generatingLink: false,
      validityOptions: [
        { label: '1天', value: 1 },
        { label: '7天', value: 7 },
        { label: '永久', value: -1 }
      ],
      loginVisible: false,
      userInfo: null,
      isLoggedIn: false
    };
  },
  computed: {
    isOwner() {
      return this.myRole === 'owner';
    }
  },
  onLoad(options) {
    this.userInfo = getCurrentUser();
    this.isLoggedIn = !!this.userInfo;
    
    if (options.id) {
      this.orgId = options.id;
      this.fetchOrganizationDetail();
    }
    
    uni.$on('userInfoUpdated', this.handleUserInfoUpdated);
  },
  onUnload() {
    uni.$off('userInfoUpdated', this.handleUserInfoUpdated);
  },
  methods: {
    handleUserInfoUpdated(userInfo) {
      this.userInfo = userInfo;
      this.isLoggedIn = !!userInfo;
    },
    
    async fetchOrganizationDetail() {
      this.loading = true;
      try {
        const result = await api.get(`/org/organizations/${this.orgId}`);
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.organization = result.data.organization || {};
          this.members = result.data.members || [];
          this.myRole = result.data.my_role || 'member';
        } else {
          api.showError(result?.message || '获取组织信息失败');
        }
      } catch (error) {
        console.error('获取组织详情失败:', error);
        api.showError('获取组织信息失败');
      } finally {
        this.loading = false;
      }
    },
    
    showEditOrgDialog() {
      this.editForm = {
        name: this.organization.name || '',
        description: this.organization.description || ''
      };
      this.showEditOrg = true;
    },
    
    cancelEditOrg() {
      this.showEditOrg = false;
    },
    
    async confirmEditOrg() {
      if (!this.editForm.name.trim()) {
        api.showError('请输入组织名称');
        return;
      }
      
      try {
        const result = await api.put(`/org/organizations/${this.orgId}`, {
          name: this.editForm.name.trim(),
          description: this.editForm.description.trim()
        });
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('组织信息已更新');
          this.showEditOrg = false;
          this.organization.name = this.editForm.name.trim();
          this.organization.description = this.editForm.description.trim();
        } else {
          api.showError(result?.message || '更新失败');
        }
      } catch (error) {
        console.error('更新组织信息失败:', error);
        api.showError('更新失败');
      }
    },
    
    showInviteDialog() {
      this.inviteLink = '';
      this.copied = false;
      this.inviteValidity = 7;
      this.showInvite = true;
    },
    
    cancelInvite() {
      this.showInvite = false;
      this.inviteLink = '';
      this.copied = false;
    },
    
    async generateInviteLink() {
      this.generatingLink = true;
      try {
        const result = await api.post(`/org/organizations/${this.orgId}/invite`, {
          validity_days: this.inviteValidity
        });
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          const inviteCode = result.data.invite_code;
          // 生成完整的邀请链接
          const baseUrl = window.location.origin || '';
          this.inviteLink = `${baseUrl}/pages/organization/join?code=${inviteCode}`;
        } else {
          api.showError(result?.message || '生成邀请链接失败');
        }
      } catch (error) {
        console.error('生成邀请链接失败:', error);
        api.showError('生成邀请链接失败');
      } finally {
        this.generatingLink = false;
      }
    },
    
    copyInviteLink() {
      if (!this.inviteLink) {
        api.showError('请先生成邀请链接');
        return;
      }
      
      // #ifdef H5
      navigator.clipboard.writeText(this.inviteLink).then(() => {
        this.onCopySuccess();
      }).catch(() => {
        this.fallbackCopy();
      });
      // #endif
      
      // #ifndef H5
      uni.setClipboardData({
        data: this.inviteLink,
        success: () => {
          this.onCopySuccess();
        },
        fail: () => {
          api.showError('复制失败');
        }
      });
      // #endif
    },
    
    onCopySuccess() {
      this.copied = true;
      api.showSuccess('链接已复制');
      setTimeout(() => {
        this.copied = false;
      }, 2000);
    },
    
    fallbackCopy() {
      const input = document.createElement('input');
      input.value = this.inviteLink;
      document.body.appendChild(input);
      input.select();
      try {
        document.execCommand('copy');
        this.onCopySuccess();
      } catch (e) {
        api.showError('复制失败，请手动复制');
      }
      document.body.removeChild(input);
    },
    
    confirmRemoveMember(member) {
      uni.showModal({
        title: '确认移除',
        content: `确定将 ${member.nickname || member.email} 移出组织吗？`,
        success: async (res) => {
          if (res.confirm) {
            await this.removeMember(member.user_id);
          }
        }
      });
    },
    
    async removeMember(userId) {
      try {
        const result = await api.delete(`/org/organizations/${this.orgId}/members/${userId}`);
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('成员已移除');
          this.fetchOrganizationDetail();
        } else {
          api.showError(result?.message || '移除失败');
        }
      } catch (error) {
        console.error('移除成员失败:', error);
        api.showError('移除失败');
      }
    },
    
    confirmLeaveOrg() {
      uni.showModal({
        title: '确认退出',
        content: '确定要退出该组织吗？退出后将无法访问组织的共享资源。',
        success: async (res) => {
          if (res.confirm) {
            await this.leaveOrganization();
          }
        }
      });
    },
    
    async leaveOrganization() {
      try {
        const result = await api.post(`/org/organizations/${this.orgId}/leave`);
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('已退出组织');
          setTimeout(() => {
            uni.navigateBack();
          }, 1000);
        } else {
          api.showError(result?.message || '退出失败');
        }
      } catch (error) {
        console.error('退出组织失败:', error);
        api.showError('退出失败');
      }
    },
    
    confirmDissolveOrg() {
      uni.showModal({
        title: '⚠️ 危险操作',
        content: '解散组织将删除所有组织数据，包括成员关系和组织知识库。此操作不可恢复！确定要解散吗？',
        confirmColor: '#ff4d4f',
        success: async (res) => {
          if (res.confirm) {
            await this.dissolveOrganization();
          }
        }
      });
    },
    
    async dissolveOrganization() {
      try {
        const result = await api.delete(`/org/organizations/${this.orgId}`);
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('组织已解散');
          setTimeout(() => {
            uni.navigateBack();
          }, 1000);
        } else {
          api.showError(result?.message || '解散失败');
        }
      } catch (error) {
        console.error('解散组织失败:', error);
        api.showError('解散失败');
      }
    },
    
    formatDate(dateStr) {
      if (!dateStr) return '-';
      const date = new Date(dateStr);
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    },
    
    getAvatarText(name) {
      if (!name) return '?';
      return name.charAt(0).toUpperCase();
    },
    
    getRoleText(role) {
      const roleMap = {
        'owner': '创建者',
        'member': '成员'
      };
      return roleMap[role] || '成员';
    },
    
    getRoleClass(role) {
      return `role-${role || 'member'}`;
    },
    
    onLoginSuccess(userInfo) {
      this.userInfo = typeof userInfo === 'string' ? JSON.parse(userInfo) : userInfo;
      this.isLoggedIn = !!this.userInfo;
      this.fetchOrganizationDetail();
    },
    
    onLoginVisibleChange(visible) {
      this.loginVisible = visible;
    }
  }
};
</script>

<style>
.org-detail-container {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px;
  color: #666;
}

/* 信息区块 */
.info-section, .members-section {
  background-color: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.edit-btn, .invite-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  border: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1.2;
}

.info-card {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 14px;
  color: #666;
}

.info-value {
  font-size: 14px;
  color: #333;
}

.role-tag {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 12px;
}

.role-owner {
  background-color: #fff3e0;
  color: #f57c00;
}

.role-admin {
  background-color: #e3f2fd;
  color: #1976d2;
}

.role-member {
  background-color: #f5f5f5;
  color: #666;
}

/* 成员列表 */
.members-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.member-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background-color: #f9f9f9;
  border-radius: 8px;
  gap: 12px;
}

.member-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-text {
  color: white;
  font-size: 16px;
  font-weight: 600;
}

.member-info {
  flex: 1;
  min-width: 0;
}

.member-name {
  font-size: 14px;
  color: #333;
  font-weight: 500;
  display: block;
}

.member-email {
  font-size: 12px;
  color: #999;
  display: block;
  margin-top: 2px;
}

.member-role {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 12px;
  flex-shrink: 0;
}

.member-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.action-btn {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 4px;
  border: none;
}

.promote-btn {
  background-color: #e3f2fd;
  color: #1976d2;
}

.remove-btn, .leave-btn {
  background-color: #ffebee;
  color: #d32f2f;
}

/* 危险操作区 */
.danger-section {
  background-color: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.danger-title {
  color: #d32f2f;
  margin-bottom: 16px;
}

.danger-btn {
  background-color: #ffebee;
  color: #d32f2f;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  border: 1px solid #ffcdd2;
  width: 100%;
}

/* 弹窗样式 */
.dialog {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog-content {
  background-color: white;
  border-radius: 12px;
  padding: 24px;
  width: 90%;
  max-width: 450px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
}

.dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
  text-align: center;
  display: block;
}

.form-item {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
}

.required {
  color: #ff4d4f;
}

.form-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  min-height: 80px;
  box-sizing: border-box;
  resize: vertical;
}

.validity-options {
  display: flex;
  gap: 10px;
}

.validity-option {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.validity-option.active {
  border-color: var(--primary-color, #007AFF);
  background-color: rgba(0, 122, 255, 0.1);
  color: var(--primary-color, #007AFF);
}

.invite-link-section {
  margin-top: 16px;
}

.invite-link-box {
  display: flex;
  align-items: center;
  gap: 10px;
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 6px;
}

.invite-link-text {
  flex: 1;
  font-size: 12px;
  color: #666;
  word-break: break-all;
}

.copy-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  border: none;
  flex-shrink: 0;
  transition: all 0.3s;
}

.copy-btn.copied {
  background-color: #52c41a;
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.cancel-btn, .confirm-btn {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  border: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1.2;
}

.cancel-btn {
  background-color: #f5f5f5;
  color: #666;
}

.confirm-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
}

.confirm-btn[disabled] {
  background-color: #ccc;
  color: #999;
}

/* 响应式 */
@media screen and (max-width: 767px) {
  .org-detail-container {
    padding: 15px;
  }
  
  .member-item {
    flex-wrap: wrap;
  }
  
  .member-actions {
    width: 100%;
    margin-top: 8px;
    justify-content: flex-end;
  }
}
</style>
