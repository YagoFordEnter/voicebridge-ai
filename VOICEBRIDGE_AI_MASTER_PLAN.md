
# VOICEBRIDGE AI — Co-Piloto de Acessibilidade, Teleprompter & Engenharia Reversa

## 1. Visão & Propósito (Projeto Autoral — Yago Santos Silva)
Sistema desktop local em Python (`C:\VoiceBridgeAI`) projetado como ferramenta de acessibilidade comunicacional e co-piloto em tempo real para entrevistas técnicas internacionais em inglês (Teams, Meet, LinkedIn) e gravação de pitches em vídeo sem perda de contato visual.

## 2. Conexões no Grafo (`CEREBRO_YAGO`)
- Base Validada (Código Existente): [[COLA_ENTREVISTA]] (`C:\CacadorDeVagas\tools\cola_entrevista\cola_entrevista.py`)
- Contexto Técnico & Respostas: [[ENTREVISTA_AIR_RESPOSTAS]] | [[ENTREVISTA_AIR_LLIA]]
- Arsenal de Engenharia Reversa & Skills: `C:\Users\bxtna\Documents\GitHub-Referencia` (`morluto_rea`, `Panniantong_Agent-Reach`, `google_skills`, `Leonxlnx_taste-skill`)

## 3. Arquitetura Técnica (Hardware: Lenovo LOQ 15 — RTX 2050 4GB VRAM)
1. **Stealth Overlay Teleprompter (`PyQt6`):**
   - Janela *frameless*, fundo escuro translúcido, `Always on Top` posicionada colada sob a webcam.
   - Invisibilidade nativa em compartilhamento de tela via Windows API (`SetWindowDisplayAffinity` -> `WDA_EXCLUDEFROMCAPTURE`).
2. **Áudio Dual-Channel & Rolagem por Voz:**
   - **Saída do Sistema (WASAPI Loopback):** Captura a pergunta do entrevistador (evolução do loopback já validado no `cola_entrevista.py`).
   - **Microfone + `faster-whisper` (`base.en` quantizado `int8_float16` na RTX 2050) + `rapidfuzz`:** Ouve o inglês falado pelo Yago em tempo real, destaca a palavra atual e rola o texto suavemente no ritmo da fala (pausando automaticamente em hesitações).
3. **Cérebro Co-Piloto (Zero Custo):**
   - Pipeline rápido via **Groq API** (`llama-3.3-70b-versatile` com fallback para `gpt-oss-20b` / Gemini Flash), lendo `config/profile_context.md` (PICTA WCAG 2.1/2.2, NVDA, Axe, WAVE, Lighthouse + 2 anos LATAM SGSO) e gerando frases curtas de inglês falado natural com pausas marcadas (`|`).
4. **Correção de Contato Visual (Eye-Contact):**
   - Uso nativo do **NVIDIA Broadcast (Eye Contact)** na RTX 2050 em conjunto com o overlay, com módulo opcional em `OpenCV + MediaPipe Face Mesh + pyvirtualcam`.

## 4. Diretriz de Engenharia Reversa para o Agente Antigravity
- **NÃO copiar** repositórios brutos para dentro de `C:\VoiceBridgeAI`.
- Utilizar as ferramentas externas instaladas em `Documents\GitHub-Referencia` (`morluto_rea` para engenharia reversa e `Panniantong_Agent-Reach` para mineração de padrões no GitHub) + reutilizar a base funcional de `C:\CacadorDeVagas\tools\cola_entrevista\cola_entrevista.py`.