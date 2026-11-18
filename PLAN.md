# Plano de Evolução Modular: VoiceBridge AI

Com base na engenharia reversa do script validado `C:\CacadorDeVagas\tools\cola_entrevista\cola_entrevista.py`, nos requisitos do `AGENT_SPEC.md` e nas restrições de hardware (Lenovo LOQ 15, RTX 2050 4GB VRAM, CUDA):

## Lições Essenciais Extraídas do `cola_entrevista.py`
1. **Loopback em Processo Separado:** No Windows, o gravador de loopback WASAPI perde pacotes de áudio quando executado dentro de uma thread compartilhada; isolá-lo em subprocesso (`python -W ignore ... --rec`) com leitura contínua via `stdout.buffer` garante estabilidade contínua.
2. **Threshold de Silêncio Ajustado:** Janela de ~1.75s (7 chunks sem som após fala) é o ponto ideal para consolidar a pergunta do entrevistador sem cortar pausas naturais de pensamento.
3. **Resiliência de Modelos Groq:** Fallback automático entre modelos de baixa latência (`llama-3.3-70b-versatile` / `openai/gpt-oss-120b` -> `gpt-oss-20b`) com streaming direto.

---

## Estrutura Modular dos 4 Arquivos Python

```text
C:\VoiceBridgeAI\
├── requirements.txt
├── PLAN.md
├── main.py                     # Orquestrador / Entrypoint
├── ui/
│   └── overlay.py              # [1] Interface PyQt6 Translúcida + WDA_EXCLUDEFROMCAPTURE
├── audio/
│   └── capture.py              # [2] Captura Dual (Microfone + Loopback WASAPI em subprocesso)
├── ai/
│   ├── transcriber.py          # [3] faster-whisper (CUDA int8_float16) + rapidfuzz (Scroll)
│   └── copilot.py              # [4] Co-Piloto Groq API streaming com config/profile_context.md
```

### 1. `ui/overlay.py` — Interface PyQt6 Stealth
- **Posicionamento & Estilo:** Janela frameless, fundo escuro translúcido (`rgba(18, 18, 18, 0.92)`), `Qt.WindowType.WindowStaysOnTopHint`, fixada no topo central (logo abaixo da webcam para contato visual direto).
- **Invisibilidade em Compartilhamento de Tela:** Aplicação de `ctypes.windll.user32.SetWindowDisplayAffinity(int(self.winId()), 0x00000011)` (`WDA_EXCLUDEFROMCAPTURE`), garantindo invisibilidade no Zoom, Microsoft Teams, Google Meet e OBS screen capture.
- **Modos de Exibição:** 
  - Modo Teleprompter: texto com rolagem suave guiada pelo sinal do `rapidfuzz`.
  - Modo Co-Piloto: exibição de tópicos de fala em tempo real para a pergunta ouvida.
- **Atalhos e Controles:** Arraste livre com mouse, `Esc` para minimizar/fechar, atalhos de pausa/continuação.

### 2. `audio/capture.py` — Captura Dual-Channel
- **Canal 1 (Interviewer - Loopback):** Mantém a abordagem comprovada de `soundcard` rodando isolado em subprocesso (`--rec-loopback`), capturando áudio do sistema com silêncio calibrado (1.75s) para enviar blocos de áudio da pergunta.
- **Canal 2 (Yago - Microfone):** Captura contínua do microfone físico via `sounddevice` / `soundcard` em chunks curtos de 0.5s a 1.0s para o motor de transcrição do Yago, com fila thread-safe `queue.Queue`.

### 3. `ai/transcriber.py` — Transcrição & Rolagem por Voz (Voice-Tracking)
- **Engine Whisper:** `faster-whisper` com modelo `base.en` (ou `tiny.en`), configurado para `device="cuda"`, `compute_type="int8_float16"` (consumo inferior a ~700MB na RTX 2050), com fallback seguro para CPU `int8`.
- **Sincronizador Fuzzy (`rapidfuzz`):** 
  - Recebe o texto falado por Yago em tempo real.
  - Compara a janela de palavras recentes com o roteiro carregado no teleprompter usando `fuzz.partial_ratio` e alinhamento de tokens.
  - Calcula a posição exata da fala no script e emite sinais PyQt para avançar a rolagem vertical suavemente.

### 4. `ai/copilot.py` — Co-Piloto de Entrevista LLM
- **Carregamento de Perfil:** Leitura dinâmica de `config/profile_context.md` (resumo técnico do Yago, pesquisa PICTA WCAG 2.1/2.2, NVDA, LATAM SGSO, STAR stories).
- **Streaming Groq:** Chamada com baixa latência (<400ms) utilizando a biblioteca `groq`:
  - Modelo principal: `llama-3.3-70b-versatile` (com fallback para `openai/gpt-oss-120b` / `20b`).
  - System Prompt calibrado para respostas em formato falado natural: primeira frase contextualizada pronta para pronunciar + 2 a 3 tópicos curtos (máximo 14 palavras por tópico) separados por `|` para ritmo de fala.
