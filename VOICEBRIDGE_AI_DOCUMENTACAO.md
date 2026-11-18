# VOICEBRIDGE AI — Arquitetura, Engenharia Reversa & Playbook de IA

- **Data de Construção:** 18/11/2026
- **Autor:** Yago Santos Silva
- **Diretório:** `C:\VoiceBridgeAI`
- **Hardware Alvo:** Lenovo LOQ 15 | Intel Core i5 | 16GB RAM | NVIDIA RTX 2050 (4GB VRAM)
- **Conexões no Grafo:** [[COLA_ENTREVISTA]] | [[ENTREVISTA_AIR_RESPOSTAS]] | [[ENTREVISTA_AIR_LLIA]] | [[VOICEBRIDGE_AI_MASTER_PLAN]] | [[CACADOR_ESTADO_2026-10-12]]

---

## 1. Visão Geral & Propósito
Assistente desktop local de **acessibilidade comunicacional e co-piloto para entrevistas técnicas em inglês** e gravação de pitches em vídeo. Resolve dois gargalos simultâneos sem depender de serviços pagos:
1. **Leitura natural sem perda de contato visual:** Teleprompter translúcido posicionado sob a webcam, com rolagem automática guiada pela própria voz do usuário e invisível em compartilhamentos de tela.
2. **Suporte cognitivo em tempo real:** Escuta ativa da pergunta do entrevistador via loopback do sistema e geração de tópicos curtos em inglês falado natural baseados no perfil real do Yago.

---

## 2. Arquitetura Modular (`C:\VoiceBridgeAI`)

```text
C:\VoiceBridgeAI\
├── AGENT_SPEC.md                  # Especificação arquitetural permanente para agentes
├── PLAN.md                        # Plano enxuto de execução gerado na Fase 1
├── requirements.txt               # Dependências isoladas do ambiente virtual
├── .env / .env.example            # Chaves de API (GROQ_API_KEY)
├── config/
│   └── profile_context.md         # Base de conhecimento (PICTA, LATAM SGSO, projetos, STAR)
├── audio/
│   └── capture.py                 # Captura Dual-Channel (Subprocesso Loopback + Thread Mic)
├── ai/
│   ├── transcriber.py             # Motor faster-whisper (CUDA int8_float16 / fallback CPU)
│   ├── script_matcher.py          # Sincronização fuzzy (rapidfuzz) para auto-scroll por voz
│   └── copilot.py                 # Cascata LLM Groq em streaming com hot-reload de .env
├── ui/
│   └── overlay.py                 # Janela PyQt6 Stealth (Always-on-Top + WDA_EXCLUDEFROMCAPTURE)
└── main.py                        # Orquestrador assíncrono via queue.Queue e Sinais Qt