## Prompt para gerar o HTML/CSS/JS do aplicativo (sem frameworks)

> **Objetivo**: Criar uma **SPA simples** (uma página, múltiplas seções) no estilo **iOS dark** para o projeto **Agno SDK Agent Generator**. Não gere back‑end aqui. **Não escreva bibliotecas externas** e **não use frameworks** (nem CSS, nem JS). O foco é **HTML semântico + CSS puro + JS vanilla** com excelente usabilidade.

---

### Requisitos de alto nível
1. **Páginas/Seções** (aba/tabs internas, sem rotas reais):
   - **Criação de Agente** (principal).
   - **Meus Agentes** (lista de agentes salvos/gerados).
   - **Logs** (console em tempo real e filtros básicos).
   - **Configurações** (inclui a lista de integrações do print: *WhatsApp via Evolution API*, *APIs de Pagamento*, *Plataformas de Agendamento*, *CRM e Sistemas de Vendas*, *Sistemas de Atendimento*, cada uma com **toggle**).
2. **Estilo**: tema **iOS dark graphite** (bordas 20px, cinzas hierárquicos, tipografia SF‑like).
3. **Acessibilidade**: contraste **AA**, navegação por **teclado**, `aria-*` em componentes, foco visível.
4. **Interações**: transições 150–220ms, toasts, skeleton loaders, modais (Preview JSON e QR Code).
5. **Segurança no front**: sanitizar textos antes de injetar, **não** armazenar segredos em `localStorage`.

---

### Estrutura do arquivo e módulos (saídas esperadas)
- `index.html` — HTML semântico com **Top Nav** e as quatro seções.
- `styles.css` — CSS com **variáveis** de tema e componentes reutilizáveis.
- `app.js` — JS **modular** (IIFE ou módulos ES) para estado, validação e chamadas de API.

---

### Top Nav / Layout Base
- Top bar com **título** e ícone minimalista.
- Abaixo, uma **barra de tabs** (ou side‑nav responsivo) com 4 botões para trocar a seção ativa.
- Use **IDs/anchors fixos** para cada seção (ver IDs obrigatórios).
- Cards com **padding 16–24px**, **radius 20px**, **shadow suave**, separadores sutis.

---

### Criação de Agente (seção principal)
**Objetivo**: coletar dados e validar, gerar um **JSON local** de preview e acionar endpoints depois (somente wiring; não implemente back‑end).

**Campos** (com labels flutuantes):
- `agent_name` (texto): 3–40 chars, alfanumérico, hífen/underscore.
- `instructions` (textarea): **mín. 80 chars**; contador de caracteres.
- `specialization` (select): `Atendimento`, `Agendamento`, `Vendas`, `Suporte`, `Custom`.
- `tools` (checkbox‑group): `WhatsApp (Evolution)`, `E-mail`, `Google Calendar`, `HTTP Webhooks`, `Banco de dados`.

**Ações**:
- **Pré‑visualizar Esquema**: abre modal com o JSON do agente (sanitizado e formatado, copy‑to‑clipboard).
- **Salvar Rascunho**: armazena **somente** os campos do formulário em `localStorage`.
- **Continuar**: troca para “Meus Agentes” ou exibe a etapa de **Geração de Código** (pode ser um sub‑card nesta mesma seção com resumo + ações).

**Validações**:
- Bloqueie avanço sem os obrigatórios; mensagens inline sob o campo.
- Mostre **badges** de erro/sucesso ao lado do título do card.

---

### Meus Agentes
- **Grid de cards** (ou tabela responsiva) com: Nome, Especialização, Tools, Status WhatsApp (badge: DESCONHECIDO/QR_ABERTO/CONECTANDO/CONECTADO).
- **Ações por agente**: `Pré‑visualizar` (abre modal com arquivos gerados — conteúdo mockado), `Copiar Código`, `Baixar ZIP`, `Materializar no Servidor`, `Conectar WhatsApp` (abre modal de QR), `Excluir`.
- Skeleton loaders enquanto carrega a lista (mesmo que a fonte seja localStorage; simule latência pequena).

---

### Logs
- Console de logs (monospace, scrollable) com filtros: **nível** (INFO/WARN/ERROR), **origem** (frontend/backend/evolution), **texto** (search).
- Botões: `Pausar/Retomar`, `Limpar`, `Exportar .txt`.
- Simule SSE/polling com `setInterval` + buffer em memória (não chame back‑end real).

---

### Configurações
- Card “**Configurações de Integrações**” replicando o visual do print: cada item com **ícone**, título, descrição curta e **toggle** à direita.
- Outros cards:
  - **Conexões**: `API Base URL` (readonly padrão `http://localhost:8000`, com botão “Testar Conexão”).
  - **Aparência**: escala de fonte (−/0/+), opção de **reduzir movimento**.
- **Persistência**: salve toggles e preferências **não sensíveis** no `localStorage`.

---

### IDs e data‑attributes obrigatórios (para automação)
- Seções: `#page-create`, `#page-agents`, `#page-logs`, `#page-settings`.
- Botões principais:
  - `#btn-preview-agent-schema`, `#btn-save-draft`, `#btn-continue`.
  - `#btn-test-connection`, `#btn-open-qr-modal`, `#btn-send-test` (estes últimos só **marcadores**, sem back‑end real).
- Modais: `#modal-preview-json`, `#modal-qr`.
- Logs: `#log-console`, filtro nível `#log-level`, busca `#log-search`.
- Config: toggles como `[data-integration="whatsapp"]`, `[data-integration="payments"]`, `[data-integration="scheduling"]`, `[data-integration="crm"]`, `[data-integration="support"]`.

---

### Design Tokens (defina como variáveis CSS)
```text
--bg: #0B0B0F;
--surface: #1C1C1E;
--surface-alt: #2C2C2E;
--stroke: #3A3A3C;
--text-primary: #F2F2F7;
--text-secondary: #C7C7CC;
--accent: #0A84FF;
--success: #32D74B;
--warning: #FFD60A;
--danger: #FF453A;
--radius: 20px;
--shadow: 0 6px 24px rgba(0,0,0,.35);
--transition: 180ms ease;
```
**Tipografia**: `system-ui, -apple-system, 'SF Pro Text', 'SF Pro Display', Inter, Roboto, Arial, sans-serif`.
**Tamanhos**: h1 28px, h2 22px, h3 18px, body 15px, caption 13px.

---

### Componentes obrigatórios
- **Card**: `section-card` com título, descrição breve e `divider`.
- **Button** (pill, 40px altura): estados *default/hover/pressed/disabled*.
- **Input** com label flutuante e foco com glow leve.
- **Select**, **Checkbox‑group** (tools), **Toggle** (config/integrações).
- **Progress bar** (para estados “conectando”).
- **Toast** (sucesso/erro) com auto‑dismiss.
- **Modal**: `modal-qr` (img/base64 placeholder) e `modal-preview-json` (JSON em `<pre>` com copy).

---

### JS — comportamento mínimo
- **Gerenciador de estado** simples (objeto único `appState`) com:
  - `agentDraft`: { `agent_name`, `instructions`, `specialization`, `tools[]` }.
  - `ui`: seção ativa, preferências (reduzir movimento, fontScale), integrações ativas.
- **Validação**: regex para nome, min length p/ prompt, ao digitar.
- **Persistência**: salvar/ler `agentDraft` e preferências em `localStorage` (chave: `agno:ui` / `agno:draft`).
- **Modais**: abrir/fechar via classes utilitárias, bloquear scroll do body.
- **Logs**: função `log(level, source, message)` que adiciona linhas com timestamp; filtros reativos.
- **Toasts**: fila simples; cada toast expira (4–6s) e pode ser fechada.

---

### Ações simuladas (sem back‑end)
- **Pré‑visualizar Esquema**: montar JSON a partir do formulário, exibir formatado no modal.
- **Testar Conexão** (Configurações): simular request com `setTimeout` e mostrar toast OK/ERROR (não chame rede de verdade).
- **Abrir QR**: abrir `modal-qr` com uma imagem placeholder (retângulo com padrão quadriculado e label “QR placeholder”).

> **Importante**: Todos os botões que teoricamente chamariam API devem apenas **simular** resultado (carregando → sucesso/erro) e **nunca** conter URLs reais nem chaves.

---

### Acessibilidade e microinterações
- Use `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-describedby` nos modais; foco vai para o primeiro elemento interativo quando abrir e retorna ao trigger ao fechar.
- Estados de foco com alto contraste (outline halo suave na cor `--accent`).
- Respeite preferências do usuário: se `prefers-reduced-motion` → reduzir animações.

---

### Boas práticas (DOs & DON'Ts)
**DOs**
- HTML semântico (`header`, `main`, `section`, `nav`, `footer`).
- Componentização via classes utilitárias e BEM leve.
- Layout **mobile‑first**; desktop até 1200px de largura de conteúdo.

**DON'Ts**
- `innerHTML` com conteúdo do usuário sem sanitizar.
- CORS, URLs de API ou segredos hardcoded.
- Textos com contraste insuficiente no dark.

---

### Critérios de aceite
- Quatro seções funcionais com navegação suave.
- Formulário da **Criação de Agente** valida e salva rascunho; preview JSON abre e copia.
- **Meus Agentes** renderiza pelo menos 3 cards de exemplo, com ações (todas simuladas).
- **Logs** filtráveis, com export `.txt`.
- **Configurações** replica a lista de integrações (com toggles persistentes) e tem botão “Testar Conexão”.
- Acessibilidade básica (aria, foco, contraste) e microinterações (transições ≤ 220ms).

---

### Entrega
- Forneça **apenas** os três arquivos (`index.html`, `styles.css`, `app.js`) prontos para abrir em `Live Server`.
- O código deve estar **comentado** nos pontos críticos (acessibilidade, modais, validação e persistência).
- Sem dependências externas. Nada de CDN.

