# VOICEBRIDGE AI — Master Handoff, Diagnóstico Ao Vivo & Tutoriais de Operação

- **Autor:** Yago Santos Silva
- **Data de Registro:** 18/11/2026
- **Repositório GitHub:** `https://github.com/yago-silva-ads/voicebridge-ai` (Branch `main`, commit `674f77d`)
- **Diretório Local:** `C:\VoiceBridgeAI`
- **Hardware Validado:** Lenovo LOQ 15 | Intel Core i5 | 16GB RAM | NVIDIA RTX 2050 (4GB VRAM — CUDA Ativo)
- **Conexões no Grafo (`CEREBRO_YAGO`):** [[COLA_ENTREVISTA]] | [[ENTREVISTA_AIR_RESPOSTAS]] | [[ENTREVISTA_AIR_LLIA]] | [[VOICEBRIDGE_AI_MASTER_PLAN]] | [[VOICEBRIDGE_AI_DOCUMENTACAO]] | [[CACADOR_ESTADO_2026-10-12]]

---

## 1. Diagnóstico Real do Teste Ao Vivo (Log de 18/11/2026)

Durante a execução de `.\.venv\Scripts\python.exe main.py --mode interview`, **95% da arquitetura funcionou de primeira**:

### O que já está 100% validado e operacional
1. **Invisibilidade de Tela (`WDA_EXCLUDEFROMCAPTURE`):** Aplicado com sucesso (`hwnd=1441946`). A janela fica visível para você e invisível em compartilhamentos de tela (Teams, Meet, Zoom, OBS).
2. **GPU NVIDIA RTX 2050 (CUDA):** `faster-whisper` (`base.en` em `int8_float16`) carregou na placa de vídeo em ~3 segundos (`✓ Whisper loaded on cuda`) com VAD ativo.
3. **Atalhos Globais (`pynput`):** `Ctrl+Shift+H`, `Ctrl+Shift+M` e `Ctrl+Shift+Space` ativos globalmente mesmo fora de foco.
4. **Ponte Wi-Fi iPhone 13 (`web_companion.py`):** Servidor FastAPI/WebSocket ativo em `http://192.168.15.71:8000`.
5. **Dual-Channel + Echo Gate:** Subprocesso de Loopback (`PID 13024`) e thread de Microfone operando em paralelo sem travar a UI, alternando limpo entre `INTERVIEW` e `SCRIPT` (`19 words`).

### Único Ponto de Melhoria Encontrado no Log (Corrigir na Próxima Sessão)
No log às `19:02:38`, a primeira tentativa da Groq falhou antes de acionar o fallback:
```text
WARNING — Model llama-3.3-70b-versatile failed: Error code: 404 - model_not_found
INFO — Copilot response via openai/gpt-oss-120b (124 chars)
```
- **O que isso significa:** O modelo `llama-3.3-70b-versatile` retornou `404` na sua conta Groq, fazendo o sistema perder ~1 segundo antes de cair automaticamente no `openai/gpt-oss-120b` (que respondeu com `200 OK`).
- **Ação para o próximo agente:** No arquivo `ai/copilot.py`, colocar **`openai/gpt-oss-120b`** como **primeiro modelo da lista** (e `openai/gpt-oss-20b` como segundo), eliminando o erro `404` e deixando a resposta instantânea (<350ms).

---

## 2. Tutoriais Práticos de Uso (Guia Rápido para o Yago)

### Cenário A: Entrevista no Notebook (Com Fone de Ouvido — Melhor Qualidade)
1. **Conecte o fone de ouvido ANTES** de abrir o programa (o Loopback captura a saída padrão ativa na inicialização).
2. Abra o **NVIDIA Broadcast** e ligue o efeito **Eye Contact** (Contato Visual) na RTX 2050.
3. Abra o PowerShell e execute:
   ```powershell
   cd C:\VoiceBridgeAI
   .\.venv\Scripts\python.exe main.py --mode interview
   ```
4. Arraste a barra translúcida para o topo central, logo abaixo da lente da webcam.

---

### Cenário B: Entrevista no Notebook (Sem Fone — Usando Alto-Falantes)
1. Abra o **NVIDIA Broadcast** → aba **Microfone** → ative **Remoção de Ruído** e **Remoção de Eco da Sala** (impede o eco acústico).
2. Execute no PowerShell:
   ```powershell
   cd C:\VoiceBridgeAI
   .\.venv\Scripts\python.exe main.py --mode interview
   ```
3. **Como funciona:** A trava *Half-Duplex (`Echo Gate`)* bloqueia o seu microfone enquanto o entrevistador fala nos alto-falantes e por `1.5s` após ele terminar, gerando os tópicos da Groq sem bagunçar a rolagem do texto.

---

### Cenário C: Usando o iPhone 13 Como Tela Auxiliar ou Chamada no Viva-Voz
1. Garanta que o **Lenovo LOQ 15** e o **iPhone 13** estejam na **mesma rede Wi-Fi**.
2. **Liberar Firewall (fazer apenas 1 vez se o Safari não carregar):**
   Abra o PowerShell como **Administrador** e rode:
   ```powershell
   New-NetFirewallRule -DisplayName "VoiceBridge AI iPhone" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
   ```
3. **Escolha o modo de chamada:**
   - **Chamada no Notebook + Tela no iPhone 13:** Rode `.\.venv\Scripts\python.exe main.py --mode interview`, abra `http://192.168.15.71:8000` (ou o IP exibido no terminal) no Safari do iPhone e apoie o celular logo abaixo da webcam do notebook.
   - **Chamada no Viva-Voz do iPhone 13 ao lado do Notebook:** Rode com a flag de captação de sala:
     ```powershell
     .\.venv\Scripts\python.exe main.py --room-mic
     ```

---

### Cenário D: Gravar Vídeos / Pitch em Inglês (Modo Teleprompter)
1. Copie o texto do seu roteiro em inglês (`Ctrl + C`).
2. Rode:
   ```powershell
   cd C:\VoiceBridgeAI
   .\.venv\Scripts\python.exe main.py --mode script
   ```
3. Clique em **`📋 Paste`** na barra superior do overlay (ou cole pelo Safari do iPhone 13).
4. Comece a ler em voz alta: o `faster-whisper` + `rapidfuzz` acompanha sua voz e rola o texto automaticamente no seu ritmo.

---

### Cenário E: Como Adaptar o Cérebro para uma Nova Vaga
Sempre que surgir uma entrevista nova (ex.: PIT Solutions, Vivo, vagas internacionais):
1. Edite o arquivo `C:\VoiceBridgeAI\config\profile_context.md` adicionando os requisitos da vaga e 3–4 respostas curtas no topo do arquivo.
2. O `CopilotEngine` recarrega o contexto automaticamente a cada pergunta.

### Tabela de Atalhos Globais (Funcionam com Meet/Teams/OBS em Foco)
| Atalho | Ação |
| :--- | :--- |
| `Ctrl + Shift + M` | Alterna entre **📜 SCRIPT** (Teleprompter) e **🎙️ INTERVIEW** (Co-Piloto) |
| `Ctrl + Shift + H` | Oculta / Mostra a janela instantaneamente |
| `Ctrl + Shift + Space` | Pausa / Retoma a rolagem automática |
| `Esc` | Encerra a aplicação com segurança |

---

## 3. Manual de Engenharia de Prompt & Gestão de Tokens (Para Agentes IA)

Para desenvolver projetos complexos sem estourar cotas de modelos pagos (como Claude Opus/Sonnet) e sem gerar código quebrado (`# TODO`):

1. **Regra 1 — Grounding Antes do Código:** Sempre crie um `AGENT_SPEC.md` na raiz antes de abrir o agente IDE, fixando hardware (RTX 2050 4GB VRAM), stack e restrições.
2. **Regra 2 — Roteamento por Custo/Capacidade:**
   - **Leitura, Planejamento e Markdown (`README`, docs):** Use **Gemini Flash** (ultrarrápido, quase zero consumo de cota).
   - **Escrita de Código Cirúrgico (Backend / UI):** Use **GPT-OSS 120B (Medium)** ou **Claude Sonnet (Thinking)**. Evite **Opus** para tarefas rotineiras.
3. **Regra 3 — Isolamento de Repositórios:** Nunca jogue pastas de referência externa (`C:\Users\bxtna\Documents\GitHub-Referencia`) dentro do workspace ativo. Mantenha-as fora e aponte o caminho apenas se precisar extrair um padrão específico.
4. **Regra 4 — Commits por Marco:** Sempre faça `git commit` após cada fase validada (ex.: `v1.0` desktop -> `v1.1` mobile/echo-gate) para ter ponto de restauração imediato (`git reset --hard`).

---

## 4. Prompts Prontos para a Próxima Sessão (Copiar & Colar no Agente)

### Prompt 1 — Hotfix Rápido (Tirar Erro 404 da Groq + Atualizar README GitHub)
*Use com **Gemini 3.8 Flash** ou **GPT-OSS 120B** no Antigravity IDE:*

> "Atue como Engenheiro de Software Sênior em `C:\VoiceBridgeAI`. Execute duas atualizações rápidas e faça commit:
> 1. Em `ai/copilot.py`, altere a lista de prioridade de modelos da Groq para tentar **`openai/gpt-oss-120b`** primeiro e **`openai/gpt-oss-20b`** como fallback (removendo `llama-3.3-70b-versatile` que retornou HTTP 404 nos testes em produção).
> 2. Atualize o `README.md` em inglês profissional para refletir a **v1.1** já implementada: corrija o link de `git clone` para `https://github.com/yago-silva-ads/voicebridge-ai.git`, adicione a documentação do **Half-Duplex Echo Gate** (uso sem fone), a flag `--room-mic` e o **iPhone 13 Wi-Fi Companion (`web_companion.py`)** na porta `8000`.
> 3. Valide a sintaxe de `ai/copilot.py` e execute `git add . && git commit -m "fix: prioritize gpt-oss-120b on Groq and update README for v1.1" && git push`."

---

### Prompt 2 — Evolução v1.2 (QR Code no Terminal + Seletor de Áudio)
*Use quando quiser deixar o pareamento com o iPhone 13 em 1 segundo:*

> "Atue como Engenheiro Python em `C:\VoiceBridgeAI`. Implemente duas melhorias de usabilidade para a v1.2:
> 1. **QR Code no Terminal (`qrcode`):** Adicione `qrcode` ao `requirements.txt`, instale na `.venv` e exiba um QR Code ASCII limpo no terminal ao iniciar o `web_companion.py`, permitindo escanear o endereço `http://IP:8000` direto com a câmera do iPhone 13 sem digitar nada.
> 2. **Flag `--list-devices` e `--mic-index`:** Adicione argumentos CLI em `main.py` para listar dispositivos de áudio disponíveis no Windows e permitir escolher manualmente o índice do microfone caso haja múltiplos dispositivos virtuais (como NVIDIA Broadcast).
> 3. Valide a sintaxe e faça commit na branch `main`."

---

### Prompt 3 — Evolução SaaS v2.0 (Empacotamento `.exe` + Cloud API)
*Use quando for transformar o projeto em produto comercializável:*

> "Atue como Arquiteto SaaS. Crie um plano técnico (`SAAS_ROADMAP.md`) detalhando como empacotar o `VoiceBridge AI` em um instalador Windows `.exe` de 1 clique (PyInstaller/Nuitka) com modo Cloud leve (enviando áudio para Whisper API / Groq sem exigir GPU NVIDIA local), autenticação de usuários e planos Free (BYOK) vs. Pro."