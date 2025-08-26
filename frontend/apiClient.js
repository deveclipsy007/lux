// @ts-check
/// <reference path="./api.ts" />

/**
 * Retorna headers de autenticação
 */
function getAuthHeaders() {
  const token = appState.apiToken || Storage.load('apiToken');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Verifica erros de autenticação
 * @param {Response} response
 */
function checkAuth(response) {
  if (response.status === 401) {
    Navigation.switchSection('page-settings');
    Toast.warning('Autenticação Necessária', 'Informe seu token de acesso nas Configurações.');
    throw new Error('Não autenticado');
  }
}

/**
 * Requisição base com interceptors
 * @param {string} endpoint
 * @param {RequestInit} [options]
 */
async function request(endpoint, options = {}) {
  const url = `${window.API_BASE}${endpoint}`;
  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...(options.headers || {})
    }
  };

  try {
    Logger.log('info', 'api', `${config.method || 'GET'} ${endpoint}`);

    const response = await fetch(url, config);
    checkAuth(response);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      Toast.error('Erro na API', data.detail || `HTTP ${response.status}`);
      Logger.log('error', 'api', `Erro em ${endpoint}: ${data.detail || `HTTP ${response.status}`}`);
      throw new Error(data.detail || `HTTP ${response.status}`);
    }

    Logger.log('info', 'api', `Sucesso: ${endpoint}`);
    return data;
  } catch (error) {
    if (error instanceof TypeError) {
      Toast.error('Erro de Rede', 'Não foi possível conectar ao servidor');
    }
    Logger.log('error', 'api', `Erro em ${endpoint}: ${error.message}`);
    throw error;
  }
}

function generateAgent(agentData) {
  return request('/api/agents/generate', {
    method: 'POST',
    body: JSON.stringify(agentData)
  });
}

function materializeAgent(agentData) {
  return request('/api/agents/materialize', {
    method: 'POST',
    body: JSON.stringify(agentData)
  });
}

function getAgent(agentId) {
  return request(`/api/agents/${agentId}`);
}

function updateAgent(agentId, agentData) {
  return request(`/api/agents/${agentId}`, {
    method: 'PUT',
    body: JSON.stringify(agentData)
  });
}

function deleteAgent(agentId) {
  return request(`/api/agents/${agentId}`, {
    method: 'DELETE'
  });
}

function listAgents() {
  return request('/api/agents');
}

function createWhatsAppInstance(instanceData) {
  return request('/api/wpp/instances', {
    method: 'POST',
    body: JSON.stringify(instanceData)
  });
}

function getQRCode(instanceId) {
  return request(`/api/wpp/instances/${instanceId}/qr`);
}

function getInstanceStatus(instanceId) {
  return request(`/api/wpp/instances/${instanceId}/status`);
}

function sendTestMessage(messageData) {
  return request('/api/wpp/messages', {
    method: 'POST',
    body: JSON.stringify(messageData)
  });
}

function testConnection() {
  return request('/api/health');
}

// Expor funções globalmente
window.getAuthHeaders = getAuthHeaders;
window.checkAuth = checkAuth;
window.request = request;
window.generateAgent = generateAgent;
window.materializeAgent = materializeAgent;
window.getAgent = getAgent;
window.updateAgent = updateAgent;
window.deleteAgent = deleteAgent;
window.listAgents = listAgents;
window.createWhatsAppInstance = createWhatsAppInstance;
window.getQRCode = getQRCode;
window.getInstanceStatus = getInstanceStatus;
window.sendTestMessage = sendTestMessage;
window.testConnection = testConnection;
