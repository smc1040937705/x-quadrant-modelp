<template>
  <app-layout title="加入组织">
    <view class="join-container">
      <!-- 加载状态 -->
      <view v-if="loading" class="loading-state">
        <text>正在获取邀请信息...</text>
      </view>
      
      <!-- 邀请无效 -->
      <view v-else-if="error" class="error-state">
        <text class="error-icon">❌</text>
        <text class="error-title">邀请链接无效</text>
        <text class="error-message">{{ errorMessage }}</text>
        <button class="back-btn" @tap="goBack">返回</button>
      </view>
      
      <!-- 已是成员 -->
      <view v-else-if="alreadyMember" class="already-member-state">
        <text class="success-icon">✓</text>
        <text class="state-title">您已在该组织中</text>
        <text class="state-message">您已经是「{{ inviteInfo.org_name }}」的成员</text>
        <button class="primary-btn" @tap="goToOrganization">查看组织</button>
      </view>
      
      <!-- 邀请信息 -->
      <view v-else class="invite-info">
        <view class="invite-card">
          <text class="invite-title">您被邀请加入</text>
          <text class="org-name">{{ inviteInfo.org_name }}</text>
          
          <view class="invite-details">
            <view class="detail-item">
              <text class="detail-label">邀请人</text>
              <text class="detail-value">{{ inviteInfo.inviter_name || inviteInfo.inviter_email }}</text>
            </view>
            <view v-if="inviteInfo.org_description" class="detail-item">
              <text class="detail-label">组织描述</text>
              <text class="detail-value">{{ inviteInfo.org_description }}</text>
            </view>
            <view class="detail-item">
              <text class="detail-label">当前成员</text>
              <text class="detail-value">{{ inviteInfo.member_count || 0 }} 人</text>
            </view>
          </view>
          
          <!-- 未登录提示 -->
          <view v-if="!isLoggedIn" class="login-hint">
            <text>请先登录后再加入组织</text>
            <button class="login-btn" @tap="showLoginDialog">立即登录</button>
          </view>
          
          <!-- 已登录，显示加入按钮 -->
          <view v-else class="action-section">
            <button class="join-btn" @tap="joinOrganization" :disabled="joining">
              {{ joining ? '加入中...' : '加入组织' }}
            </button>
            <button class="cancel-btn" @tap="goBack">取消</button>
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
      inviteCode: '',
      inviteInfo: {},
      loading: true,
      error: false,
      errorMessage: '',
      alreadyMember: false,
      joining: false,
      loginVisible: false,
      userInfo: null,
      isLoggedIn: false
    };
  },
  onLoad(options) {
    this.userInfo = getCurrentUser();
    this.isLoggedIn = !!this.userInfo;
    
    if (options.code) {
      this.inviteCode = options.code;
      this.fetchInviteInfo();
    } else {
      this.error = true;
      this.errorMessage = '邀请链接参数缺失';
      this.loading = false;
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
      
      // 登录后重新获取邀请信息（检查是否已是成员）
      if (this.isLoggedIn && this.inviteCode) {
        this.fetchInviteInfo();
      }
    },
    
    async fetchInviteInfo() {
      this.loading = true;
      this.error = false;
      
      try {
        const result = await api.get(`/org/invites/${this.inviteCode}`, {}, false);
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.inviteInfo = result.data || {};
          this.alreadyMember = result.data.already_member || false;
        } else if (result && result.code === 'INVITE_EXPIRED') {
          this.error = true;
          this.errorMessage = '邀请链接已过期';
        } else if (result && result.code === 'INVITE_NOT_FOUND') {
          this.error = true;
          this.errorMessage = '邀请链接不存在';
        } else {
          this.error = true;
          this.errorMessage = result?.message || '获取邀请信息失败';
        }
      } catch (error) {
        console.error('获取邀请信息失败:', error);
        this.error = true;
        this.errorMessage = '网络错误，请稍后重试';
      } finally {
        this.loading = false;
      }
    },
    
    async joinOrganization() {
      if (!this.isLoggedIn) {
        this.loginVisible = true;
        return;
      }
      
      this.joining = true;
      try {
        const result = await api.post(`/org/invites/${this.inviteCode}/accept`);
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('已成功加入组织');
          
          // 跳转到组织详情页
          setTimeout(() => {
            const orgId = result.data?.org_id || this.inviteInfo.org_id;
            if (orgId) {
              uni.redirectTo({
                url: `/pages/organization/detail?id=${orgId}`
              });
            } else {
              uni.redirectTo({
                url: '/pages/organization/index'
              });
            }
          }, 1000);
        } else if (result && result.code === 'ALREADY_MEMBER') {
          this.alreadyMember = true;
        } else {
          api.showError(result?.message || '加入失败');
        }
      } catch (error) {
        console.error('加入组织失败:', error);
        api.showError('加入失败，请稍后重试');
      } finally {
        this.joining = false;
      }
    },
    
    goToOrganization() {
      const orgId = this.inviteInfo.org_id;
      if (orgId) {
        uni.redirectTo({
          url: `/pages/organization/detail?id=${orgId}`
        });
      } else {
        uni.redirectTo({
          url: '/pages/organization/index'
        });
      }
    },
    
    goBack() {
      uni.navigateBack({
        fail: () => {
          uni.redirectTo({
            url: '/pages/organization/index'
          });
        }
      });
    },
    
    showLoginDialog() {
      this.loginVisible = true;
    },
    
    onLoginSuccess(userInfo) {
      this.userInfo = typeof userInfo === 'string' ? JSON.parse(userInfo) : userInfo;
      this.isLoggedIn = !!this.userInfo;
      
      // 登录成功后重新获取邀请信息
      this.fetchInviteInfo();
    },
    
    onLoginVisibleChange(visible) {
      this.loginVisible = visible;
    }
  }
};
</script>

<style>
.join-container {
  padding: 20px;
  max-width: 500px;
  margin: 0 auto;
  min-height: 60vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.loading-state, .error-state, .already-member-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.error-icon, .success-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.success-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: #4caf50;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  margin-bottom: 16px;
}

.error-title, .state-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.error-message, .state-message {
  font-size: 14px;
  color: #666;
  text-align: center;
  margin-bottom: 24px;
}

.back-btn {
  background-color: #f5f5f5;
  color: #666;
  padding: 10px 32px;
  border-radius: 8px;
  font-size: 14px;
  border: none;
}

.primary-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 12px 32px;
  border-radius: 8px;
  font-size: 14px;
  border: none;
}

/* 邀请卡片 */
.invite-card {
  background-color: white;
  border-radius: 16px;
  padding: 32px 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.invite-title {
  font-size: 14px;
  color: #666;
  display: block;
  margin-bottom: 8px;
}

.org-name {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  display: block;
  margin-bottom: 24px;
}

.invite-details {
  background-color: #f9f9f9;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
  text-align: left;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 8px 0;
}

.detail-item:not(:last-child) {
  border-bottom: 1px solid #eee;
}

.detail-label {
  font-size: 13px;
  color: #999;
  flex-shrink: 0;
}

.detail-value {
  font-size: 14px;
  color: #333;
  text-align: right;
  margin-left: 16px;
}

.login-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background-color: #fff3e0;
  border-radius: 8px;
  margin-bottom: 16px;
}

.login-hint text {
  font-size: 14px;
  color: #f57c00;
}

.login-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  border: none;
}

.action-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.join-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 14px 32px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  border: none;
  width: 100%;
}

.join-btn[disabled] {
  background-color: #ccc;
}

.cancel-btn {
  background-color: transparent;
  color: #666;
  padding: 12px 32px;
  border-radius: 8px;
  font-size: 14px;
  border: none;
}

/* 响应式 */
@media screen and (max-width: 767px) {
  .join-container {
    padding: 15px;
  }
  
  .invite-card {
    padding: 24px 16px;
  }
  
  .org-name {
    font-size: 24px;
  }
}
</style>
