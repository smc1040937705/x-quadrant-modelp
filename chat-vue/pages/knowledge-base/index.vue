<template>
  <app-layout>
    <view class="knowledge-container">
      <!-- 知识库管理区域 -->
      <view class="kb-section">
        <view class="section-header">
          <view class="section-title">知识库</view>
          <button class="create-kb-btn" @tap="showCreateKBDialog">创建知识库</button>
        </view>
        
        <!-- Tab切换 -->
        <view class="kb-tabs">
          <view 
            :class="['tab-item', { active: activeTab === 'personal' }]" 
            @tap="switchTab('personal')"
          >
            <text class="tab-text">个人知识库</text>
            <text class="tab-count">{{ personalKBs.length }}</text>
          </view>
          <view 
            v-for="org in organizations" 
            :key="org.org_id"
            :class="['tab-item', { active: activeTab === 'org_' + org.org_id }]" 
            @tap="switchTab('org_' + org.org_id)"
          >
            <text class="tab-text">{{ org.org_name }}</text>
            <text class="tab-count">{{ org.knowledge_bases ? org.knowledge_bases.length : 0 }}</text>
          </view>
        </view>
        
        <view v-if="loadingKBs" class="loading">
          <text>加载中...</text>
        </view>
        
        <!-- 个人知识库内容 -->
        <view v-else-if="activeTab === 'personal'" class="kb-content">
          <view v-if="personalKBs.length === 0" class="empty-state">
            <text class="empty-icon">📚</text>
            <text class="empty-text">暂无个人知识库</text>
            <text class="empty-hint">点击上方"创建知识库"按钮开始创建</text>
          </view>
          <view v-else class="kb-grid">
            <view v-for="kb in personalKBs" :key="kb.id" class="kb-card" @tap="navigateToDetail(kb.id)">
              <view class="kb-card-content">
                <view class="kb-card-header">
                  <text class="kb-name">{{ kb.name }}</text>
                  <text class="kb-doc-count">{{ kb.doc_count || 0 }}个文档</text>
                </view>
                <text class="kb-description">{{ kb.description || '无描述' }}</text>
                <view v-if="kb.shared_to_orgs && kb.shared_to_orgs.length > 0" class="kb-share-tags">
                  <text class="share-tag" v-for="org in kb.shared_to_orgs" :key="org.org_id">
                    已共享: {{ org.org_name }}
                  </text>
                </view>
              </view>
              <view class="kb-card-footer">
                <button class="action-btn rename-btn" @tap.stop="showRenameKBDialog(kb)">编辑</button>
                <button class="action-btn share-btn" @tap.stop="showShareDialog(kb)">共享</button>
                <button class="action-btn delete-btn" @tap.stop="confirmDeleteKB(kb.id)">删除</button>
              </view>
            </view>
          </view>
        </view>
        
        <!-- 组织知识库内容 -->
        <view v-else class="kb-content">
          <view v-for="org in organizations" :key="org.org_id">
            <view v-if="activeTab === 'org_' + org.org_id">
              <view v-if="!org.knowledge_bases || org.knowledge_bases.length === 0" class="empty-state">
                <text class="empty-icon">🏢</text>
                <text class="empty-text">该组织暂无共享知识库</text>
                <text class="empty-hint">将个人知识库共享到组织后，成员即可查看</text>
              </view>
              <view v-else class="kb-grid">
                <view v-for="kb in org.knowledge_bases" :key="kb.id" class="kb-card" @tap="navigateToDetail(kb.id)">
                  <view class="kb-card-content">
                    <view class="kb-card-header">
                      <text class="kb-name">{{ kb.name }}</text>
                      <text class="kb-doc-count">{{ kb.doc_count || 0 }}个文档</text>
                    </view>
                    <text class="kb-description">{{ kb.description || '无描述' }}</text>
                    <view class="kb-creator-tag">
                      <text v-if="kb.is_owner" class="creator-tag mine">我的</text>
                      <text v-else class="creator-tag others">{{ kb.sharer_name || '他人' }}创建</text>
                    </view>
                  </view>
                  <view class="kb-card-footer">
                    <button v-if="kb.is_owner" class="action-btn unshare-btn" @tap.stop="confirmUnshare(kb, org.org_id)">取消共享</button>
                  </view>
                </view>
              </view>
            </view>
          </view>
        </view>
        
        <!-- 无组织提示 -->
        <view v-if="organizations.length === 0 && !loadingKBs && activeTab === 'personal'" class="no-org-tip">
          <text>您还没有加入任何组织，</text>
          <text class="link" @tap="navigateToOrg">去创建或加入组织</text>
        </view>
      </view>
      
      <!-- 共享知识库弹窗 -->
      <view v-if="showShare" class="dialog share-dialog">
        <view class="dialog-content" @tap.stop>
          <text class="dialog-title">共享知识库</text>
          <text class="dialog-subtitle">选择要共享到的组织</text>
          
          <view class="org-list">
            <view v-if="userOrganizations.length === 0" class="empty-org">
              <text>您还没有加入任何组织</text>
            </view>
            <view 
              v-for="org in userOrganizations" 
              :key="org.id"
              :class="['org-item', { selected: selectedOrgIds.includes(org.id), disabled: isAlreadyShared(org.id) }]"
              @tap="toggleOrgSelection(org.id)"
            >
              <text class="org-name">{{ org.name }}</text>
              <text v-if="isAlreadyShared(org.id)" class="shared-mark">已共享</text>
              <text v-else-if="selectedOrgIds.includes(org.id)" class="select-mark">✓</text>
            </view>
          </view>
          
          <view class="dialog-buttons">
            <button class="cancel-btn" @tap="cancelShare">取消</button>
            <button class="confirm-btn" @tap="confirmShare" :disabled="selectedOrgIds.length === 0">确认共享</button>
          </view>
        </view>
      </view>
      
      <!-- 创建资料库弹窗 -->
      <view v-if="showCreateKB" class="dialog create-kb-dialog">
        <view class="dialog-content" @tap.stop>
          <text class="dialog-title">创建知识资料库</text>
          
          <view class="form-item">
            <text class="form-label">资料库名称</text>
            <view class="input-wrapper" :class="{ 'focus-within': isNameFocused }">
              <input 
                type="text" 
                v-model="newKB.name"
                placeholder="输入资料库名称" 
                maxlength="140"
                class="basic-input"
                @focus="focusNameInput"
                @blur="isNameFocused = false"
              />
            </view>
          </view>
          
          <view class="form-item">
            <text class="form-label">资料库描述</text>
            <view class="input-wrapper" :class="{ 'focus-within': isDescFocused }">
              <textarea
                v-model="newKB.description"
                placeholder="输入知识库描述(选填)" 
                class="basic-textarea"
                @focus="focusDescInput"
                @blur="isDescFocused = false"
              ></textarea>
            </view>
          </view>
          
          <view class="form-item">
            <text class="form-label">归属</text>
            <view class="owner-selector">
              <view 
                :class="['owner-option', { active: newKB.owner_type === 'personal' }]" 
                @tap="newKB.owner_type = 'personal'; newKB.org_id = null"
              >
                个人
              </view>
              <view 
                v-for="org in userOrganizations" 
                :key="org.id"
                :class="['owner-option', { active: newKB.owner_type === 'organization' && newKB.org_id === org.id }]" 
                @tap="newKB.owner_type = 'organization'; newKB.org_id = org.id"
              >
                {{ org.name }}
              </view>
            </view>
          </view>
          
          <view class="form-item">
            <text class="form-label">分块策略</text>
            <view class="select-wrapper">
              <select v-model="newKB.chunking_strategy" class="form-select">
                <option value="fixed">固定长度 (Fixed)</option>
                <option value="semantic">语义分块 (Semantic)</option>
                <option value="sentence">句子分块 (Sentence)</option>
              </select>
            </view>
          </view>
          
          <view class="form-row" v-if="newKB.chunking_strategy === 'fixed'">
            <view class="form-item form-item-half">
              <text class="form-label">分块大小</text>
              <input 
                type="number" 
                v-model.number="newKB.chunk_size"
                placeholder="默认1000" 
                min="100" 
                max="10000"
                class="basic-input"
              />
            </view>
            <view class="form-item form-item-half">
              <text class="form-label">重叠大小</text>
              <input 
                type="number" 
                v-model.number="newKB.chunk_overlap"
                placeholder="默认200" 
                min="0" 
                max="2000"
                class="basic-input"
              />
            </view>
          </view>
          
          <view class="chunking-tip">
            <text class="tip-text" v-if="newKB.chunking_strategy === 'fixed'">固定长度分块：按字符数分割，适合大多数场景</text>
            <text class="tip-text" v-if="newKB.chunking_strategy === 'semantic'">语义分块：按语义相似性分割，效果更好但处理较慢</text>
            <text class="tip-text" v-if="newKB.chunking_strategy === 'sentence'">句子分块：按句子边界分割，保持语义完整性</text>
          </view>
          
          <view class="dialog-buttons">
            <button class="cancel-btn" @tap="cancelCreateKB" :disabled="creating">取消</button>
            <button class="confirm-btn" @tap="confirmCreateKB" :disabled="!newKB.name || creating">
              <text v-if="creating">创建中...</text>
              <text v-else>创建</text>
            </button>
          </view>
        </view>
      </view>
      
      <!-- 重命名资料库弹窗 -->
      <view v-if="showRenameKB" class="dialog rename-kb-dialog">
        <view class="dialog-content" @tap.stop>
          <text class="dialog-title">重命名知识资料库</text>
          
          <view class="form-item">
            <text class="form-label">资料库名称</text>
            <view class="input-wrapper" :class="{ 'focus-within': isRenameNameFocused }">
              <input 
                type="text" 
                v-model="newKBName"
                placeholder="输入新的资料库名称" 
                maxlength="140"
                class="basic-input"
                @focus="focusRenameNameInput"
                @blur="isRenameNameFocused = false"
              />
            </view>
          </view>
          
          <view class="form-item">
            <text class="form-label">资料库描述</text>
            <view class="input-wrapper" :class="{ 'focus-within': isRenameDescFocused }">
              <textarea
                v-model="newKBDesc"
                placeholder="输入知识库描述(选填)" 
                class="basic-textarea"
                @focus="focusRenameDescInput"
                @blur="isRenameDescFocused = false"
              ></textarea>
            </view>
          </view>
          
          <view class="form-item">
            <text class="form-label">分块策略</text>
            <view class="select-wrapper">
              <select v-model="renameKBChunkingStrategy" class="form-select">
                <option value="fixed">固定长度 (Fixed)</option>
                <option value="semantic">语义分块 (Semantic)</option>
                <option value="sentence">句子分块 (Sentence)</option>
              </select>
            </view>
          </view>
          
          <view class="form-row" v-if="renameKBChunkingStrategy === 'fixed'">
            <view class="form-item form-item-half">
              <text class="form-label">分块大小</text>
              <input 
                type="number" 
                v-model.number="renameKBChunkSize"
                placeholder="默认1000" 
                min="100" 
                max="10000"
                class="basic-input"
              />
            </view>
            <view class="form-item form-item-half">
              <text class="form-label">重叠大小</text>
              <input 
                type="number" 
                v-model.number="renameKBChunkOverlap"
                placeholder="默认200" 
                min="0" 
                max="2000"
                class="basic-input"
              />
            </view>
          </view>
          
          <view class="chunking-tip">
            <text class="tip-text" v-if="renameKBChunkingStrategy === 'fixed'">固定长度分块：按字符数分割，适合大多数场景</text>
            <text class="tip-text" v-if="renameKBChunkingStrategy === 'semantic'">语义分块：按语义相似性分割，效果更好但处理较慢</text>
            <text class="tip-text" v-if="renameKBChunkingStrategy === 'sentence'">句子分块：按句子边界分割，保持语义完整性</text>
          </view>
          
          <view class="dialog-buttons">
            <button class="cancel-btn" @tap="cancelRenameKB">取消</button>
            <button class="confirm-btn" @tap="confirmRenameKB" :disabled="!newKBName">保存</button>
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
import auth from '../../utils/auth.js';

export default {
  components: {
    AppLayout,
    LoginDialog
  },
  data() {
    return {
      // 知识库相关
      personalKBs: [],
      organizations: [],
      loadingKBs: false,
      userOrganizations: [],
      activeTab: 'personal',
      
      // 共享知识库相关
      showShare: false,
      shareKb: null,
      selectedOrgIds: [],
      
      // 创建知识库相关
      showCreateKB: false,
      creating: false,
      newKB: {
        name: '',
        description: '',
        chunking_strategy: 'fixed',
        chunk_size: 1000,
        chunk_overlap: 200
      },
      isNameFocused: false,
      isDescFocused: false,
      
      // 重命名知识库相关
      showRenameKB: false,
      renameKBId: null,
      newKBName: '',
      newKBDesc: '',
      renameKBChunkingStrategy: 'fixed',
      renameKBChunkSize: 1000,
      renameKBChunkOverlap: 200,
      isRenameNameFocused: false,
      isRenameDescFocused: false,
      
      // 登录相关
      loginVisible: false,
      userInfo: null,
      isLoggedIn: false,
    }
  },
  computed: {
    // 获取已共享的组织ID列表
    sharedOrgIds() {
      if (!this.shareKb || !this.shareKb.shared_to_orgs) return [];
      return this.shareKb.shared_to_orgs.map(org => org.org_id);
    }
  },
  onLoad() {
    this.userInfo = getCurrentUser();
    this.isLoggedIn = !!this.userInfo;
    
    this.checkDeviceType();
    
    uni.$on('userInfoUpdated', this.handleUserInfoUpdated);
    
    this.validateAndLoad();
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
        
        this.fetchKnowledgeBases();
        this.fetchUserOrganizations();
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
    
    checkDeviceType() {
      uni.getSystemInfo({
        success: (res) => {
          this.isPc = res.windowWidth >= 768;
        }
      });
    },
    
    // 处理用户信息更新事件
    handleUserInfoUpdated(userInfo) {
      this.userInfo = userInfo;
      this.isLoggedIn = !!userInfo;
      
      // 检查是否正在退出应用
      const isExitingApp = uni.getStorageSync('isExitingApp');
      if (isExitingApp === 'true') {
        return;
      }
      
      // 只有在用户登录时才重新加载知识库列表
      if (this.isLoggedIn) {
        this.fetchKnowledgeBases();
      }
    },

    async fetchKnowledgeBases() {
      this.loadingKBs = true;
      
      try {
        const result = await api.get('/llm/knowledge-bases/basic');
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          const data = result.data || {};
          this.personalKBs = data.personal || [];
          this.organizations = data.organizations || [];
        } else if (result && result.code === 'UNAUTHORIZED') {
          this.personalKBs = [];
          this.organizations = [];
          uni.removeStorageSync('userInfo');
          uni.removeStorageSync('token');
          this.isLoggedIn = false;
          
          uni.showToast({
            title: '登录已过期，请重新登录',
            icon: 'none',
            duration: 2000
          });
          
          setTimeout(() => {
            uni.reLaunch({ 
              url: '/pages/user/login/index' 
            });
          }, 1500);
          return;
        } else {
          this.personalKBs = [];
          this.organizations = [];
          
          uni.showToast({
            title: result?.message || '获取知识库列表失败',
            icon: 'none',
            duration: 2000
          });
        }
      } catch (error) {
        console.error('获取知识库列表失败:', error);
        this.personalKBs = [];
        this.organizations = [];
        
        // 检查是否是网络错误
        const isNetworkError = error.code === 'NETWORK_ERROR' || 
          (error.errMsg && (
            error.errMsg.includes('request:fail') || 
            error.errMsg.includes('timeout') || 
            error.errMsg.includes('connection refused')
          ));
        
        if (isNetworkError) {
          // 网络错误，显示友好提示
          uni.showToast({
            title: '网络连接失败，请检查网络或服务器状态',
            icon: 'none',
            duration: 3000
          });
        } else if (error.message && error.message.includes('未授权')) {
          // 未授权错误，清除登录状态并跳转到登录页
          uni.removeStorageSync('userInfo');
          uni.removeStorageSync('token');
          this.isLoggedIn = false;
          
          // 跳转到登录页
          setTimeout(() => {
            uni.reLaunch({ url: '/pages/user/login/index' });
          }, 100);
        } else {
          // 其他错误
          uni.showToast({
            title: '获取知识库列表失败',
            icon: 'none',
            duration: 2000
          });
        }
      } finally {
        this.loadingKBs = false;
      }
    },
    
    // 导航到知识库详情页
    navigateToDetail(kbId) {
      uni.navigateTo({
        url: `/pages/knowledge-base/detail?id=${kbId}`
      });
    },
    
    switchTab(tab) {
      this.activeTab = tab;
    },
    
    showShareDialog(kb) {
      this.shareKb = kb;
      this.selectedOrgIds = [];
      this.showShare = true;
    },
    
    // 取消共享
    cancelShare() {
      this.showShare = false;
      this.shareKb = null;
      this.selectedOrgIds = [];
    },
    
    // 检查是否已共享到某组织
    isAlreadyShared(orgId) {
      return this.sharedOrgIds.includes(orgId);
    },
    
    // 切换组织选择
    toggleOrgSelection(orgId) {
      if (this.isAlreadyShared(orgId)) return;
      
      const index = this.selectedOrgIds.indexOf(orgId);
      if (index > -1) {
        this.selectedOrgIds.splice(index, 1);
      } else {
        this.selectedOrgIds.push(orgId);
      }
    },
    
    // 确认共享
    async confirmShare() {
      if (this.selectedOrgIds.length === 0) {
        api.showError('请选择要共享的组织');
        return;
      }
      
      try {
        let successCount = 0;
        for (const orgId of this.selectedOrgIds) {
          const result = await api.post(`/llm/knowledge-bases/${this.shareKb.id}/share`, {
            org_id: orgId
          });
          if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
            successCount++;
          }
        }
        
        if (successCount > 0) {
          api.showSuccess(`成功共享到 ${successCount} 个组织`);
          this.fetchKnowledgeBases();
        }
        
        this.cancelShare();
      } catch (error) {
        console.error('共享知识库失败:', error);
        api.showError('共享知识库失败');
      }
    },
    
    // 确认取消共享
    confirmUnshare(kb, orgId) {
      uni.showModal({
        title: '确认取消共享',
        content: '取消共享后，组织成员将无法访问该知识库，确定要取消吗？',
        success: async (res) => {
          if (res.confirm) {
            await this.unshareKnowledgeBase(kb.id, orgId);
          }
        }
      });
    },
    
    // 取消共享知识库
    async unshareKnowledgeBase(kbId, orgId) {
      try {
        const result = await api.delete(`/llm/knowledge-bases/${kbId}/share/${orgId}`);
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('取消共享成功');
          this.fetchKnowledgeBases();
        } else {
          api.showError(result?.message || '取消共享失败');
        }
      } catch (error) {
        console.error('取消共享失败:', error);
        api.showError('取消共享失败');
      }
    },
    
    // 导航到组织页面
    navigateToOrg() {
      uni.navigateTo({
        url: '/pages/organization/index'
      });
    },
    
    // 显示创建资料库弹窗
    showCreateKBDialog() {
      // 检查用户是否已登录
      if (!this.isLoggedIn) {
        uni.showModal({
          title: '提示',
          content: '创建知识资料库需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }
      
      this.newKB = {
        name: '',
        description: '',
        chunking_strategy: 'fixed',
        chunk_size: 1000,
        chunk_overlap: 200
      };
      this.showCreateKB = true;
    },
    
    // 取消创建知识库
    cancelCreateKB() {
      this.showCreateKB = false;
    },
    
    // 确认创建知识库
    async confirmCreateKB() {
      if (!this.newKB.name.trim()) {
        api.showError('请输入知识库名称');
        return;
      }
      
      // 再次检查用户是否已登录
      if (!this.isLoggedIn) {
        this.showCreateKB = false;
        uni.showModal({
          title: '提示',
          content: '创建知识资料库需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }
      
      this.creating = true; // 显示创建中状态
      
      try {
        // 构建请求数据
        const requestData = {
          name: this.newKB.name,
          description: this.newKB.description || '',
          chunking_strategy: this.newKB.chunking_strategy,
          chunk_size: this.newKB.chunk_size,
          chunk_overlap: this.newKB.chunk_overlap
        };
        
        // 实际API调用
        const result = await api.post('/llm/knowledge-bases', requestData);
        
        // 检查响应状态
        if (result && result.code === 'UNAUTHORIZED') {
          // 用户未登录，显示登录弹窗
          this.showCreateKB = false;
          this.loginVisible = true;
          return;
        }
        
        if (result && (result.code === '0000')) {
          // 先关闭创建弹窗，避免后续操作失败导致弹窗无法关闭
          this.showCreateKB = false;
          
          // 显示成功提示
          api.showSuccess('知识库创建成功');
          
          // 刷新知识库列表
          this.fetchKnowledgeBases();
          
          // 如果返回了知识库ID，跳转到详情页
          if (result.data && result.data.id) {
            setTimeout(() => {
              this.navigateToDetail(result.data.id);
            }, 500);
          }
        } else {
          // 其他错误情况
          api.showError(result?.message || '创建知识库失败');
        }
      } catch (error) {
        console.error('创建知识库失败:', error);
        api.showError('创建知识库失败');
      } finally {
        this.creating = false; // 隐藏创建中状态
      }
    },
    
    // 显示重命名知识库弹窗
    showRenameKBDialog(kb) {
      // 检查用户是否已登录
      if (!this.isLoggedIn) {
        uni.showModal({
          title: '提示',
          content: '编辑知识库需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }
      
      this.renameKBId = kb.id;
      this.newKBName = kb.name;
      this.newKBDesc = kb.description || '';
      this.renameKBChunkingStrategy = kb.chunking_strategy || 'fixed';
      this.renameKBChunkSize = kb.chunk_size || 1000;
      this.renameKBChunkOverlap = kb.chunk_overlap || 200;
      this.showRenameKB = true;
    },
    
    // 取消重命名知识库
    cancelRenameKB() {
      this.showRenameKB = false;
      this.renameKBId = null;
    },
    
    // 确认重命名知识库
    async confirmRenameKB() {
      if (!this.newKBName.trim()) {
        api.showError('请输入知识库名称');
        return;
      }
      
      // 再次检查用户是否已登录
      if (!this.isLoggedIn) {
        this.showRenameKB = false;
        uni.showModal({
          title: '提示',
          content: '编辑知识库需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }
      
      try {
        // 实际API调用
        const result = await api.put(`/llm/knowledge-bases/${this.renameKBId}`, {
          name: this.newKBName,
          description: this.newKBDesc || '',
          chunking_strategy: this.renameKBChunkingStrategy,
          chunk_size: this.renameKBChunkSize,
          chunk_overlap: this.renameKBChunkOverlap
        });
        
        if (result && (result.code === '0000')) {
          api.showSuccess('知识库更新成功');
          
          // 刷新知识库列表
          this.fetchKnowledgeBases();
        } else {
          api.showError(result?.message || '更新知识库失败');
        }
      } catch (error) {
        console.error('更新知识库失败:', error);
        api.showError('更新知识库失败');
      }
      
      this.showRenameKB = false;
      this.renameKBId = null;
    },
    
    // 确认删除知识库
    confirmDeleteKB(kbId) {
      // 检查用户是否已登录
      if (!this.isLoggedIn) {
        uni.showModal({
          title: '提示',
          content: '删除知识库需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }
      
      uni.showModal({
        title: '确认删除',
        content: '删除知识库将同时删除其中所有文档，此操作不可恢复！确定要删除吗？',
        success: async (res) => {
          if (res.confirm) {
            await this.deleteKnowledgeBase(kbId);
          }
        }
      });
    },
    
    // 删除知识库
    async deleteKnowledgeBase(kbId) {
      try {
        // 实际API调用
        const result = await api.delete(`/llm/knowledge-bases/${kbId}`);
        
        if (result && (result.code === '0000')) {
          api.showSuccess('知识库删除成功');
          
          // 刷新知识库列表
          this.fetchKnowledgeBases();
        } else {
          api.showError(result?.message || '删除知识库失败');
        }
      } catch (error) {
        console.error('删除知识库失败:', error);
        api.showError('删除知识库失败');
      }
    },
    
    // 登录成功后的处理
    onLoginSuccess(userInfo) {
      // 更新用户信息
      if (typeof userInfo === 'string') {
        try {
          this.userInfo = JSON.parse(userInfo);
        } catch (e) {
          console.error('解析用户信息失败:', e);
          this.userInfo = userInfo;
        }
      } else {
        this.userInfo = userInfo;
      }
      
      // 更新登录状态
      this.isLoggedIn = !!this.userInfo;
      
      // 登录成功后，加载知识库列表
      this.fetchKnowledgeBases();
    },

    // 登录弹窗可见性变化的处理
    onLoginVisibleChange(visible) {
      this.loginVisible = visible;
    },

    // 显示登录对话框
    showLoginDialog() {
      this.loginVisible = true;
    },

    // 添加新方法来处理输入框的聚焦
    focusNameInput(e) {
      this.isNameFocused = true;
      this.$nextTick(() => {
        const input = e.target;
        if (input) {
          input.focus();
        }
      });
    },
    
    focusDescInput(e) {
      this.isDescFocused = true;
      this.$nextTick(() => {
        const textarea = e.target;
        if (textarea) {
          textarea.focus();
        }
      });
    },
    
    focusRenameNameInput(e) {
      this.isRenameNameFocused = true;
      this.$nextTick(() => {
        const input = e.target;
        if (input) {
          input.focus();
        }
      });
    },
    
    focusRenameDescInput(e) {
      this.isRenameDescFocused = true;
      this.$nextTick(() => {
        const textarea = e.target;
        if (textarea) {
          textarea.focus();
        }
      });
    },
    
    // 获取用户组织列表
    async fetchUserOrganizations() {
      if (!this.isLoggedIn) {
        this.userOrganizations = [];
        return;
      }
      
      try {
        const result = await api.get('/org/organizations');
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.userOrganizations = result.data || [];
        } else {
          this.userOrganizations = [];
        }
      } catch (error) {
        console.error('获取组织列表失败:', error);
        this.userOrganizations = [];
      }
    }
  }
}
</script>

<style>
.knowledge-container {
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

.create-kb-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 8px 15px;
  border-radius: 6px;
  font-size: 14px;
  border: none;
}

.kb-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  overflow-x: auto;
  padding-bottom: 5px;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background-color: #f5f5f5;
  border-radius: 20px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.3s;
}

.tab-item:hover {
  background-color: #e8e8e8;
}

.tab-item.active {
  background-color: var(--primary-color, #007AFF);
  color: white;
}

.tab-text {
  font-size: 14px;
}

.tab-count {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.tab-item.active .tab-count {
  background-color: rgba(255, 255, 255, 0.2);
}

.kb-content {
  margin-top: 10px;
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background-color: #f9f9f9;
  border-radius: 12px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  color: #666;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 14px;
  color: #999;
  margin-bottom: 20px;
}

.create-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  border: none;
}

.kb-category {
  margin-bottom: 20px;
}

.category-header {
  display: flex;
  align-items: center;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
}

.category-header:hover {
  background-color: #e9ecef;
}

.category-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  flex: 1;
}

.category-count {
  font-size: 14px;
  color: #666;
  background-color: #e0e0e0;
  padding: 2px 10px;
  border-radius: 12px;
  margin-right: 10px;
}

.category-role {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  margin-right: 10px;
}

.category-role.owner {
  background-color: #e3f2fd;
  color: #1976d2;
}

.category-role.member {
  background-color: #fff3e0;
  color: #f57c00;
}

.category-arrow {
  font-size: 12px;
  color: #666;
  transition: transform 0.3s;
}

.category-arrow.expanded {
  transform: rotate(180deg);
}

.kb-list {
  margin-top: 10px;
  padding-left: 15px;
}

.empty-category {
  padding: 20px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.kb-card {
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
  margin-bottom: 15px;
}

.kb-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.15);
}

.kb-card-content {
  padding: 15px;
  flex-grow: 1;
}

.kb-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.kb-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  word-break: break-word;
}

.kb-doc-count {
  font-size: 12px;
  color: #666;
  background-color: #f0f0f0;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}

.kb-description {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.kb-share-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 8px;
}

.share-tag {
  font-size: 11px;
  color: #1976d2;
  background-color: #e3f2fd;
  padding: 2px 8px;
  border-radius: 4px;
}

.kb-creator-tag {
  margin-top: 8px;
}

.creator-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
}

.creator-tag.mine {
  color: #2e7d32;
  background-color: #e8f5e9;
}

.creator-tag.others {
  color: #666;
  background-color: #f5f5f5;
}

.kb-card-footer {
  display: flex;
  justify-content: flex-end;
  padding: 10px 15px;
  background-color: #f8f9fa;
  border-top: 1px solid #eee;
  gap: 10px;
}

.action-btn {
  font-size: 12px;
  padding: 5px 12px;
  border-radius: 4px;
  border: none;
}

.rename-btn {
  background-color: #f0f0f0;
  color: #333;
}

.share-btn {
  background-color: #e3f2fd;
  color: #1976d2;
}

.unshare-btn {
  background-color: #fff3e0;
  color: #f57c00;
}

.delete-btn {
  background-color: rgba(255, 59, 48, 0.1);
  color: #ff3b30;
}

.no-org-tip {
  text-align: center;
  padding: 30px;
  color: #666;
  font-size: 14px;
}

.no-org-tip .link {
  color: #007AFF;
  cursor: pointer;
}

.share-dialog .dialog-content {
  max-width: 400px;
}

.dialog-subtitle {
  font-size: 14px;
  color: #666;
  margin-bottom: 20px;
}

.org-list {
  max-height: 300px;
  overflow-y: auto;
}

.org-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.org-item:hover {
  border-color: #007AFF;
  background-color: #f8f9fa;
}

.org-item.selected {
  border-color: #007AFF;
  background-color: #e3f2fd;
}

.org-item.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.org-name {
  font-size: 14px;
  color: #333;
}

.shared-mark {
  font-size: 12px;
  color: #999;
}

.select-mark {
  font-size: 14px;
  color: #007AFF;
  font-weight: bold;
}

.empty-org {
  text-align: center;
  padding: 20px;
  color: #999;
}

.empty-state, .loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 0;
  background-color: white;
  border-radius: 10px;
  margin-bottom: 20px;
  text-align: center;
  color: #999;
  font-size: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.login-hint {
  flex-direction: row;
  background-color: #f8f9fa;
}

/* 对话框样式 */
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
  border-radius: 10px;
  padding: 20px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
  text-align: center;
}

.form-item {
  margin-bottom: 15px;
}

.form-label {
  display: block;
  font-size: 14px;
  color: #333;
  margin-bottom: 5px;
}

/* 修改表单样式，避免与uni-app样式冲突 */
.form-input, .form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background-color: #fff;
  color: #333;
  box-sizing: border-box;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.form-textarea {
  min-height: 100px;
  resize: vertical;
}

.form-input:focus, .form-textarea:focus {
  border-color: var(--primary-color, #007AFF);
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1);
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  gap: 10px;
}

.cancel-btn, .confirm-btn {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 14px;
  border: none;
  cursor: pointer;
}

.cancel-btn {
  background-color: #f0f0f0;
  color: #333;
}

.confirm-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
}

.confirm-btn[disabled] {
  background-color: #cccccc;
  color: #666;
}

/* 响应式设计 */
@media screen and (min-width: 768px) {
  .knowledge-container {
    padding: 30px;
  }
}

@media screen and (max-width: 767px) {
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .create-kb-btn {
    width: 100%;
  }
  
  .dialog-content {
    width: 95%;
    padding: 15px;
  }
}

/* 按钮样式修复 */
.create-kb-btn, .action-btn, .login-btn, .select-file-btn, .primary-btn, .cancel-btn, .confirm-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.rename-btn, .delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 32px;
}

/* 弹窗按钮修复 */
.dialog-buttons button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 36px;
}

/* uni-app输入框样式修复 */
.uni-input-wrapper, .uni-textarea-wrapper {
  width: 100%;
  position: relative;
}

.uni-input-wrapper .form-input, .uni-textarea-wrapper .form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: #f8f9fa;
  font-size: 14px;
  box-sizing: border-box;
}

.input-container {
  width: 100%;
  position: relative;
}

.native-input, .native-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background-color: #fff;
  color: #333;
  box-sizing: border-box;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.native-textarea {
  min-height: 100px;
  resize: vertical;
}

.native-input:focus, .native-textarea:focus {
  border-color: var(--primary-color, #007AFF);
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1);
}

/* 修复uni-app环境下的原生输入元素 */
page input, page textarea {
  width: 100%;
  box-sizing: border-box;
}

/* 确保输入元素在各种环境下显示正常 */
.input-container input, .input-container textarea {
  margin: 0;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  width: 100%;
  background-color: #fff;
  color: #333;
  font-size: 14px;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.input-wrapper {
  width: 100%;
  position: relative;
}

.basic-input, .basic-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: #fff;
  color: #333;
  font-size: 14px;
  box-sizing: border-box;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  height: 40px;
  line-height: 20px;
}

.basic-textarea {
  min-height: 100px;
  height: auto;
  resize: vertical;
}

/* 确保在各种环境下输入框都能正常工作 */
page .basic-input, page .basic-textarea {
  width: 100%;
  box-sizing: border-box;
}

/* 移动端适配 */
@media screen and (max-width: 767px) {
  .basic-input, .basic-textarea {
    font-size: 16px; /* 移动端更大的字体，防止缩放 */
  }
}

/* 修复uni-easyinput组件样式 */
/deep/ .uni-easyinput__content {
  background-color: #fff !important;
  border: 1px solid #ddd !important;
  border-radius: 6px !important;
}

/deep/ .uni-easyinput__content-input {
  font-size: 14px !important;
  color: #333 !important;
}

/deep/ .uni-easyinput__content-textarea {
  min-height: 100px !important;
}

/* 确保基本输入元素在uni-app环境中正确显示 */
.dialog-content .input-wrapper input,
.dialog-content .input-wrapper textarea {
  border: 1px solid #ddd !important;
  background-color: #fff !important;
  color: #333 !important;
  font-size: 14px !important;
  padding: 10px !important;
  border-radius: 6px !important;
  width: 100% !important;
  box-sizing: border-box !important;
  outline: none !important;
  -webkit-appearance: none !important;
  appearance: none !important;
}

.input-wrapper.focus-within {
  outline: none;
}

.input-wrapper.focus-within input,
.input-wrapper.focus-within textarea {
  border-color: var(--primary-color, #007AFF) !important;
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1) !important;
}

.form-select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background-color: #fff;
  color: #333;
  box-sizing: border-box;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  height: 40px;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 16px;
}

.form-select:focus {
  border-color: var(--primary-color, #007AFF);
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1);
}

.form-row {
  display: flex;
  gap: 15px;
}

.form-item-half {
  flex: 1;
}

.chunking-tip {
  padding: 8px 12px;
  background-color: #f8f9fa;
  border-radius: 6px;
  margin-top: -8px;
  margin-bottom: 15px;
}

.tip-text {
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}
</style> 