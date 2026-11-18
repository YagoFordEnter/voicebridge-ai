# Cola de Entrevista (copiloto ao vivo)

Criada em 27/10/2026 e usada na entrevista AI/R Fellowship com a Llia.

**Código:** `C:\CacadorDeVagas\tools\cola_entrevista\cola_entrevista.py`
**Rodar:** `python C:\CacadorDeVagas\tools\cola_entrevista\cola_entrevista.py` (Esc fecha; arrastar a janela para perto da câmera)

## Como funciona
1. Ouve o áudio que sai do PC (loopback da saída padrão), num processo separado para não perder áudio.
2. Transcreve no próprio PC com faster-whisper `base`.
3. Mostra na hora um card pronto (por palavra-chave) e depois o roteiro da IA: frase de abertura + 2-3 tópicos.
4. IA: Groq grátis, `openai/gpt-oss-120b`, que cai para o `gpt-oss-20b` se bater no limite. Usa só fatos de [[ENTREVISTA_AIR_RESPOSTAS]]. A Anthropic é opcional (paga).
5. Chaves no `C:\CacadorDeVagas\.env`, só pelos nomes: `GROQ_API_KEY` e `ANTHROPIC_API_KEY` (opcional).

## Ajustes depois da entrevista
- Respondia antes de a Llia terminar a pergunta. Agora espera ~1,75 s de silêncio (antes 0,75 s) e só corta trechos longos depois de 30 s.

## Atenção
- Conecte o fone ANTES de abrir a cola: ela escuta a saída de som que estava como padrão quando abriu.
- Para outra vaga: troque `ENTREVISTA_AIR_RESPOSTAS.md` no código e os `CARDS`.
- Pendente: ler o banco do CacadorDeVagas e o LinkedIn e analisar a empresa automaticamente.
