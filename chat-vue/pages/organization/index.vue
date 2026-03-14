<template>
  <app-layout title="我的组织">
    <view class="org-container">
      <!-- 顶部操作栏 -->
      <view class="section-header">
        <view class="section-title">我的组织</view>
        <view class="header-actions">
          <button class="join-org-btn" @tap="showJoinDialog">加入组织</button>
          <button class="create-org-btn" @tap="showCreateOrgDialog">创建组织</button>
        </view>
      </view>
      
      <!-- 加载状态 -->
      <view v-if="loading" class="loading">
        <text>加载中...</text>
      </view>
      
      <!-- 空状态 -->
      <view v-else-if="organizations.length === 0" class="empty-state">
        <text class="empty-icon">🏢</text>
        <text class="empty-text">暂无组织</text>
        <text class="empty-hint">创建或加入一个组织，与团队成员共享知识库</text>
        <view class="empty-actions">
          <button class="join-org-btn" @tap="showJoinDialog">加入组织</button>
        </view>
      </view>
      
      <!-- 组织列表 -->
      <view v-else class="org-grid">
        <view 
          v-for="org in organizations" 
          :key="org.id" 
          class="org-card" 
          @tap="navigateToDetail(org.id)"
        >
          <view class="org-card-content">
            <view class="org-card-header">
              <text class="org-name">{{ org.name }}</text>
              <view class="org-role-tag" :class="getRoleClass(org.role)">
                {{ getRoleText(org.role) }}
              </view>
            </view>
            <text class="org-description">{{ org.description || '暂无描述' }}</text>
            <view class="org-meta">
              <text class="org-member-count">{{ org.member_count || 0 }} 名成员</text>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 创建组织弹窗 -->
      <view v-if="showCreateOrg" class="dialog" @tap.self="cancelCreateOrg">
        <view class="dialog-content">
          <text class="dialog-title">创建组织</text>
          
          <view class="form-item">
            <text class="form-label">组织名称 <text class="required">*</text></text>
            <input 
              type="text" 
              :value="newOrg.name"
              @input="onNameInput"
              placeholder="输入组织名称" 
              maxlength="50"
              class="form-input"
              confirm-type="next"
              :adjust-position="true"
            />
          </view>
          
          <view class="form-item">
            <text class="form-label">组织描述</text>
            <textarea
              :value="newOrg.description"
              @input="onDescInput"
              placeholder="输入组织描述(选填)" 
              class="form-textarea"
              maxlength="200"
              :adjust-position="true"
            ></textarea>
          </view>
          
          <view class="dialog-buttons">
            <button class="cancel-btn" @tap="cancelCreateOrg" :disabled="creating">取消</button>
            <button class="confirm-btn" @tap="confirmCreateOrg" :disabled="!newOrg.name.trim() || creating">
              {{ creating ? '创建中...' : '创建' }}
            </button>
          </view>
        </view>
      </view>
      
      <!-- 加入组织弹窗 -->
      <view v-if="showJoinOrg" class="dialog" @tap.self="cancelJoinOrg">
        <view class="dialog-content">
          <text class="dialog-title">加入组织</text>
          
          <view class="form-item">
            <text class="form-label">邀请链接</text>
            <input 
              type="text" 
              v-model="inviteLink"
              placeholder="粘贴邀请链接" 
              class="form-input"
            />
          </view>
          
          <view class="join-tip">
            <text>请向组织管理员获取邀请链接</text>
          </view>
          
          <view class="dialog-buttons">
            <button class="cancel-btn" @tap="cancelJoinOrg">取消</button>
            <button class="confirm-btn" @tap="confirmJoinOrg" :disabled="!inviteLink.trim()">
              加入
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
import { getCurrentUser, verifyToken } from '../../utils/auth.js';

export default {
  components: {
    AppLayout,
    LoginDialog
  },
  data() {
    return {
      organizations: [],
      loading: false,
      showCreateOrg: false,
      showJoinOrg: false,
      inviteLink: '',
      creating: false,
      newOrg: {
        name: '',
        description: ''
      },
      loginVisible: false,
      userInfo: null,
      isLoggedIn: false
    };
  },
  onLoad() {
    this.userInfo = getCurrentUser();
    this.isLoggedIn = !!this.userInfo;
    
    uni.$on('userInfoUpdated', this.handleUserInfoUpdated);
    
    this.validateAndLoad();
  },
  onShow() {
    if (this.isLoggedIn) {
      this.fetchOrganizations();
    }
  },
  onUnload() {
    uni.$off('userInfoUpdated', this.handleUserInfoUpdated);
  },
  methods: {
    async validateAndLoad() {
      const token = uni.getStorageSync('token');
      
      if (!token) {
        this.redirectToLogin();
        return;
      }
      
      try {
        const valid = await verifyToken();
        if (!valid) {
          this.redirectToLogin();
          return;
        }
        
        this.userInfo = getCurrentUser();
        this.isLoggedIn = true;
        this.fetchOrganizations();
      } catch (e) {
        console.error('验证token失败:', e);
        this.redirectToLogin();
      }
    },
    
    redirectToLogin() {
      uni.removeStorageSync('token');
      uni.removeStorageSync('userInfo');
      
      uni.reLaunch({
        url: '/pages/user/login/index'
      });
    },
    
    handleUserInfoUpdated(userInfo) {
      this.userInfo = userInfo;
      this.isLoggedIn = !!userInfo;
      if (this.isLoggedIn) {
        this.fetchOrganizations();
      } else {
        this.organizations = [];
      }
    },
    
    async fetchOrganizations() {
      if (!this.isLoggedIn) {
        this.organizations = [];
        return;
      }
      
      this.loading = true;
      try {
        const result = await api.get('/org/organizations');
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.organizations = result.data || [];
        } else {
          this.organizations = [];
        }
      } catch (error) {
        console.error('获取组织列表失败:', error);
        this.organizations = [];
      } finally {
        this.loading = false;
      }
    },
    
    navigateToDetail(orgId) {
      uni.navigateTo({
        url: `/pages/organization/detail?id=${orgId}`
      });
    },
    
    showCreateOrgDialog() {
      if (!this.isLoggedIn) {
        uni.showModal({
          title: '提示',
          content: '创建组织需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }
      
      this.newOrg = { name: '', description: '' };
      this.showCreateOrg = true;
    },
    
    cancelCreateOrg() {
      this.showCreateOrg = false;
    },
    
    onNameInput(e) {
      this.newOrg.name = e.detail.value;
    },
    
    onDescInput(e) {
      this.newOrg.description = e.detail.value;
    },
    
    async confirmCreateOrg() {
      if (!this.newOrg.name.trim()) {
        api.showError('请输入组织名称');
        return;
      }
      
      this.creating = true;
      try {
        const result = await api.post('/org/organizations', {
          name: this.newOrg.name.trim(),
          description: this.newOrg.description.trim()
        });
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('组织创建成功');
          this.showCreateOrg = false;
          this.fetchOrganizations();
          
          if (result.data && result.data.id) {
            setTimeout(() => {
              this.navigateToDetail(result.data.id);
            }, 500);
          }
        } else {
          api.showError(result?.message || '创建组织失败');
        }
      } catch (error) {
        console.error('创建组织失败:', error);
        api.showError('创建组织失败');
      } finally {
        this.creating = false;
      }
    },
    
    showJoinDialog() {
      this.inviteLink = '';
      this.showJoinOrg = true;
    },
    
    cancelJoinOrg() {
      this.showJoinOrg = false;
    },
    
    confirmJoinOrg() {
      if (!this.inviteLink.trim()) {
        api.showError('请输入邀请链接');
        return;
      }
      
      let code = this.inviteLink.trim();
      const codeMatch = code.match(/code=([a-zA-Z0-9_-]+)/);
      if (codeMatch) {
        code = codeMatch[1];
      }
      
      this.showJoinOrg = false;
      uni.navigateTo({
        url: `/pages/organization/join?code=${code}`
      });
    },
    
    getRoleText(role) {
      const roleMap = {
        'owner': '创建者',
        'admin': '管理员',
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
      this.fetchOrganizations();
    },
    
    onLoginVisibleChange(visible) {
      this.loginVisible = visible;
    }
  }
};
</script>

<style>
.org-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.join-org-btn {
  background-color: #fff;
  color: var(--primary-color, #007AFF);
  padding: 0 15px;
  height: 36px;
  line-height: 36px;
  border-radius: 6px;
  font-size: 14px;
  border: 1px solid var(--primary-color, #007AFF);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.create-org-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 0 15px;
  height: 36px;
  line-height: 36px;
  border-radius: 6px;
  font-size: 14px;
  border: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.empty-actions {
  margin-top: 20px;
}

.empty-actions .join-org-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  border: none;
}

.join-tip {
  text-align: center;
  padding: 10px 0;
  color: #999;
  font-size: 12px;
}

.org-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.org-card {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.org-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.org-card-content {
  padding: 20px;
}

.org-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.org-name {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.org-role-tag {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 12px;
  white-space: nowrap;
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

.org-description {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.org-meta {
  display: flex;
  align-items: center;
}

.org-member-count {
  font-size: 13px;
  color: #999;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background-color: white;
  border-radius: 12px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 18px;
  color: #333;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 14px;
  color: #999;
  text-align: center;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px;
  color: #666;
}

/* 弹窗样式 */
.dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.dialog-content {
  background-color: white;
  border-radius: 12px;
  padding: 24px;
  width: 90%;
  max-width: 450px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 10000;
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
  height: 44px;
  padding: 0 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
  background-color: #fff;
  position: relative;
  z-index: 10001;
}

.form-input:focus {
  border-color: var(--primary-color, #007AFF);
  outline: none;
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

.form-textarea:focus {
  border-color: var(--primary-color, #007AFF);
  outline: none;
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
  line-height: 1.2;
  display: flex;
  align-items: center;
  justify-content: center;
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
  .org-container {
    padding: 15px;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .create-org-btn {
    width: 100%;
    text-align: center;
  }
  
  .org-grid {
    grid-template-columns: 1fr;
  }
}
</style>
