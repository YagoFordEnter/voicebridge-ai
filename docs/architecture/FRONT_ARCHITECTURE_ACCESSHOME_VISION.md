# FRONT-END ARCHITECTURE, DESIGN SYSTEM & ACCESSHOME INTEGRATION

- **Autor:** Yago Santos Silva (`YagoFordEnter`)
- **Escopo:** Padrão Visual Unificado (VoiceBridge AI, Portfólio & Aplicações Web)
- **Pesquisa Base:** PICTA 2026 — Acessibilidade Digital em Interfaces de Smart Homes (WCAG 2.2 / eMAG 3.1 / NVDA)

---

## 1. Posicionamento & Verdade de Produto
Os sistemas desenvolvidos neste ecossistema partem de uma premissa clara de **Engenharia Centrada no Ser Humano e Desenho Universal**:
- **VoiceBridge AI (Acessibilidade Cognitiva & Linguística):** Não é uma ferramenta voltada à deficiência auditiva, mas sim um **co-piloto de fluência e redução de carga cognitiva** para profissionais não-nativos em inglês e pessoas sob alta pressão comunicacional (entrevistas técnicas, reuniões internacionais e apresentações).
- **AccessHome Analyzer (Auditoria & Inclusão Sob Demanda):** Módulo embarcado derivado da pesquisa científica **PICTA 2026** (Centro Universitário Senac). Ele permanece **desativado por padrão** para manter a interface limpa e sem ruído visual, podendo ser **ativado com 1 clique** por recrutadores, auditores ou usuários para inspecionar a acessibilidade real da página em tempo real.

---

## 2. Design System Unificado (Padrão Linear / Vercel / Raycast)

### Regras Inegociáveis de Interface
1. **Zero Emojis:** Nenhum emoji é utilizado em botões, títulos, badges ou textos de interface. Toda sinalização visual usa ícones vetoriais minimalistas (`lucide-react`, `strokeWidth={1.75}`) e etiquetas técnicas em monoespaço.
2. **Tipografia Funcional:**
   - **Interface & Leitura:** `Inter` (hierarquia clara, espaçamento confortável).
   - **Dados, Métricas & Atalhos:** `JetBrains Mono` (latência em ms, scores WCAG, tags de stack e `<kbd>`).
3. **Sistema Dual-Theme (Light & Dark Mode com Contraste AAA/AA):**
   - **Light Mode (Modo Claro):** Fundo `#F8FAFC` (Slate 50) | Cards `#FFFFFF` | Bordas 1px `#E2E8F0` | Texto `#0F172A` | Ação Primária Azul Cobalto `#1D4ED8`.
   - **Dark Mode (Modo Escuro):** Fundo `#090D16` | Cards `#0F172A` | Bordas 1px `#1E293B` | Texto `#F8FAFC` | Ação Primária Azul Safira `#3B82F6`.

---

## 3. Como o AccessHome Analyzer Funciona Dentro dos Projetos (Toggle ON/OFF)

Em vez de ficar apenas como um texto estático no currículo, o **AccessHome Analyzer** é embarcado como um componente React/TypeScript reutilizável (`<AccessHomeInspector />`) no canto da barra de navegação:

- **Estado Padrão (`OFF` — Discreto):** Um botão compacto na barra superior exibe `WCAG Inspector: Off`. A aplicação roda normalmente sem nenhuma interferência visual.
- **Estado Ativo (`ON` — Modo Auditoria PICTA 2026):** Ao clicar para ativar, abre um painel lateral técnico não-destrutivo que executa 4 verificações reais no DOM da página aberta:
  1. **Auditoria Semântica em Tempo Real:** Varre o HTML ativo e contabiliza `<h1>–<h6>`, landmarks (`<header>`, `<main>`, `<nav>`, `<aside>`), botões sem `aria-label` e imagens sem `alt`.
  2. **Simulador de Leitor de Tela (Modo NVDA Preview):** Exibe em tempo real a árvore de acessibilidade falada do elemento que está sob foco do teclado (`Tab`), demonstrando como o NVDA interpreta a página.
  3. **Assistente de Leitura & Contraste:** Permite ativar alto contraste reforçado (`> 7:1`), guia de foco visível ampliado e espaçamento tipográfico para dislexia/baixa visão.
  4. **Relatório de Conformidade:** Exibe o selo dinâmico de aprovação baseado nos critérios da pesquisa PICTA 2026 (`WCAG 2.2 AA` / `eMAG 3.1`).