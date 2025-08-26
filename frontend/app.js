/**
 * Agno SDK Agent Generator - Frontend Application
 * 
 * Aplicação SPA em JavaScript vanilla para criação de agentes SDK
 * com integração ao WhatsApp via Evolution API.
 * 
 * Funcionalidades:
 * - Gerenciamento de estado e navegação entre seções
 * - Validação de formulário e persistência em localStorage
 * - Integração com APIs do backend
 * - Modais, toasts e logs em tempo real
 * - Acessibilidade e microinterações
 */

// Configuração da aplicação
window.API_BASE = 'http://localhost:8000';

// Estado global da aplicação
const appState = {
  // Rascunho do agente sendo criado
  agentDraft: {
    agent_name: '',
    instructions: '',
    specialization: '',
    tools: []
  },
  
  // Interface do usuário
  ui: {
    activeSection: 'page-create',
    fontScale: 0,
    reduceMotion: false,
    integrations: {
      whatsapp: false,
      payments: false,
      scheduling: false,
      crm: false,
      support: false
    }
  },

  // Configurações da Evolution API
  evolutionAPI: {
    baseURL: 'https://evolution.agentecortex.com',
    apiKey: 'e464af0bf64bbd059aa777d5cded286e',
    instanceName: 'agno-agent',
    connected: false
  },

  // Token de acesso à API
  apiToken: '',

  // Estado dos agentes
  agents: [],
  
  // Estado dos logs
  logs: [],
  
  // Estado de carregamento
  loading: false,
  
  // Arquivos gerados
  generatedFiles: []
};

// Utilitários
const Utils = {
  /**
   * Sanitiza HTML para prevenir XSS
   */
  sanitizeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  },

  /**
   * Debounce para otimizar chamadas de função
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  /**
   * Formata timestamp para exibição
   */
  formatTimestamp(date = new Date()) {
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  },

  /**
   * Gera ID único
   */
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  },

  /**
   * Converte texto em slug
   */
  slugify(text) {
    return text
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)+/g, '');
  },

  /**
   * Copia texto para a área de transferência
   */
  async copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      // Fallback para navegadores mais antigos
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      const success = document.execCommand('copy');
      document.body.removeChild(textarea);
      return success;
    }
  },

  /**
   * Download de arquivo
   */
  downloadFile(content, filename, contentType = 'text/plain') {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
};

// Gerenciador de Persistência
const Storage = {
  /**
   * Salva estado no localStorage
   */
  save(key, data) {
    try {
      localStorage.setItem(`agno:${key}`, JSON.stringify(data));
      return true;
    } catch (error) {
      console.error('Erro ao salvar no localStorage:', error);
      return false;
    }
  },

  /**
   * Carrega estado do localStorage
   */
  load(key, defaultValue = null) {
    try {
      const data = localStorage.getItem(`agno:${key}`);
      return data ? JSON.parse(data) : defaultValue;
    } catch (error) {
      console.error('Erro ao carregar do localStorage:', error);
      return defaultValue;
    }
  },

  /**
   * Remove item do localStorage
   */
  remove(key) {
    try {
      localStorage.removeItem(`agno:${key}`);
      return true;
    } catch (error) {
      console.error('Erro ao remover do localStorage:', error);
      return false;
    }
  }
};

// Gerenciador de Estados
const StateManager = {
  /**
   * Atualiza estado e persiste automaticamente
   */
  updateState(path, value) {
    const keys = path.split('.');
    let current = appState;
    
    for (let i = 0; i < keys.length - 1; i++) {
      current = current[keys[i]];
    }
    
    current[keys[keys.length - 1]] = value;
    
    // Persiste dados não sensíveis
    this.persistState();
    
    // Dispara eventos personalizados para componentes
    window.dispatchEvent(new CustomEvent('stateChange', {
      detail: { path, value, state: appState }
    }));
  },

  /**
   * Persiste estado relevante
   */
  persistState() {
    Storage.save('agentDraft', appState.agentDraft);
    Storage.save('ui', appState.ui);
    Storage.save('agents', appState.agents);
    Storage.save('apiToken', appState.apiToken);
  },

  /**
   * Carrega estado persistido
   */
  loadPersistedState() {
    appState.agentDraft = Storage.load('agentDraft', appState.agentDraft);
    appState.ui = Storage.load('ui', appState.ui);
    appState.agents = Storage.load('agents', appState.agents);
    appState.apiToken = Storage.load('apiToken', appState.apiToken);
  },

  /**
   * Reseta rascunho do agente
   */
  resetAgentDraft() {
    appState.agentDraft = {
      agent_name: '',
      instructions: '',
      specialization: '',
      tools: []
    };
    this.persistState();
  }
};

// Sistema de Logs
const Logger = {
  logs: [],
  maxLogs: 1000,
  paused: false,

  /**
   * Adiciona entrada de log
   */
  log(level, source, message) {
    if (this.paused) return;

    const entry = {
      id: Utils.generateId(),
      timestamp: new Date(),
      level: level.toUpperCase(),
      source,
      message: Utils.sanitizeHtml(message)
    };

    this.logs.unshift(entry);
    
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(0, this.maxLogs);
    }

    appState.logs = this.logs;
    
    // Atualiza console se estiver visível
    if (appState.ui.activeSection === 'page-logs') {
      this.renderLogs();
    }

    // Log também no console do navegador em desenvolvimento
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      console[level.toLowerCase()] || console.log(`[${source}] ${message}`);
    }
  },

  /**
   * Renderiza logs no console
   */
  renderLogs(filter = {}) {
    const console = document.getElementById('log-console');
    if (!console) return;

    let filteredLogs = this.logs;

    // Aplicar filtros
    if (filter.level) {
      filteredLogs = filteredLogs.filter(log => log.level === filter.level);
    }
    
    if (filter.source) {
      filteredLogs = filteredLogs.filter(log => log.source === filter.source);
    }
    
    if (filter.search) {
      const searchTerm = filter.search.toLowerCase();
      filteredLogs = filteredLogs.filter(log => 
        log.message.toLowerCase().includes(searchTerm)
      );
    }

    console.innerHTML = filteredLogs.map(log => `
      <div class="log-entry log-${log.level.toLowerCase()}" data-log-id="${log.id}">
        <span class="log-timestamp">${Utils.formatTimestamp(log.timestamp)}</span>
        <span class="log-level log-level-${log.level.toLowerCase()}">${log.level}</span>
        <span class="log-source">${log.source}</span>
        <span class="log-message">${log.message}</span>
      </div>
    `).join('');

    // Scroll para o último log
    console.scrollTop = 0;
  },

  /**
   * Pausa/retoma logs
   */
  togglePause() {
    this.paused = !this.paused;
    return this.paused;
  },

  /**
   * Limpa logs
   */
  clear() {
    this.logs = [];
    appState.logs = [];
    this.renderLogs();
  },

  /**
   * Exporta logs para arquivo
   */
  export() {
    const content = this.logs.map(log => 
      `${Utils.formatTimestamp(log.timestamp)} [${log.level}] ${log.source}: ${log.message}`
    ).join('\n');
    
    Utils.downloadFile(content, `agno-logs-${Date.now()}.txt`, 'text/plain');
  }
};

// Sistema de Toasts
const Toast = {
  container: null,
  toasts: new Map(),

  /**
   * Inicializa container de toasts
   */
  init() {
    this.container = document.getElementById('toast-container');
  },

  /**
   * Mostra toast
   */
  show(type, title, message, duration = 5000) {
    if (!this.container) return;

    const id = Utils.generateId();
    const icons = {
      success: '✅',
      warning: '⚠️',
      error: '❌',
      info: 'ℹ️'
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.innerHTML = `
      <span class="toast-icon" aria-hidden="true">${icons[type] || icons.info}</span>
      <div class="toast-content">
        <div class="toast-title">${Utils.sanitizeHtml(title)}</div>
        <div class="toast-message">${Utils.sanitizeHtml(message)}</div>
      </div>
      <button type="button" class="toast-close" aria-label="Fechar notificação">×</button>
    `;

    // Event listeners
    toast.querySelector('.toast-close').addEventListener('click', () => {
      this.hide(id);
    });

    this.container.appendChild(toast);
    this.toasts.set(id, toast);

    // Animar entrada
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });

    // Auto-dismiss
    if (duration > 0) {
      setTimeout(() => {
        this.hide(id);
      }, duration);
    }

    return id;
  },

  /**
   * Oculta toast
   */
  hide(id) {
    const toast = this.toasts.get(id);
    if (!toast) return;

    toast.classList.remove('show');
    
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
      this.toasts.delete(id);
    }, 300);
  },

  /**
   * Métodos de conveniência
   */
  success(title, message, duration) {
    return this.show('success', title, message, duration);
  },

  warning(title, message, duration) {
    return this.show('warning', title, message, duration);
  },

  error(title, message, duration) {
    return this.show('error', title, message, duration);
  },

  info(title, message, duration) {
    return this.show('info', title, message, duration);
  }
};

// Sistema de Modais
const Modal = {
  activeModal: null,
  previousFocus: null,

  /**
   * Abre modal
   */
  open(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    // Armazena foco anterior para restaurar depois
    this.previousFocus = document.activeElement;

    // Previne scroll do body
    document.body.style.overflow = 'hidden';

    // Mostra modal
    modal.classList.add('show');
    modal.setAttribute('aria-hidden', 'false');
    this.activeModal = modal;

    // Foca primeiro elemento interativo
    const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (firstFocusable) {
      firstFocusable.focus();
    }

    // Adiciona listeners
    modal.addEventListener('click', this.handleBackdropClick.bind(this));
    document.addEventListener('keydown', this.handleKeydown.bind(this));

    Logger.log('info', 'frontend', `Modal ${modalId} aberto`);
  },

  /**
   * Fecha modal
   */
  close(modal = this.activeModal) {
    if (!modal) return;

    modal.classList.remove('show');
    modal.setAttribute('aria-hidden', 'true');
    
    // Restaura scroll do body
    document.body.style.overflow = '';

    // Restaura foco
    if (this.previousFocus) {
      this.previousFocus.focus();
      this.previousFocus = null;
    }

    this.activeModal = null;

    // Remove listeners
    modal.removeEventListener('click', this.handleBackdropClick);
    document.removeEventListener('keydown', this.handleKeydown);

    Logger.log('info', 'frontend', 'Modal fechado');
  },

  /**
   * Handler para clique no backdrop
   */
  handleBackdropClick(event) {
    if (event.target.classList.contains('modal-backdrop')) {
      this.close();
    }
  },

  /**
   * Handler para teclas (ESC para fechar)
   */
  handleKeydown(event) {
    if (event.key === 'Escape') {
      this.close();
    }
  },

  /**
   * Modal de confirmação para exclusão de agente
   */
  confirmDelete(agent) {
    return new Promise((resolve) => {
      const modalId = 'modal-confirm-delete';
      let modal = document.getElementById(modalId);

      // Remove modal existente para evitar duplicação
      if (modal) {
        modal.remove();
      }

      modal = document.createElement('div');
      modal.id = modalId;
      modal.className = 'modal';
      modal.setAttribute('role', 'dialog');
      modal.setAttribute('aria-hidden', 'true');

      const warningText = agent.whatsappInstance
        ? '<p class="warning-text">Esta ação removerá também a instância WhatsApp conectada</p>'
        : '';

      modal.innerHTML = `
        <div class="modal-backdrop" aria-label="Fechar modal"></div>
        <div class="modal-content">
          <header class="modal-header">
            <h2 class="modal-title">Excluir Agente</h2>
            <button type="button" class="modal-close" aria-label="Fechar modal">✕</button>
          </header>
          <div class="modal-body">
            <p>Tem certeza que deseja excluir <strong>${Utils.sanitizeHtml(agent.agent_name)}</strong>?</p>
            ${warningText}
            <div class="form-group">
              <div class="input-wrapper">
                <input type="text" id="confirm-agent-name" class="form-input" />
                <label for="confirm-agent-name" class="form-label">Digite o nome do agente</label>
              </div>
            </div>
          </div>
          <footer class="modal-footer">
            <button type="button" class="button button-secondary" data-action="cancel">Cancelar</button>
            <button type="button" class="button button-danger" data-action="confirm" disabled>Excluir</button>
          </footer>
        </div>
      `;

      document.body.appendChild(modal);

      const input = modal.querySelector('#confirm-agent-name');
      const confirmBtn = modal.querySelector('[data-action="confirm"]');
      const cancelBtn = modal.querySelector('[data-action="cancel"]');
      const closeBtn = modal.querySelector('.modal-close');

      const cleanup = () => {
        this.close(modal);
        modal.remove();
      };

      input.addEventListener('input', () => {
        confirmBtn.disabled = input.value !== agent.agent_name;
      });

      cancelBtn.addEventListener('click', () => {
        cleanup();
        resolve(false);
      });

      closeBtn.addEventListener('click', () => {
        cleanup();
        resolve(false);
      });

      confirmBtn.addEventListener('click', () => {
        cleanup();
        resolve(true);
      });

      this.open(modalId);
    });
  }
};

// Validador de Formulários
const Validator = {
  rules: {
    agent_name: {
      required: true,
      minLength: 3,
      maxLength: 40,
      pattern: /^[a-zA-Z0-9_-]+$/,
      message: 'Nome deve ter 3-40 caracteres, apenas letras, números, hífen e underscore'
    },
    instructions: {
      required: true,
      minLength: 80,
      message: 'Instruções devem ter pelo menos 80 caracteres'
    },
    specialization: {
      required: true,
      message: 'Selecione uma especialização'
    },
    tools: {
      required: true,
      minItems: 1,
      message: 'Selecione pelo menos uma integração'
    },
    whatsapp_api_url: {
      required: true,
      pattern: /^https?:\/\//,
      message: 'URL da API inválida',
      dependsOn: 'whatsapp'
    },
    whatsapp_api_key: {
      required: true,
      minLength: 10,
      message: 'API key deve ter pelo menos 10 caracteres',
      dependsOn: 'whatsapp'
    },
    whatsapp_phone: {
      required: true,
      pattern: /^\+?[1-9]\d{7,14}$/,
      message: 'Telefone inválido',
      dependsOn: 'whatsapp'
    },
    email_smtp_server: {
      required: true,
      pattern: /^https?:\/\//,
      message: 'Servidor SMTP inválido',
      dependsOn: 'email'
    },
    email_port: {
      required: true,
      pattern: /^\d+$/,
      message: 'Porta inválida',
      dependsOn: 'email'
    },
    email_from: {
      required: true,
      pattern: /^[^@\s]+@[^@\s]+\.[^@\s]+$/,
      message: 'E-mail inválido',
      dependsOn: 'email'
    }
  },

  /**
   * Valida campo individual
   */
  validateField(name, value) {
    const rule = this.rules[name];
    if (!rule) return { valid: true };

    if (rule.dependsOn) {
      const tools = FormManager ? FormManager.getFieldValue('tools') : [];
      if (!tools.includes(rule.dependsOn)) {
        return { valid: true };
      }
    }

    const errors = [];

    // Required
    if (rule.required && (!value || (Array.isArray(value) && value.length === 0))) {
      errors.push('Este campo é obrigatório');
    }

    // Se valor está vazio e não é obrigatório, passa
    if (!value && !rule.required) {
      return { valid: true };
    }

    // MinLength
    if (rule.minLength && value.length < rule.minLength) {
      errors.push(`Mínimo de ${rule.minLength} caracteres`);
    }

    // MaxLength
    if (rule.maxLength && value.length > rule.maxLength) {
      errors.push(`Máximo de ${rule.maxLength} caracteres`);
    }

    // Pattern
    if (rule.pattern && !rule.pattern.test(value)) {
      errors.push(rule.message || 'Formato inválido');
    }

    // MinItems (para arrays)
    if (rule.minItems && Array.isArray(value) && value.length < rule.minItems) {
      errors.push(`Selecione pelo menos ${rule.minItems} item(s)`);
    }

    return {
      valid: errors.length === 0,
      errors,
      message: rule.message || errors[0]
    };
  },

  /**
   * Valida formulário completo
   */
  validateForm(data) {
    const results = {};
    let isValid = true;

    for (const [field, value] of Object.entries(data)) {
      const result = this.validateField(field, value);
      results[field] = result;
      if (!result.valid) {
        isValid = false;
      }
    }

    return { valid: isValid, fields: results };
  },

  /**
   * Mostra erro no campo
   */
  showFieldError(fieldName, message) {
    const field = document.querySelector(`[name="${fieldName}"]`);
    const errorElement = document.getElementById(`${fieldName}_error`);
    
    if (field) {
      field.classList.add('error');
      field.setAttribute('aria-invalid', 'true');
    }
    
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.classList.add('show');
    }
  },

  /**
   * Limpa erro do campo
   */
  clearFieldError(fieldName) {
    const field = document.querySelector(`[name="${fieldName}"]`);
    const errorElement = document.getElementById(`${fieldName}_error`);
    
    if (field) {
      field.classList.remove('error');
      field.setAttribute('aria-invalid', 'false');
    }
    
    if (errorElement) {
      errorElement.textContent = '';
      errorElement.classList.remove('show');
    }
  }
};

// Cliente da API
const ApiClient = {
  /**
   * Retorna headers de autenticação
   */
  getAuthHeaders() {
    const token = appState.apiToken || Storage.load('apiToken');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  },

  /**
   * Verifica erros de autenticação
   */
  checkAuth(response) {
    if (response.status === 401) {
      Navigation.switchSection('page-settings');
      Toast.warning('Autenticação Necessária', 'Informe seu token de acesso nas Configurações.');
      throw new Error('Não autenticado');
    }
  },

  /**
   * Requisição base
   */
  async request(endpoint, options = {}) {
    const url = `${window.API_BASE}${endpoint}`;
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
        ...(options.headers || {})
      }
    };

    try {
      Logger.log('info', 'api', `${config.method || 'GET'} ${endpoint}`);

      const response = await fetch(url, config);
      this.checkAuth(response);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }

      Logger.log('info', 'api', `Sucesso: ${endpoint}`);
      return data;
    } catch (error) {
      Logger.log('error', 'api', `Erro em ${endpoint}: ${error.message}`);
      throw error;
    }
  },

  /**
   * Gera código do agente
   */
  async generateAgent(agentData) {
    return this.request('/api/agents/generate', {
      method: 'POST',
      body: JSON.stringify(agentData)
    });
  },

  /**
   * Materializa agente no servidor
   */
  async materializeAgent(agentData) {
    return this.request('/api/agents/materialize', {
      method: 'POST',
      body: JSON.stringify(agentData)
    });
  },

  /**
   * Obtém dados de um agente específico
   */
  async getAgent(agentId) {
    return this.request(`/api/agents/${agentId}`);
  },

  /**
   * Atualiza agente existente
   */
  async updateAgent(agentId, agentData) {
    return this.request(`/api/agents/${agentId}`, {
      method: 'PUT',
      body: JSON.stringify(agentData)
    });
  },

  /**
   * Remove agente existente
   */
  async deleteAgent(agentId) {
    return this.request(`/api/agents/${agentId}`, {
      method: 'DELETE'
    });
  },

  /**
   * Lista todos os agentes
   */
  async listAgents() {
    return this.request('/api/agents');
  },

  /**
   * Cria instância do WhatsApp
   */
  async createWhatsAppInstance(instanceData) {
    return this.request('/api/wpp/instances', {
      method: 'POST',
      body: JSON.stringify(instanceData)
    });
  },

  /**
   * Obtém QR Code
   */
  async getQRCode(instanceId) {
    return this.request(`/api/wpp/instances/${instanceId}/qr`);
  },

  /**
   * Obtém status da instância
   */
  async getInstanceStatus(instanceId) {
    return this.request(`/api/wpp/instances/${instanceId}/status`);
  },

  /**
   * Envia mensagem de teste
   */
  async sendTestMessage(messageData) {
    return this.request('/api/wpp/messages', {
      method: 'POST',
      body: JSON.stringify(messageData)
    });
  },

  /**
   * Testa conexão com API
   */
  async testConnection() {
    return this.request('/api/health');
  }
};

// Navegação entre seções
const Navigation = {
  /**
   * Muda seção ativa
   */
  switchSection(sectionId) {
    // Remove ativo de todas as seções e tabs
    document.querySelectorAll('.page-section').forEach(section => {
      section.classList.remove('active');
    });
    
    document.querySelectorAll('.tab-button').forEach(button => {
      button.classList.remove('active');
      button.setAttribute('aria-pressed', 'false');
    });

    // Ativa seção e tab
    const section = document.getElementById(sectionId);
    const tab = document.querySelector(`[data-section="${sectionId}"]`);
    
    if (section) {
      section.classList.add('active');
    }
    
    if (tab) {
      tab.classList.add('active');
      tab.setAttribute('aria-pressed', 'true');
    }

    // Atualiza estado
    StateManager.updateState('ui.activeSection', sectionId);
    
    // Logs específicos da seção
    if (sectionId === 'page-logs') {
      Logger.renderLogs();
    }
    
    if (sectionId === 'page-agents') {
      AgentManager.renderAgents();
    }

    Logger.log('info', 'frontend', `Navegação para ${sectionId}`);
  },

  /**
   * Inicializa navegação
   */
  init() {
    document.querySelectorAll('.tab-button').forEach(button => {
      button.addEventListener('click', (e) => {
        const sectionId = button.getAttribute('data-section');
        if (sectionId) {
          this.switchSection(sectionId);
        }
      });
    });

    // Seção inicial
    this.switchSection(appState.ui.activeSection);
  }
};

// Gerenciador de Agentes
const AgentManager = {
  editingAgentId: null,
  currentAgentId: null,
  pollingId: null,
  offlineNotified: false,

  /**
   * Busca lista de agentes da API ou localStorage
   */
  async fetchAgents() {
    try {
      const agents = await ApiClient.listAgents();
      StateManager.updateState('agents', agents);
      this.offlineNotified = false;
    } catch (error) {
      const cached = Storage.load('agents', []);
      StateManager.updateState('agents', cached);
      if (!this.offlineNotified) {
        Toast.warning('Modo Offline', 'Usando agentes salvos localmente');
        this.offlineNotified = true;
      }
    }
    this.renderAgents();
  },

  /**
   * Inicia polling periódico para sincronização
   */
  startPolling(interval = 30000) {
    this.fetchAgents();
    this.pollingId = setInterval(() => this.fetchAgents(), interval);
  },

  /**
   * Interrompe polling
   */
  stopPolling() {
    if (this.pollingId) {
      clearInterval(this.pollingId);
      this.pollingId = null;
    }
  },

  /**
   * Renderiza lista de agentes
   */
  renderAgents() {
    const grid = document.getElementById('agents-grid');
    if (!grid) return;

    const agents = appState.agents;

    if (agents.length === 0) {
      // Mostra exemplos mockados
      grid.innerHTML = this.getMockAgents();
    } else {
      grid.innerHTML = agents.map(agent => this.renderAgentCard(agent)).join('');
    }
  },

  /**
   * Renderiza card de agente
   */
  renderAgentCard(agent) {
    const toolsHtml = agent.tools.map(tool => 
      `<span class="tool-tag">${tool}</span>`
    ).join('');

    const statusBadge = this.getStatusBadge(agent.status || 'DESCONHECIDO');

    return `
      <div class="agent-card" data-agent-id="${agent.id}">
        <div class="agent-card-header">
          <div>
            <h3 class="agent-card-title">${Utils.sanitizeHtml(agent.agent_name)}</h3>
            <p class="agent-card-spec">${Utils.sanitizeHtml(agent.specialization)}</p>
          </div>
          ${statusBadge}
        </div>
        <div class="agent-card-body">
          <div class="agent-tools">
            ${toolsHtml}
          </div>
        </div>
        <div class="agent-card-actions">
          <button type="button" class="button button-small" onclick="AgentManager.viewAgent('${agent.id}')">
            Detalhes
          </button>
          <button type="button" class="button button-small" onclick="AgentManager.previewAgent('${agent.id}')">
            Pré-visualizar
          </button>
          <button type="button" class="button button-small" onclick="AgentManager.copyCode('${agent.id}')">
            Copiar Código
          </button>
          <button type="button" class="button button-small" onclick="AgentManager.downloadZip('${agent.id}')">
            Baixar ZIP
          </button>
          <button type="button" class="button button-small button-accent" onclick="AgentManager.connectWhatsApp('${agent.id}')">
            Conectar WhatsApp
          </button>
          <button type="button" class="button button-small" onclick="AgentManager.editAgent('${agent.id}')">
            Editar
          </button>
          <button type="button" class="button button-small button-danger" onclick="AgentManager.deleteAgent('${agent.id}')">
            Excluir
          </button>
        </div>
      </div>
    `;
  },

  /**
   * Agentes mockados para demonstração
   */
  getMockAgents() {
    const mockAgents = [
      {
        id: 'mock-1',
        agent_name: 'atendimento-bot',
        specialization: 'Atendimento',
        tools: ['WhatsApp', 'E-mail'],
        status: 'CONECTADO'
      },
      {
        id: 'mock-2',
        agent_name: 'vendas-assistant',
        specialization: 'Vendas',
        tools: ['WhatsApp', 'CRM', 'Pagamentos'],
        status: 'QR_ABERTO'
      },
      {
        id: 'mock-3',
        agent_name: 'agendamento-bot',
        specialization: 'Agendamento',
        tools: ['WhatsApp', 'Google Calendar'],
        status: 'DESCONHECIDO'
      }
    ];

    return mockAgents.map(agent => this.renderAgentCard(agent)).join('');
  },

  /**
   * Badge de status
   */
  getStatusBadge(status) {
    const badges = {
      CONECTADO: '<span class="badge badge-success">✓ Conectado</span>',
      QR_ABERTO: '<span class="badge badge-warning">📱 QR Aberto</span>',
      CONECTANDO: '<span class="badge badge-warning">⏳ Conectando</span>',
      DESCONHECIDO: '<span class="badge badge-error">❓ Desconhecido</span>'
    };
    
    return badges[status] || badges.DESCONHECIDO;
  },

  /**
   * Exibe detalhes do agente
   */
  async viewAgent(agentId) {
    try {
      const agent = await ApiClient.getAgent(agentId);
      this.currentAgentId = agentId;

      const nameInput = document.getElementById('detail-agent-name');
      const instructionsInput = document.getElementById('detail-agent-instructions');
      const toolsContainer = document.getElementById('detail-agent-tools');
      const statsContainer = document.getElementById('detail-agent-stats');

      if (nameInput) nameInput.value = agent.name || '';
      if (instructionsInput) instructionsInput.value = agent.instructions || '';
      if (toolsContainer) {
        toolsContainer.innerHTML = (agent.tools || []).map(t => `<span class="tool-tag">${t}</span>`).join('');
      }
      if (statsContainer) {
        statsContainer.innerHTML = `
          <p>Mensagens processadas: ${agent.messages_processed || 0}</p>
          <p>Uptime: ${agent.uptime_seconds || 0}s</p>
          <p>Erros: ${agent.error_count || 0}</p>
        `;
      }

      Navigation.switchSection('page-agent-detail');
    } catch (error) {
      Toast.error('Erro', error.message || 'Não foi possível carregar o agente');
    }
  },

  /**
   * Pré-visualiza agente (simulado)
   */
  previewAgent(agentId) {
    const mockFiles = {
      'main.py': '# Arquivo principal do agente\nfrom agno import Agent\n\n# Código mockado para demonstração',
      'agent.py': '# Definição do agente\nclass MyAgent:\n    def __init__(self):\n        pass',
      'services/evolution.py': '# Integração Evolution API\nimport requests\n\nclass EvolutionService:\n    def __init__(self):\n        pass'
    };

    document.getElementById('json-preview').innerHTML = `<code>${JSON.stringify(mockFiles, null, 2)}</code>`;
    Modal.open('modal-preview-json');
    
    Toast.info('Pré-visualização', 'Código mockado para demonstração');
  },

  /**
   * Copia código do agente
   */
  async copyCode(agentId) {
    const success = await Utils.copyToClipboard('# Código do agente mockado\nprint("Hello World")');
    if (success) {
      Toast.success('Copiado!', 'Código copiado para a área de transferência');
    } else {
      Toast.error('Erro', 'Não foi possível copiar o código');
    }
  },

  /**
   * Download ZIP do agente
   */
  downloadZip(agentId) {
    // Simulação de download
    Utils.downloadFile('# Conteúdo mockado do ZIP\nprint("Agent files")', `agent-${agentId}.zip`);
    Toast.success('Download iniciado', 'ZIP do agente baixado com sucesso');
  },

  /**
   * Abre modal de edição de agente
   */
  editAgent(agentId) {
    const agent = appState.agents.find(a => a.id === agentId);
    if (!agent) {
      Toast.error('Editar', 'Agente não encontrado');
      return;
    }

    this.editingAgentId = agentId;
    const form = document.getElementById('edit-agent-form');
    if (!form) return;

    form.querySelector('#edit-agent-id').value = agentId;
    form.querySelector('#edit-agent_name').value = agent.agent_name || '';
    form.querySelector('#edit-instructions').value = agent.instructions || '';
    form.querySelector('#edit-specialization').value = agent.specialization || '';
    form.querySelectorAll('input[name="tools"]').forEach(input => {
      input.checked = agent.tools.includes(input.value);
    });

    Modal.open('modal-edit-agent');
  },

  /**
   * Salva alterações do agente
   */
  async saveAgent(agentData = null) {
    try {
      if (!agentData) {
        const form = document.getElementById('edit-agent-form');
        if (!form) return;
        const tools = Array.from(form.querySelectorAll('input[name="tools"]:checked')).map(i => i.value);
        agentData = {
          id: this.editingAgentId,
          agent_name: form.querySelector('#edit-agent_name').value.trim(),
          instructions: form.querySelector('#edit-instructions').value.trim(),
          specialization: form.querySelector('#edit-specialization').value,
          tools
        };
      }

      const updatedAgent = await ApiClient.updateAgent(agentData.id, agentData);
      const agents = appState.agents.map(a => a.id === updatedAgent.id ? updatedAgent : a);
      StateManager.updateState('agents', agents);
      this.renderAgents();
      Modal.close();
      this.editingAgentId = null;
      Toast.success('Agente atualizado', 'As alterações foram salvas');
      Logger.log('info', 'frontend', `Agente atualizado: ${updatedAgent.id}`);
    } catch (error) {
      Toast.error('Erro', error.message || 'Não foi possível salvar o agente');
    }
  },

  /**
   * Conecta com WhatsApp via Evolution API
  */
  async connectWhatsApp(agentId) {
    try {
      const agent = appState.agents.find(a => a.id === agentId);
      if (!agent) {
        Toast.error('WhatsApp', 'Agente não encontrado');
        return;
      }

      const instanceName = Utils.slugify(agent.agent_name);

      // Abre modal de QR Code
      Modal.open('modal-qr');

      const qrDisplay = document.getElementById('qr-display');
      qrDisplay.innerHTML = `
        <div class="loading-spinner"></div>
        <p class="qr-label">Criando instância WhatsApp...</p>
      `;

      Toast.info('WhatsApp', 'Iniciando conexão com WhatsApp...');

      // Cria instância WhatsApp
      agent.whatsappInstance = instanceName;
      StateManager.persistState();
      await this.createWhatsAppInstance(instanceName);
      
      // Obtém QR Code
      const qrCode = await this.getQRCode(instanceName);
      
      if (qrCode) {
        qrDisplay.innerHTML = `
          <div class="qr-code-container">
            <img src="data:image/png;base64,${qrCode}" alt="QR Code WhatsApp" class="qr-code-image"/>
          </div>
          <p class="qr-label">Escaneie com WhatsApp para conectar</p>
          <div class="qr-status" id="qr-status">Aguardando escaneamento...</div>
        `;
        
        // Monitora status da conexão
        this.monitorConnectionStatus(instanceName);
        
        Toast.success('WhatsApp', 'QR Code gerado! Escaneie com seu WhatsApp.');
      } else {
        throw new Error('Falha ao obter QR Code');
      }
      
    } catch (error) {
      Logger.log('error', 'whatsapp', `Erro ao conectar WhatsApp: ${error.message}`);
      
      const qrDisplay = document.getElementById('qr-display');
      qrDisplay.innerHTML = `
        <div class="error-message">
          <span class="error-icon">❌</span>
          <p>Erro ao conectar: ${error.message}</p>
          <button onclick="AgentManager.connectWhatsApp('${agentId}')" class="button button-small">
            Tentar Novamente
          </button>
        </div>
      `;
      
      Toast.error('WhatsApp', `Erro: ${error.message}`);
    }
  },

  /**
   * Cria instância WhatsApp na Evolution API
   */
  async createWhatsAppInstance(instanceName) {
    const maxAttempts = 2;
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const data = await ApiClient.request('/api/wpp/instances', {
          method: 'POST',
          body: JSON.stringify({
            instance_name: instanceName,
            webhook_url: `${window.API_BASE}/api/wpp/webhook`,
            events: ['messages.upsert', 'connection.update']
          })
        });

        Logger.log('info', 'whatsapp', `Instância ${instanceName} criada com sucesso`);

        if (data.status === 'recreated') {
          Toast.info('WhatsApp', 'Instância existente corrigida.');
        }

        return data;
      } catch (error) {
        Logger.log('error', 'whatsapp', `Erro ao criar instância: ${error.message}`);
        if (attempt === maxAttempts) {
          Toast.error('WhatsApp', 'Falha ao criar instância. Tente repetir a conexão.');
          throw error;
        }
      }
    }
  },

  /**
   * Obtém QR Code da instância
   */
  async getQRCode(instanceName) {
    try {
      const { qr } = await ApiClient.request(`/api/wpp/instances/${instanceName}/qr`);

      if (qr) {
        return qr;
      } else {
        throw new Error('QR Code não disponível');
      }

    } catch (error) {
      Logger.log('error', 'whatsapp', `Erro ao obter QR Code: ${error.message}`);
      throw error;
    }
  },

  /**
   * Monitora status da conexão WhatsApp
   */
  async monitorConnectionStatus(instanceName) {
    const statusElement = document.getElementById('qr-status');
    let attempts = 0;
    const maxAttempts = 30; // 5 minutos (10s * 30)

    const checkStatus = async () => {
      try {
        const response = await fetch(`${window.API_BASE}/api/wpp/instances/${instanceName}/status`, {
          headers: ApiClient.getAuthHeaders()
        });
        ApiClient.checkAuth(response);

        if (response.ok) {
          const data = await response.json();
          const state = data.state;
          
          if (statusElement) {
            statusElement.textContent = this.getConnectionStatusText(state);
          }

          if (state === 'open' || state === 'connected') {
            appState.evolutionAPI.connected = true;
            Toast.success('WhatsApp', 'WhatsApp conectado com sucesso!');

            // Configura webhook
            await this.setupWebhook(instanceName);
            // Verifica se o webhook foi configurado corretamente
            const safeName = encodeURIComponent(instanceName);
            try {
              const statusResponse = await fetch(`${window.API_BASE}/api/wpp/instances/${safeName}/status`, {
                headers: ApiClient.getAuthHeaders()
              });
              ApiClient.checkAuth(statusResponse);
              const statusData = await statusResponse.json().catch(() => ({}));
              const statusOk = statusResponse.ok &&
                statusData.status === 'success' &&
                (statusData.state === 'open' || statusData.state === 'connected');
              if (!statusOk) {
                Logger.log('warning', 'whatsapp', JSON.stringify({ action: 'verify_status', success: false, httpStatus: statusResponse.status }));
                Toast.warning('WhatsApp', 'Não foi possível confirmar o status da conexão.');
              }

              const webhookResponse = await fetch(`${window.API_BASE}/api/wpp/instances/${safeName}/webhook`, {
                headers: ApiClient.getAuthHeaders()
              });
              ApiClient.checkAuth(webhookResponse);
              const webhookData = await webhookResponse.json().catch(() => ({}));
              const webhookOk = webhookResponse.ok && webhookData.status === 'success';
              if (!webhookOk) {
                Logger.log('warning', 'whatsapp', JSON.stringify({ action: 'verify_webhook', success: false, httpStatus: webhookResponse.status }));
                Toast.warning('WhatsApp', 'Webhook não confirmado.');
              }

              if (statusOk && webhookOk) {
                Logger.log('info', 'whatsapp', JSON.stringify({ action: 'post_setup_verification', success: true }));
                // Atualiza UI
                this.updateAgentStatus(instanceName, 'CONECTADO');
              }
            } catch (verifyError) {
              Logger.log('error', 'whatsapp', JSON.stringify({ action: 'post_setup_verification', success: false, error: verifyError.message }));
              Toast.error('WhatsApp', 'Erro ao verificar conexão após configuração do webhook.');
            }
            return;
          }
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(checkStatus, 10000); // Verifica a cada 10 segundos
        } else {
          if (statusElement) {
            statusElement.textContent = 'Timeout - QR Code expirado';
          }
          Toast.warning('WhatsApp', 'QR Code expirado. Tente novamente.');
        }

      } catch (error) {
        Logger.log('error', 'whatsapp', `Erro ao verificar status: ${error.message}`);
      }
    };

    // Inicia monitoramento
    setTimeout(checkStatus, 5000); // Primeira verificação em 5s
  },

  /**
   * Configura webhook para receber mensagens
   */
  async setupWebhook(instanceName) {
    try {
      const safeName = encodeURIComponent(instanceName);
      const webhookUrl = `${window.API_BASE}/api/wpp/webhook/${safeName}`;

      const response = await fetch(`${window.API_BASE}/api/wpp/instances/${safeName}/webhook`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...ApiClient.getAuthHeaders()
        },
        body: JSON.stringify({
          webhook_url: webhookUrl,
          events: ['messages.upsert', 'connection.update']
        })
      });
      ApiClient.checkAuth(response);
      const data = await response.json().catch(() => ({}));

      if (response.ok && data.status === 'success') {
        Logger.log('info', 'whatsapp', `Webhook configurado: ${webhookUrl}`);
        Toast.success('WhatsApp', data.message || 'Webhook configurado com sucesso!');
      } else {
        const errorMessage = data.message || 'Falha ao configurar webhook';
        Logger.log('warning', 'whatsapp', errorMessage);
        Toast.error('WhatsApp', errorMessage);
      }
    } catch (error) {
      Logger.log('error', 'whatsapp', `Erro ao configurar webhook: ${error.message}`);
      Toast.error('WhatsApp', `Erro ao configurar webhook: ${error.message}`);
    }
  },

  /**
   * Converte status da conexão para texto amigável
   */
  getConnectionStatusText(state) {
    const statusMap = {
      'close': 'Desconectado',
      'connecting': 'Conectando...',
      'open': 'Conectado',
      'connected': 'Conectado',
      'pairing': 'Pareando...',
      'timeout': 'Tempo esgotado'
    };
    
    return statusMap[state] || `Status: ${state}`;
  },

  /**
   * Atualiza status do agente na UI
   */
  updateAgentStatus(instanceName, status) {
    const agent = appState.agents.find(a => Utils.slugify(a.agent_name) === instanceName);
    if (!agent) return;

    const card = document.querySelector(`.agent-card[data-agent-id="${agent.id}"]`);
    if (card) {
      const statusBadge = card.querySelector('.status-badge');
      if (statusBadge) {
        statusBadge.textContent = status;
        statusBadge.className = `status-badge ${status === 'CONECTADO' ? 'status-success' : 'status-warning'}`;
      }
    }
  },

  /**
   * Exclui agente
   */
  async deleteAgent(agentId) {
    const agent = appState.agents.find(a => a.id === agentId);
    if (!agent) return;

    const confirmed = await Modal.confirmDelete(agent);
    if (!confirmed) return;

    try {
      await ApiClient.deleteAgent(agentId);
      const updated = appState.agents.filter(a => a.id !== agentId);
      StateManager.updateState('agents', updated);
      this.renderAgents();
      Toast.success('Excluído', 'Agente removido com sucesso');
      Logger.log('info', 'frontend', `Agente removido: ${agentId}`);
    } catch (error) {
      Toast.error('Erro', error.message || 'Não foi possível excluir o agente');
    }
  }
};

// Gerenciador do Formulário Principal
const FormManager = {
  form: null,

  /**
   * Inicializa formulário
   */
  init() {
    this.form = document.getElementById('agent-form');
    if (!this.form) return;

    this.setupValidation();
    this.setupActions();
    this.setupCharCounter();
    this.loadDraft();
    this.toggleIntegrationFields();
  },

  /**
   * Configura validação em tempo real
   */
  setupValidation() {
    const fields = ['agent_name', 'instructions', 'specialization', 'whatsapp_api_url', 'whatsapp_api_key', 'whatsapp_phone', 'email_smtp_server', 'email_port', 'email_from'];
    
    fields.forEach(fieldName => {
      const field = document.querySelector(`[name="${fieldName}"]`);
      if (field) {
        const debouncedValidation = Utils.debounce(() => {
          this.validateField(fieldName);
        }, 300);
        
        field.addEventListener('input', debouncedValidation);
        field.addEventListener('blur', () => this.validateField(fieldName));
      }
    });

    // Validação das tools (checkboxes)
    document.querySelectorAll('[name="tools"]').forEach(checkbox => {
      checkbox.addEventListener('change', () => {
        this.validateField('tools');
        this.toggleIntegrationFields();
      });
    });
  },

  /**
   * Configura ações dos botões
   */
  setupActions() {
    // Preview do esquema
    document.getElementById('btn-preview-agent-schema')?.addEventListener('click', () => {
      this.previewSchema();
    });

    // Salvar rascunho
    document.getElementById('btn-save-draft')?.addEventListener('click', () => {
      this.saveDraft();
    });

    // Submit do formulário
    this.form.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleSubmit();
    });
  },

  /**
   * Configura contador de caracteres
   */
  setupCharCounter() {
    const instructionsField = document.getElementById('instructions');
    const counter = document.getElementById('instructions_count');
    
    if (instructionsField && counter) {
      instructionsField.addEventListener('input', () => {
        const length = instructionsField.value.length;
        const currentCount = counter.querySelector('.current-count');
        
        if (currentCount) {
          currentCount.textContent = length;
          
          // Atualiza classes do contador
          counter.classList.remove('warning', 'error');
          if (length < 80) {
            counter.classList.add(length < 40 ? 'error' : 'warning');
          }
        }
      });
    }
  },

  toggleIntegrationFields() {
    const tools = this.getFieldValue('tools');
    const wpp = document.getElementById('whatsapp-config');
    if (wpp) {
      wpp.style.display = tools.includes('whatsapp') ? 'block' : 'none';
    }
    const email = document.getElementById('email-config');
    if (email) {
      email.style.display = tools.includes('email') ? 'block' : 'none';
    }
  },

  /**
   * Valida campo individual
   */
  validateField(fieldName) {
    const value = this.getFieldValue(fieldName);
    const result = Validator.validateField(fieldName, value);
    
    if (result.valid) {
      Validator.clearFieldError(fieldName);
    } else {
      Validator.showFieldError(fieldName, result.message);
    }
    
    return result.valid;
  },

  /**
   * Obtém valor do campo
   */
  getFieldValue(fieldName) {
    if (fieldName === 'tools') {
      return Array.from(document.querySelectorAll('[name="tools"]:checked'))
        .map(checkbox => checkbox.value);
    }
    
    const field = document.querySelector(`[name="${fieldName}"]`);
    return field ? field.value.trim() : '';
  },

  /**
   * Obtém dados do formulário
   */
  getFormData() {
    return {
      agent_name: this.getFieldValue('agent_name'),
      instructions: this.getFieldValue('instructions'),
      specialization: this.getFieldValue('specialization'),
      tools: this.getFieldValue('tools'),
      whatsapp_api_url: this.getFieldValue('whatsapp_api_url'),
      whatsapp_api_key: this.getFieldValue('whatsapp_api_key'),
      whatsapp_phone: this.getFieldValue('whatsapp_phone'),
      email_smtp_server: this.getFieldValue('email_smtp_server'),
      email_port: this.getFieldValue('email_port'),
      email_from: this.getFieldValue('email_from')
    };
  },

  buildPayload(data) {
    const payload = {
      agent_name: data.agent_name,
      instructions: data.instructions,
      specialization: data.specialization,
      tools: data.tools,
      integrations: {}
    };

    if (data.tools.includes('whatsapp')) {
      payload.integrations.whatsapp = {
        api_url: data.whatsapp_api_url,
        api_key: data.whatsapp_api_key,
        phone_number: data.whatsapp_phone
      };
    }
    if (data.tools.includes('email')) {
      payload.integrations.email = {
        smtp_server: data.email_smtp_server,
        smtp_port: Number(data.email_port),
        from_email: data.email_from
      };
    }

    return payload;
  },

  /**
   * Carrega rascunho salvo
   */
  loadDraft() {
    const draft = appState.agentDraft;
    
    // Carrega valores nos campos
    document.querySelector('[name="agent_name"]').value = draft.agent_name || '';
    document.querySelector('[name="instructions"]').value = draft.instructions || '';
    document.querySelector('[name="specialization"]').value = draft.specialization || '';

    // Carrega tools selecionadas
    document.querySelectorAll('[name="tools"]').forEach(checkbox => {
      checkbox.checked = draft.tools.includes(checkbox.value);
    });

    // Carrega configurações de integração
    document.querySelector('[name="whatsapp_api_url"]').value = draft.integrations?.whatsapp?.api_url || '';
    document.querySelector('[name="whatsapp_api_key"]').value = draft.integrations?.whatsapp?.api_key || '';
    document.querySelector('[name="whatsapp_phone"]').value = draft.integrations?.whatsapp?.phone_number || '';
    document.querySelector('[name="email_smtp_server"]').value = draft.integrations?.email?.smtp_server || '';
    document.querySelector('[name="email_port"]').value = draft.integrations?.email?.smtp_port || '';
    document.querySelector('[name="email_from"]').value = draft.integrations?.email?.from_email || '';
    
    // Atualiza contador de caracteres
    const instructionsField = document.getElementById('instructions');
    if (instructionsField) {
      instructionsField.dispatchEvent(new Event('input'));
    }

    this.toggleIntegrationFields();
  },

  /**
   * Salva rascunho
   */
  saveDraft() {
    const data = this.getFormData();
    const payload = this.buildPayload(data);
    StateManager.updateState('agentDraft', payload);
    Toast.success('Rascunho Salvo', 'Seus dados foram salvos localmente');
    Logger.log('info', 'frontend', 'Rascunho salvo no localStorage');
  },

  /**
   * Preview do esquema JSON
   */
  previewSchema() {
    const data = this.buildPayload(this.getFormData());
    const jsonPreview = document.getElementById('json-preview');
    
    if (jsonPreview) {
      jsonPreview.innerHTML = `<code>${JSON.stringify(data, null, 2)}</code>`;
      Modal.open('modal-preview-json');
    }
  },

  /**
   * Manipula submit do formulário
   */
  async handleSubmit() {
    const data = this.getFormData();
    const validation = Validator.validateForm(data);

    if (!validation.valid) {
      // Mostra erros de validação
      for (const [field, result] of Object.entries(validation.fields)) {
        if (!result.valid) {
          Validator.showFieldError(field, result.message);
        }
      }

      Toast.error('Formulário Inválido', 'Corrija os erros antes de continuar');
      return;
    }

    const payload = this.buildPayload(data);

    // Salva dados e continua
    StateManager.updateState('agentDraft', payload);
    this.showCodeGeneration();

    Toast.success('Dados Válidos', 'Agora você pode gerar o código');
  },

  /**
   * Mostra seção de geração de código
   */
  showCodeGeneration() {
    const codeCard = document.getElementById('code-generation-card');
    const summaryContent = document.getElementById('agent-summary-content');
    
    if (codeCard) {
      codeCard.style.display = 'block';
      codeCard.scrollIntoView({ behavior: 'smooth' });
    }
    
    if (summaryContent) {
      const data = appState.agentDraft;
      summaryContent.innerHTML = `
        <div style="margin-bottom: 16px;">
          <strong>Nome:</strong> ${Utils.sanitizeHtml(data.agent_name)}<br>
          <strong>Especialização:</strong> ${Utils.sanitizeHtml(data.specialization)}<br>
          <strong>Tools:</strong> ${data.tools.join(', ')}
        </div>
        <div>
          <strong>Instruções:</strong><br>
          <div style="background: var(--bg); padding: 12px; border-radius: 8px; margin-top: 8px; font-size: 12px;">
            ${Utils.sanitizeHtml(data.instructions).substring(0, 200)}...
          </div>
        </div>
      `;
    }
  }
};

// Gerenciador de Geração de Código
const CodeGenerator = {
  currentFiles: {},
  activeFile: 'main.py',

  /**
   * Inicializa gerador de código
   */
  init() {
    this.setupTabs();
    this.setupActions();
  },

  /**
   * Configura tabs do editor
   */
  setupTabs() {
    document.querySelectorAll('.editor-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const fileName = tab.getAttribute('data-file');
        if (fileName) {
          this.switchFile(fileName);
        }
      });
    });
  },

  /**
   * Configura ações
   */
  setupActions() {
    // Gerar código
    document.getElementById('btn-generate-code')?.addEventListener('click', () => {
      this.generateCode();
    });

    // Copiar código
    document.getElementById('btn-copy-code')?.addEventListener('click', () => {
      this.copyCurrentCode();
    });

    // Download ZIP
    document.getElementById('btn-download-zip')?.addEventListener('click', () => {
      this.downloadZip();
    });

    // Materializar no servidor
    document.getElementById('btn-materialize-server')?.addEventListener('click', () => {
      this.materializeOnServer();
    });
  },

  /**
   * Troca arquivo ativo no editor
   */
  switchFile(fileName) {
    // Atualiza tabs
    document.querySelectorAll('.editor-tab').forEach(tab => {
      tab.classList.remove('active');
      tab.setAttribute('aria-selected', 'false');
    });
    
    const activeTab = document.querySelector(`[data-file="${fileName}"]`);
    if (activeTab) {
      activeTab.classList.add('active');
      activeTab.setAttribute('aria-selected', 'true');
    }

    // Atualiza conteúdo
    this.activeFile = fileName;
    this.updateCodeDisplay();
  },

  /**
   * Atualiza display do código
   */
  updateCodeDisplay() {
    const codeDisplay = document.getElementById('code-display');
    if (codeDisplay && this.currentFiles[this.activeFile]) {
      codeDisplay.innerHTML = `<code>${Utils.sanitizeHtml(this.currentFiles[this.activeFile])}</code>`;
    }
  },

  /**
   * Gera código do agente
   */
  async generateCode() {
    const data = appState.agentDraft;
    
    try {
      appState.loading = true;
      this.updateButtonStates(true);
      
      // Simula chamada à API (pode implementar real mais tarde)
      await this.simulateCodeGeneration(data);
      
      Toast.success('Código Gerado', 'Arquivos do agente criados com sucesso');
      Logger.log('info', 'frontend', 'Código do agente gerado com sucesso');
      
    } catch (error) {
      Toast.error('Erro na Geração', error.message);
      Logger.log('error', 'frontend', `Erro ao gerar código: ${error.message}`);
    } finally {
      appState.loading = false;
      this.updateButtonStates(false);
    }
  },

  /**
   * Simula geração de código (pode ser substituído por chamada real à API)
   */
  async simulateCodeGeneration(data) {
    return new Promise((resolve) => {
      setTimeout(() => {
        this.currentFiles = {
          'main.py': this.generateMainPy(data),
          'agent.py': this.generateAgentPy(data),
          'evolution.py': this.generateEvolutionPy(data)
        };
        
        appState.generatedFiles = Object.entries(this.currentFiles).map(([path, content]) => ({
          path: `backend/${path}`,
          content
        }));
        
        this.updateCodeDisplay();
        resolve();
      }, 2000);
    });
  },

  /**
   * Gera arquivo main.py
   */
  generateMainPy(data) {
    return `#!/usr/bin/env python3
"""
Agente ${data.agent_name}
Especialização: ${data.specialization}

Gerado automaticamente pelo Agno SDK Agent Generator
"""
import os
from dotenv import load_dotenv
from agno import Agent, AgentConfig
from services.evolution import EvolutionService

# Carrega variáveis de ambiente
load_dotenv()

def main():
    # Configuração do agente
    config = AgentConfig(
        name="${data.agent_name}",
        specialization="${data.specialization}",
        instructions="""${data.instructions}""",
        tools=${JSON.stringify(data.tools)}
    )
    
    # Inicializa agente
    agent = Agent(config)
    
    # Inicializa serviços
    if "whatsapp" in ${JSON.stringify(data.tools)}:
        evolution = EvolutionService()
        agent.add_service("whatsapp", evolution)
    
    print(f"🤖 Agente {data.agent_name} iniciado")
    print(f"📋 Especialização: {data.specialization}")
    print(f"🔧 Ferramentas: ${data.tools.join(', ')}")
    
    # Inicia loop principal
    agent.run()

if __name__ == "__main__":
    main()
`;
  },

  /**
   * Gera arquivo agent.py
   */
  generateAgentPy(data) {
    return `"""
Definição do Agente ${data.agent_name}
"""
from typing import List, Dict, Any
from agno import BaseAgent

class ${data.agent_name.replace(/[-_]/g, '').charAt(0).toUpperCase() + data.agent_name.replace(/[-_]/g, '').slice(1)}Agent(BaseAgent):
    """
    Agente especializado em: ${data.specialization}
    
    Instruções:
    ${data.instructions}
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.specialization = "${data.specialization}"
        self.tools = ${JSON.stringify(data.tools)}
    
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> str:
        """
        Processa mensagem recebida
        """
        # Implementar lógica específica da especialização
        if self.specialization == "Atendimento":
            return await self.handle_customer_service(message, context)
        elif self.specialization == "Vendas":
            return await self.handle_sales(message, context)
        elif self.specialization == "Agendamento":
            return await self.handle_scheduling(message, context)
        elif self.specialization == "Suporte":
            return await self.handle_support(message, context)
        else:
            return await self.handle_custom(message, context)
    
    async def handle_customer_service(self, message: str, context: Dict[str, Any]) -> str:
        """Lógica de atendimento ao cliente"""
        # TODO: Implementar lógica específica
        return "Olá! Como posso ajudá-lo hoje?"
    
    async def handle_sales(self, message: str, context: Dict[str, Any]) -> str:
        """Lógica de vendas"""
        # TODO: Implementar lógica específica
        return "Vou ajudá-lo com informações sobre nossos produtos!"
    
    async def handle_scheduling(self, message: str, context: Dict[str, Any]) -> str:
        """Lógica de agendamento"""
        # TODO: Implementar lógica específica
        return "Posso ajudá-lo a agendar um horário!"
    
    async def handle_support(self, message: str, context: Dict[str, Any]) -> str:
        """Lógica de suporte técnico"""
        # TODO: Implementar lógica específica
        return "Como posso ajudá-lo com suporte técnico?"
    
    async def handle_custom(self, message: str, context: Dict[str, Any]) -> str:
        """Lógica personalizada"""
        # TODO: Implementar lógica personalizada
        return "Processando sua mensagem..."
`;
  },

  /**
   * Gera arquivo evolution.py
   */
  generateEvolutionPy(data) {
    return `"""
Serviço de integração com Evolution API para WhatsApp
"""
import os
import asyncio
import httpx
from typing import Optional, Dict, Any
from loguru import logger

class EvolutionService:
    """
    Cliente para Evolution API
    """
    
    def __init__(self):
        self.base_url = os.getenv("EVOLUTION_BASE_URL")
        self.api_key = os.getenv("EVOLUTION_API_KEY")
        self.instance_name = os.getenv("EVOLUTION_DEFAULT_INSTANCE", "${data.agent_name}")
        
        if not self.base_url or not self.api_key:
            raise ValueError("Evolution API credentials not configured")
    
    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_instance(self) -> Dict[str, Any]:
        """
        Cria ou recupera instância do WhatsApp
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/instance/create",
                    headers=self.headers,
                    json={
                        "instanceName": self.instance_name,
                        "integration": "WHATSAPP-BAILEYS"
                    }
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Instância {self.instance_name} criada/recuperada")
                return data
                
            except httpx.RequestError as e:
                logger.error(f"Erro ao criar instância: {e}")
                raise
    
    async def get_qr_code(self) -> Optional[str]:
        """
        Obtém QR Code para pareamento
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/instance/connect/{self.instance_name}",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                if "qr" in data:
                    logger.info("QR Code obtido com sucesso")
                    return data["qr"]
                return None
                
            except httpx.RequestError as e:
                logger.error(f"Erro ao obter QR Code: {e}")
                return None
    
    async def get_instance_status(self) -> str:
        """
        Verifica status da instância
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/instance/connectionState/{self.instance_name}",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                status = data.get("state", "UNKNOWN")
                logger.info(f"Status da instância: {status}")
                return status
                
            except httpx.RequestError as e:
                logger.error(f"Erro ao verificar status: {e}")
                return "ERROR"
    
    async def send_message(self, to: str, message: str) -> bool:
        """
        Envia mensagem via WhatsApp
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/message/sendText/{self.instance_name}",
                    headers=self.headers,
                    json={
                        "number": to,
                        "text": message
                    }
                )
                response.raise_for_status()
                logger.info(f"Mensagem enviada para {to}")
                return True
                
            except httpx.RequestError as e:
                logger.error(f"Erro ao enviar mensagem: {e}")
                return False
    
    async def setup_webhook(self, webhook_url: str) -> bool:
        """
        Configura webhook para receber mensagens
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/webhook/set/{self.instance_name}",
                    headers=self.headers,
                    json={
                        "url": webhook_url,
                        "events": ["messages.upsert"]
                    }
                )
                response.raise_for_status()
                logger.info(f"Webhook configurado: {webhook_url}")
                return True
                
            except httpx.RequestError as e:
                logger.error(f"Erro ao configurar webhook: {e}")
                return False
`;
  },

  /**
   * Copia código atual
   */
  async copyCurrentCode() {
    const code = this.currentFiles[this.activeFile];
    if (!code) {
      Toast.warning('Nenhum Código', 'Gere o código primeiro');
      return;
    }

    const success = await Utils.copyToClipboard(code);
    if (success) {
      Toast.success('Código Copiado', `Arquivo ${this.activeFile} copiado para a área de transferência`);
    } else {
      Toast.error('Erro ao Copiar', 'Não foi possível copiar o código');
    }
  },

  /**
   * Download ZIP dos arquivos
   */
  downloadZip() {
    if (Object.keys(this.currentFiles).length === 0) {
      Toast.warning('Nenhum Código', 'Gere o código primeiro');
      return;
    }

    // Simula criação de ZIP
    const zipContent = Object.entries(this.currentFiles)
      .map(([filename, content]) => `=== ${filename} ===\n${content}\n\n`)
      .join('');
    
    Utils.downloadFile(zipContent, `${appState.agentDraft.agent_name || 'agent'}-files.zip`);
    Toast.success('Download Iniciado', 'ZIP com os arquivos do agente baixado');
  },

  /**
   * Materializa no servidor
   */
  async materializeOnServer() {
    if (Object.keys(this.currentFiles).length === 0) {
      Toast.warning('Nenhum Código', 'Gere o código primeiro');
      return;
    }

    try {
      appState.loading = true;
      
      // Simula chamada à API
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      Toast.success('Materializado', 'Agente salvo no servidor com sucesso');
      Logger.log('info', 'frontend', 'Agente materializado no servidor');
      
      // Adiciona à lista de agentes
      const newAgent = {
        id: Utils.generateId(),
        ...appState.agentDraft,
        status: 'DESCONHECIDO',
        createdAt: new Date()
      };

      const updatedAgents = [...appState.agents, newAgent];
      StateManager.updateState('agents', updatedAgents);

    } catch (error) {
      Toast.error('Erro na Materialização', error.message);
      Logger.log('error', 'frontend', `Erro ao materializar agente: ${error.message}`);
    } finally {
      appState.loading = false;
    }
  },

  /**
   * Atualiza estado dos botões durante loading
   */
  updateButtonStates(loading) {
    const buttons = ['btn-generate-code', 'btn-download-zip', 'btn-materialize-server'];
    
    buttons.forEach(buttonId => {
      const button = document.getElementById(buttonId);
      if (button) {
        button.disabled = loading;
        if (loading && buttonId === 'btn-generate-code') {
          button.innerHTML = '<span class="button-icon">⏳</span><span class="button-text">Gerando...</span>';
        } else if (!loading && buttonId === 'btn-generate-code') {
          button.innerHTML = '<span class="button-icon">⚡</span><span class="button-text">Gerar Código</span>';
        }
      }
    });

    // Habilita botões após geração bem-sucedida
    if (!loading && Object.keys(this.currentFiles).length > 0) {
      document.getElementById('btn-download-zip').disabled = false;
      document.getElementById('btn-materialize-server').disabled = false;
    }
  }
};

// Gerenciador de Configurações
const SettingsManager = {
  /**
   * Inicializa configurações
   */
  init() {
    this.setupIntegrationToggles();
    this.setupConnectionTest();
    this.setupEvolutionAPIControls();
    this.setupApiTokenControl();
    this.setupAppearanceControls();
    this.loadSettings();
  },

  /**
   * Configura toggles de integração
   */
  setupIntegrationToggles() {
    document.querySelectorAll('[data-integration]').forEach(toggle => {
      toggle.addEventListener('change', (e) => {
        const integration = toggle.getAttribute('data-integration');
        const isEnabled = toggle.checked;
        
        StateManager.updateState(`ui.integrations.${integration}`, isEnabled);
        
        Logger.log('info', 'frontend', `Integração ${integration} ${isEnabled ? 'ativada' : 'desativada'}`);
        Toast.info('Integração Atualizada', `${integration} ${isEnabled ? 'ativada' : 'desativada'}`);
      });
    });
  },

  /**
   * Configura teste de conexão
   */
  setupConnectionTest() {
    document.getElementById('btn-test-connection')?.addEventListener('click', async () => {
      try {
        const button = document.getElementById('btn-test-connection');
        const originalText = button.innerHTML;
        
        button.innerHTML = '<span class="button-icon">⏳</span><span class="button-text">Testando...</span>';
        button.disabled = true;
        
        // Simula teste de conexão
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Simula resultado (70% de sucesso)
        const success = Math.random() > 0.3;
        
        if (success) {
          Toast.success('Conexão OK', 'Backend está respondendo normalmente');
          Logger.log('info', 'api', 'Teste de conexão bem-sucedido');
        } else {
          Toast.error('Falha na Conexão', 'Backend não está respondendo');
          Logger.log('error', 'api', 'Falha no teste de conexão');
        }
        
        button.innerHTML = originalText;
        button.disabled = false;
        
      } catch (error) {
        Toast.error('Erro no Teste', 'Não foi possível testar a conexão');
        Logger.log('error', 'frontend', `Erro no teste de conexão: ${error.message}`);
      }
    });
  },

  /**
   * Configura controles da Evolution API
   */
  setupEvolutionAPIControls() {
    // Salvar credenciais
    document.getElementById('btn-save-evolution')?.addEventListener('click', () => {
      this.saveEvolutionCredentials();
    });

    // Testar Evolution API
    document.getElementById('btn-test-evolution')?.addEventListener('click', async () => {
      await this.testEvolutionConnection();
    });

    // Atualizar credenciais em tempo real
    ['evolution-base-url', 'evolution-api-key', 'evolution-instance-name'].forEach(fieldId => {
      const field = document.getElementById(fieldId);
      if (field) {
        field.addEventListener('input', (e) => {
          this.updateEvolutionConfig(fieldId, e.target.value);
        });
      }
    });
  },

  /**
   * Configura campo de token de acesso
   */
  setupApiTokenControl() {
    const field = document.getElementById('api-token');
    if (field) {
      field.addEventListener('input', (e) => {
        StateManager.updateState('apiToken', e.target.value);
      });
    }
  },

  /**
   * Salva credenciais da Evolution API
   */
  saveEvolutionCredentials() {
    const baseURL = document.getElementById('evolution-base-url')?.value;
    const apiKey = document.getElementById('evolution-api-key')?.value;
    const instanceName = document.getElementById('evolution-instance-name')?.value;

    if (!baseURL || !apiKey || !instanceName) {
      Toast.warning('Dados Incompletos', 'Preencha todos os campos da Evolution API');
      return;
    }

    // Atualiza estado
    appState.evolutionAPI = {
      ...appState.evolutionAPI,
      baseURL: baseURL,
      apiKey: apiKey,
      instanceName: instanceName
    };

    // Persiste no localStorage
    StateManager.persistState();

    Toast.success('Evolution API', 'Credenciais salvas com sucesso');
    Logger.log('info', 'settings', 'Credenciais Evolution API atualizadas');
  },

  /**
   * Testa conexão com Evolution API
   */
  async testEvolutionConnection() {
    try {
      const button = document.getElementById('btn-test-evolution');
      const originalText = button.innerHTML;
      
      button.innerHTML = '<span class="button-icon">⏳</span><span class="button-text">Testando...</span>';
      button.disabled = true;

      const baseURL = document.getElementById('evolution-base-url')?.value;
      const apiKey = document.getElementById('evolution-api-key')?.value;

      if (!baseURL || !apiKey) {
        throw new Error('Base URL e API Key são obrigatórias');
      }

      // Testa conexão com endpoint de instâncias
      const response = await fetch(`${baseURL}/instance/fetchInstances`, {
        method: 'GET',
        headers: {
          'apikey': apiKey,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        Toast.success('Evolution API', `Conexão OK! ${data.length || 0} instância(s) encontrada(s)`);
        Logger.log('info', 'evolution', `Teste de conexão bem-sucedido: ${data.length || 0} instâncias`);
        
        appState.evolutionAPI.connected = true;
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      button.innerHTML = originalText;
      button.disabled = false;

    } catch (error) {
      Logger.log('error', 'evolution', `Erro no teste de conexão: ${error.message}`);
      Toast.error('Evolution API', `Erro: ${error.message}`);
      
      appState.evolutionAPI.connected = false;
      
      const button = document.getElementById('btn-test-evolution');
      button.innerHTML = '<span class="button-icon">🔌</span><span class="button-text">Testar Evolution API</span>';
      button.disabled = false;
    }
  },

  /**
   * Atualiza configuração da Evolution API
   */
  updateEvolutionConfig(fieldId, value) {
    const configMap = {
      'evolution-base-url': 'baseURL',
      'evolution-api-key': 'apiKey',
      'evolution-instance-name': 'instanceName'
    };

    const configKey = configMap[fieldId];
    if (configKey) {
      appState.evolutionAPI[configKey] = value;
      
      // Debounced save
      clearTimeout(this.saveTimeout);
      this.saveTimeout = setTimeout(() => {
        StateManager.persistState();
      }, 1000);
    }
  },

  /**
   * Configura controles de aparência
   */
  setupAppearanceControls() {
    // Controle de escala de fonte
    document.getElementById('btn-font-decrease')?.addEventListener('click', () => {
      this.adjustFontScale(-1);
    });
    
    document.getElementById('btn-font-increase')?.addEventListener('click', () => {
      this.adjustFontScale(1);
    });
    
    // Toggle de movimento reduzido
    document.getElementById('reduce-motion')?.addEventListener('change', (e) => {
      StateManager.updateState('ui.reduceMotion', e.target.checked);
      this.applyMotionPreference(e.target.checked);
    });
  },

  /**
   * Ajusta escala da fonte
   */
  adjustFontScale(delta) {
    const currentScale = appState.ui.fontScale;
    const newScale = Math.max(-1, Math.min(1, currentScale + delta));
    
    if (newScale !== currentScale) {
      StateManager.updateState('ui.fontScale', newScale);
      document.documentElement.setAttribute('data-font-scale', newScale);
      
      const scaleValue = document.getElementById('font-scale-value');
      if (scaleValue) {
        scaleValue.textContent = newScale;
      }
      
      Toast.info('Fonte Alterada', `Escala: ${newScale > 0 ? '+' : ''}${newScale}`);
    }
  },

  /**
   * Aplica preferência de movimento
   */
  applyMotionPreference(reduceMotion) {
    if (reduceMotion) {
      document.documentElement.style.setProperty('--transition', 'none');
      document.documentElement.style.setProperty('--transition-fast', 'none');
      document.documentElement.style.setProperty('--transition-slow', 'none');
    } else {
      document.documentElement.style.removeProperty('--transition');
      document.documentElement.style.removeProperty('--transition-fast');
      document.documentElement.style.removeProperty('--transition-slow');
    }
  },

  /**
   * Carrega configurações salvas
   */
  loadSettings() {
    const ui = appState.ui;
    
    // Carrega toggles de integração
    Object.entries(ui.integrations).forEach(([integration, enabled]) => {
      const toggle = document.querySelector(`[data-integration="${integration}"]`);
      if (toggle) {
        toggle.checked = enabled;
      }
    });
    
    // Carrega escala de fonte
    document.documentElement.setAttribute('data-font-scale', ui.fontScale);
    const scaleValue = document.getElementById('font-scale-value');
    if (scaleValue) {
      scaleValue.textContent = ui.fontScale;
    }
    
    // Carrega preferência de movimento
    const reduceMotionToggle = document.getElementById('reduce-motion');
    if (reduceMotionToggle) {
      reduceMotionToggle.checked = ui.reduceMotion;
      this.applyMotionPreference(ui.reduceMotion);
    }

    // Carrega token de acesso
    const tokenField = document.getElementById('api-token');
    if (tokenField) {
      tokenField.value = appState.apiToken || '';
    }
  }
};

// Eventos globais e inicialização
document.addEventListener('DOMContentLoaded', () => {
  // Carrega estado persistido
  StateManager.loadPersistedState();
  
  // Inicializa componentes
  Toast.init();
  Navigation.init();
  FormManager.init();
  CodeGenerator.init();
  SettingsManager.init();
  AgentManager.startPolling();
  
  // Configura modais
  document.querySelectorAll('.modal-close, .modal-backdrop').forEach(element => {
    element.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal-close') || e.target.classList.contains('modal-backdrop')) {
        Modal.close();
      }
    });
  });
  
  // Botão de copiar JSON no modal
  document.getElementById('btn-copy-json')?.addEventListener('click', async () => {
    const jsonContent = document.getElementById('json-preview')?.textContent;
    if (jsonContent) {
      const success = await Utils.copyToClipboard(jsonContent);
      if (success) {
        Toast.success('JSON Copiado', 'Esquema copiado para a área de transferência');
      }
    }
  });
  
  // Configurar filtros de log
  document.getElementById('log-level')?.addEventListener('change', (e) => {
    Logger.renderLogs({ level: e.target.value });
  });
  
  document.getElementById('log-search')?.addEventListener('input', Utils.debounce((e) => {
    Logger.renderLogs({ search: e.target.value });
  }, 300));
  
  // Botões de controle de logs
  document.getElementById('btn-pause-logs')?.addEventListener('click', (e) => {
    const paused = Logger.togglePause();
    e.target.innerHTML = paused
      ? '<span class="button-icon">▶️</span><span class="button-text">Retomar</span>'
      : '<span class="button-icon">⏸️</span><span class="button-text">Pausar</span>';
    e.target.setAttribute('aria-pressed', paused);
  });
  
  document.getElementById('btn-clear-logs')?.addEventListener('click', () => {
    Logger.clear();
    Toast.info('Logs Limpos', 'Console de logs foi limpo');
  });
  
  document.getElementById('btn-export-logs')?.addEventListener('click', () => {
    Logger.export();
    Toast.success('Logs Exportados', 'Arquivo de logs baixado');
  });
  
  // Simula alguns logs iniciais
  Logger.log('info', 'frontend', 'Aplicação inicializada com sucesso');
  Logger.log('info', 'frontend', `Estado carregado: ${Object.keys(appState.agentDraft).length > 0 ? 'rascunho encontrado' : 'novo agente'}`);
  
  console.log('🚀 Agno SDK Agent Generator inicializado');
});

// Exposição global para debugging (apenas em desenvolvimento)
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
  window.agnoApp = {
    appState,
    StateManager,
    Logger,
    Toast,
    Modal,
    ApiClient,
    Utils
  };
}