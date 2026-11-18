# Playbook de Arquitetura & Engenharia de IA: VoiceBridge AI 🎙️🧠

Documento técnico de arquitetura, lições de engenharia reversa e orquestração de modelos de inteligência artificial para o sistema **VoiceBridge AI**.

---

## 1. Visão Arquitetural & Princípios de Engenharia

O **VoiceBridge AI** foi construído para resolver um desafio crítico de acessibilidade comunicacional: permitir que um desenvolvedor não-nativo em inglês participe de entrevistas técnicas em vídeo (Google Meet, Microsoft Teams, Zoom) com fluidez nativa, mantendo contato visual direto com a câmera e com suporte cognitivo em tempo real.

### Princípios Norteadores:
1. **Local-First & Hardware-Aware:** Toda a captura de áudio e transcrição Whisper roda localmente na GPU dedicada (NVIDIA GeForce RTX 2050 4GB VRAM), operando em quantização `int8_float16` para manter o consumo de VRAM abaixo de ~700 MB.
2. **Invisibilidade Criptográfica em Tela Compartilhada (Stealth Overlay):** Utilização da API de baixo nível do Windows (`ctypes.windll.user32.SetWindowDisplayAffinity` com `WDA_EXCLUDEFROMCAPTURE = 0x00000011`). A interface PyQt6 é renderizada para os olhos do usuário no monitor, mas é excluída pelo compositor do Windows (DWM) de qualquer captura de tela (Zoom, Teams, Meet, OBS).
3. **Desacoplamento Assíncrono com Filas Thread-Safe:** Nenhuma computação pesada bloqueia o Event Loop do PyQt6. A captura de áudio, transcrição e chamadas de streaming LLM operam em threads daemon desacopladas comunicando-se via `queue.Queue` e sinais Qt (`pyqtSignal`).

---

## 2. Engenharia Reversa do Script Validado (`cola_entrevista.py`)

O VoiceBridge AI não partiu do zero: ele evoluiu as lições empíricas validadas em produção no script `C:\CacadorDeVagas\tools\cola_entrevista\cola_entrevista.py` (utilizado na entrevista AI/R Fellowship):

| Desafio Encontrado em Produção | Causa Raiz Identificada | Solução Adotada no VoiceBridge AI |
|---|---|---|
| **Perda de pacotes no Loopback WASAPI** | Executar a captura de áudio do sistema (`soundcard`) dentro de uma thread Python sofria interferência de concorrência e causava estouro de buffer no Windows. | **Isolamento de Subprocesso Dedicado:** A captura WASAPI roda num subprocesso Python separado com flag `--rec-loopback`, transmitindo buffers brutos `float32` prefixados com tamanho via `stdout.buffer`. |
| **Corte prematuro da fala do entrevistador** | Threshold de silêncio padrão de 0.75s cortava perguntas no meio de pausas reflexivas do entrevistador. | **Calibração de 1.75s:** Janela de 7 chunks de 0.25s (~1.75s) sem volume RMS significativo antes de disparar o processamento, com limite de segurança em 30s para evitar buffers infinitos. |
| **Latência alta em chamadas LLM clássicas** | Provedores comerciais tradicionais ou modelos locais sem quantização demoram >2-3 segundos para responder. | **Groq API Streaming com Cascata:** Inferência em LPU na nuvem Groq (`llama-3.3-70b-versatile` com fallback para `gpt-oss-120b` e `gpt-oss-20b`), entregando o primeiro token em menos de 400ms. |
| **Instabilidade com chaves no .env** | Reiniciar a aplicação para atualizar uma API key expirada quebra o fluxo de uma entrevista ao vivo. | **Hot-Reload de Ambiente:** `load_dotenv(override=True)` executado internamente antes de cada requisição do co-piloto, permitindo colar uma nova chave sem fechar a janela. |

---

## 3. Fluxo Multi-Modelo & Orquestração Cognitiva

O VoiceBridge AI implementa uma pipeline cognitiva dividida em três camadas:

```
[ Camada 1: Grounding & Perfil Pessoal ]
               │
               ▼
   config/profile_context.md
   • Experiência e rigor LATAM SGSO (2 anos)
   • Auditorias WCAG 2.1/2.2 e NVDA no PICTA
   • Casos reais STAR (Caçador de Vagas, CRM 5.839 leads)
               │
               ▼
[ Camada 2: Transcrição Local Ultrarrápida ]
   faster-whisper (base.en / int8_float16 / CUDA)
   • Loopback: Converte pergunta falada em texto limpo
   • Microfone: Rastreia a fala do Yago via rapidfuzz
               │
               ▼
[ Camada 3: Inferência & Formatação de Fala Humana ]
   Groq API (Llama 3.3 70B / Fallbacks GPT-OSS)
   • System Prompt calibrado para discurso natural
   • Primeira linha = resposta completa de impacto
   • 2-3 tópicos de no máximo 14 palavras
   • Marcadores de respiração e pausa ("|")
```

### Por Que a Combinação Grounding + Streaming Rápido?
Em uma entrevista técnica em inglês, o candidato tem cerca de 2 a 3 segundos de janela social aceitável antes de começar a falar. O prompt de sistema do VoiceBridge AI instrui o modelo a:
1. **Nunca alucinar dados:** Utilizar estritamente os fatos auditados do `profile_context.md`.
2. **Entregar ritmo de leitura:** Frases curtas e objetivas intercaladas pelo caractere `|`, que a interface PyQt6 converte visualmente em quebras de linha com marcadores de tópicos para leitura sem tropeços.

---

## 4. Rastreamento de Voz e Rolagem Automática (`rapidfuzz`)

No modo **SCRIPT** (Teleprompter de pitch e apresentações):
- O microfone ouve a leitura do usuário em tempo real.
- O motor `faster-whisper` emite pequenos blocos de texto.
- A classe `ScriptMatcher` realiza um alinhamento fuzzy através de janela deslizante baseada em Levenshtein (`fuzz.token_set_ratio`).
- O cursor de leitura é atualizado de forma monotônica crescente (permitindo pequenas releituras sem saltos bruscos).
- A UI rola verticalmente e destaca visualmente as palavras ativas em azul brilhante translúcido.

---

## 5. Atalhos Globais e Operabilidade Windows

Utilizando a biblioteca `pynput.keyboard.GlobalHotKeys` em uma thread daemon desacoplada:
- `Ctrl + Shift + H`: Oculta ou exibe o overlay instantaneamente (útil para checar rapidamente uma janela embaixo).
- `Ctrl + Shift + M`: Alterna na hora entre o modo **SCRIPT** e o modo **INTERVIEW**.
- `Ctrl + Shift + Space`: Congela a rolagem ou reativa a sincronização de voz.
- Esses atalhos respondem mesmo se o Google Chrome (Meet), Microsoft Teams, Zoom ou OBS estiverem em foco e em tela cheia.

---

## 6. Checklist de Validação em Produção

1. **Hardware:** RTX 2050 (4GB) com driver CUDA 12/13 OK.
2. **Ambiente:** `.venv` isolado com `ctranslate2` reportando 1 GPU CUDA ativa.
3. **Invisibilidade:** Testado e aprovado com `SetWindowDisplayAffinity(hwnd, 0x00000011)`.
4. **Resiliência:** Fallback automático para CPU `int8` implementado caso a GPU sofra pico de memória por aplicações 3D ou streaming externo.
