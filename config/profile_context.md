# Yago Santos Silva — Comprehensive Profile & Interview Co-Pilot Context

## 1. Executive Summary & Core Identity
- **Name:** Yago Santos Silva
- **Location:** Guarulhos, São Paulo, Brazil (Remote Global availability, UTC-3)
- **Education:** Análise e Desenvolvimento de Sistemas (ADS) — Senac São Paulo
- **Academic Research:** CIC / PICTA Researcher — Specializing in Web Accessibility (WCAG 2.1 / 2.2, Screen Readers) and Applied AI (Flutter, Supabase, Gemini API, Python).
- **Core Engineering:** Python, Dart/Flutter, Java, JavaScript/TypeScript, SQL, Playwright, n8n, AI Agents, Linux/Windows.
- **Languages:** Portuguese (Native), English (B1/B2 Working Proficiency — reads docs daily, fluent in technical terminology, actively training live conversation).

---

## 2. Specialized Track: International Web Accessibility & QA Engineering

### 2.1 International Standards & Regulatory Compliance
- **WCAG 2.1 & 2.2 Mastery:** Deep practical knowledge of Principles (Perceivable, Operable, Understandable, Robust) across Level A, AA, and AAA criteria.
  - *WCAG 2.2 focus:* Focus Appearance (2.4.11), Focus Not Obscured (2.4.12), Dragging Movements (2.5.7), Target Size Minimum (2.5.8), Accessible Authentication (3.3.7), Redundant Entry (3.3.8).
  - *Legal Frameworks:* ADA Title III compliance, Section 508 (US Rehabilitation Act), EN 301 549 (European accessibility requirement for ICT products).
- **Assistive Technology (AT) Auditing:**
  - **NVDA (NonVisual Desktop Access):** Daily hands-on testing of screen reader flows, virtual buffer navigation, landmarks (`role="banner"`, `"main"`, `"navigation"`, `"contentinfo"`), live regions (`aria-live="polite" / "assertive"`), table navigation, and interactive widget accessibility.
  - **Keyboard Navigation & Focus Management:** Tab order inspection, skip links (`Skip to main content`), roving tabindex, escape key modal dismissal, focus trapping within dialogs, and elimination of focus loss upon dynamic DOM mutations.
- **Automated & Manual Diagnostic Tooling:**
  - **Axe DevTools (Deque):** Automated static DOM rule checking, false-positive filtering, zero-issue CI/CD gating.
  - **WAVE (WebAIM):** Visual evaluation of document outline, contrast errors, orphaned form labels, structural hierarchy.
  - **Lighthouse (Chrome):** Performance and Accessibility scoring, contrast analysis, touch target sizing.
  - **Color Contrast Analyser (CCA):** Ensuring 4.5:1 contrast for normal text and 3:1 for large text/graphical UI components.

### 2.2 Code-Level Remediation (HTML5, CSS, Modern JS)
- **Semantic HTML First:** Prioritizing native elements (`<button>`, `<a>`, `<dialog>`, `<nav>`, `<input>`) over generic `div`/`span` soups to inherit native accessibility semantics, roles, and keyboard bindings without fragile ARIA patches.
- **Precise ARIA Usage (Rule 1 of ARIA):** Using ARIA only when semantic HTML cannot represent the pattern; proper implementation of `aria-expanded`, `aria-controls`, `aria-haspopup`, `aria-describedby`, and accessible naming calculation (`accname`).
- **Responsive & Visual Accessibility:** 200% text resizing and 400% page zoom without horizontal scrolling or content truncation; respecting `prefers-reduced-motion` and dark/light system themes.

### 2.3 Regulatory Rigor & QA Discipline (LATAM Airlines — 2 Years SGSO)
- **LATAM Airlines SGSO (Safety Management System / Sistema de Gerenciamento da Segurança Operacional):**
  - Managed operational safety documentation, regulatory audit compliance, root-cause investigations, and defect reporting in high-stakes aviation operations.
  - **Transferable Value to QA & Accessibility:** In aviation, safety non-compliance leads to critical incidents; in software, accessibility non-compliance leads to lawsuits, exclusion of disabled users, and blocked government contracts. Yago brings aviation-grade audit trails, structured bug reporting, risk classification, and zero-compromise compliance mindset to software QA teams.
- **Customer Empathy & Front-Line Experience:** Front-line customer service at LATAM Airlines, Nike, and Rappi provided direct insight into end-user friction, cognitive overload, and diverse user needs under stress.

---

## 3. Real-Time Interview Responses & STAR Stories (Consolidated from ENTREVISTA_AIR_RESPOSTAS.md)

### 1. "Fale um pouco sobre você." / "Tell me about yourself."
- **EN:** "I'm Yago, based in São Paulo. I study Systems Analysis and Development at Senac and conduct accessibility and AI research at PICTA. Before transitioning into software engineering, I worked in frontline customer operations at LATAM Airlines, Nike, and Rappi, so I understand users from the ground up. Today, I build autonomous AI and automation systems. Most notably, I single-handedly built a CRM tracking 5,839+ contacts with 24/7 n8n workflows and Meta API integration, as well as an autonomous job application bot with rigorous validation gates. I combine technical automation with an unwavering commitment to compliance and user accessibility."
- **PT:** Sou o Yago, de Guarulhos, e estudo Análise e Desenvolvimento de Sistemas no Senac. Também sou pesquisador no CIC/PICTA, onde trabalho com acessibilidade e IA. Antes da tecnologia trabalhei com atendimento ao cliente na LATAM, na Nike e na Rappi, então conheço o cliente do lado de quem atende. Hoje construo automações com IA que rodam sozinhas. A que mais me marcou foi um CRM que montei sozinho numa campanha, com mais de 5.800 registros, automação no n8n e integração com a API da Meta. Foi ali que eu vi que dados bem organizados mais IA geram resultado.

### 2. "Por que você escolheu essa trilha / tecnologia?" / "Why this track / company?"
- **EN:** "Because I have already built CRM and automation pipelines from scratch using raw databases, APIs, and n8n workflows. I want to build at enterprise scale using industry-standard platforms. Furthermore, AI delivers its highest immediate ROI in customer journeys, support, and sales pipelines. I bring both perspectives: hands-on customer empathy and software engineering rigor."
- **PT:** Porque eu já fiz CRM na prática, mas do jeito artesanal: planilha, banco e automação montados por mim. Quero aprender a fazer isso na plataforma que as empresas usam de verdade. E CRM é onde a IA dá retorno mais direto: atendimento, vendas, jornada do cliente. Junta as duas coisas que eu tenho, a experiência com cliente e a com automação e desenvolvimento.

### 3. "Conte sobre um projeto de que você se orgulha." / "A project you are proud of."
- **EN:** "Caçador de Vagas ('Job Hunter'). Applying manually to dozens of roles was time-consuming. I built an automated agent in Python with Playwright that crawls multiple job boards, filters by strict profile matching, crafts targeted resumes per role, and applies autonomously. Crucially, I implemented security gates: the bot never submits false information, and only logs an application as successful when concrete evidence (confirmation DOM element / email receipt) is captured. It has delivered 64+ verified applications with a live dashboard, automated test suites, and CI/CD."
- **PT:** O Caçador de Vagas. Eu precisava me candidatar a muitas vagas e isso tomava horas. Construí em Python com Playwright um sistema que busca vagas em várias plataformas, filtra pela minha adequação, gera um currículo específico para cada vaga e se candidata sozinho. Coloquei regras de segurança: ele nunca responde uma pergunta com informação falsa e só registra a candidatura como enviada quando tem evidência. Já são 64 candidaturas enviadas com sucesso, com painel, testes automatizados e integração contínua. O que mais aprendi foi qualidade de dados: confiar no número só depois de checar a fonte.

### 4. "Como você lida com erros? Conte um." / "How do you handle errors? Give an example."
- **EN:** "While reviewing production reports for Caçador de Vagas, our dashboard suddenly indicated over 400 failed submissions. Before attempting any code changes, I traced the data origin and discovered that our automated test suites were dumping mock failures into the live production database. I properly isolated the test environment, restored clean production logs from a verified backup, and revealed the actual failure count was only 31. This taught me never to make engineering decisions based on dirty metrics—always audit the raw data source first."
- **PT:** Revisando o Caçador de Vagas, o relatório mostrava mais de 400 falhas de envio. Antes de corrigir qualquer coisa, fui olhar a fonte dos dados e descobri que os testes automatizados estavam gravando dados falsos no log real. Corrigi o isolamento dos testes, limpei os dados com backup e o número real era 31 falhas. Aprendi a validar o dado antes de tomar decisão, o que vale muito em CRM e auditorias, onde uma decisão errada vem de um dado sujo.

### 5. "Você já usou a ferramenta X?" / "Have you used this specific platform before?"
- **EN:** "I believe in absolute technical honesty: I haven't used that specific platform in production daily yet, but I have built its foundational concepts from the ground up: relational data schemas, webhook integrations, automation pipelines (analogous to Salesforce Flow or Jira automations), and AI agentic loops. I learn fast through official documentation, sandboxes, and hands-on builds."
- **PT:** Ainda não usei no dia a dia, e quero ser honesto sobre isso. Mas já construí na prática o que a ferramenta faz: banco de dados, automações no n8n, integração por API e agentes de IA. Aprendo construindo e validando em projetos reais.

### 6. "Como você aprende uma tecnologia nova rápido?" / "How do you learn fast?"
- **EN:** "By building directly against a real-world problem. I study official documentation, use AI agents as acceleration accelerators, and establish automated unit tests to verify behavior. I never accept code or outputs without running and validating them against real test cases. That is how I mastered Playwright, n8n, Flutter, and assistive tech auditing tools."
- **PT:** Construindo. Escolho um problema real, leio a documentação e uso IA como apoio, mas sempre testando o resultado: não confio no que a IA gera sem validar. Foi assim que aprendi Playwright, n8n e Flutter.

### 7. "Como você usa IA no seu dia a dia?" / "How do you use AI daily?"
- **EN:** "I orchestrate multiple specialized AI agents for planning, drafting, and code generation. However, human verification is the critical gatekeeper: I treat AI outputs as untrusted submissions until proven by automated tests and manual inspection. Just recently, an AI subagent claimed all tests passed, but my verification suite caught three broken assertions. AI accelerates development, but accountability rests entirely with me."
- **PT:** Uso para programar, automatizar e revisar, e trabalho com vários agentes de IA ao mesmo tempo, dividindo tarefas entre eles. Mas o meu papel é validar: reprovo entregas de IA sempre que os testes reais quebram. IA acelera, mas a responsabilidade pelo resultado é minha.

### 8. "Fale de uma situação difícil com um cliente / stakeholder."
- **EN:** "During my time in customer operations, an upset customer experienced an urgent service breakdown. Instead of becoming defensive or citing rigid company rules, I practiced active listening to identify their exact blocker, de-escalated the situation, coordinated directly with the operations team to expedite a resolution, and provided transparent updates. The customer departed reassured and satisfied. The takeaway: systems and workflows exist to serve human needs, not the other way around."
- **PT:** O cliente estava insatisfeito com um problema operacional → eu escutei e entendi a causa raiz sem interromper → resolvi coordenando diretamente com a operação interna → o resultado foi a resolução ágil e a fidelização do cliente. Isso me ensinou que processos e CRMs existem para viabilizar a experiência do usuário.

### 9. "Como você trabalha em equipe?" / "How do you work in a team?"
- **EN:** "In university engineering cohorts, we operate using Agile Scrum and Kanban boards with clear sprint goals. In my engineering workflow, I define clear contracts, structured interfaces, and transparent communication. Nothing is marked 'Done' without reproducible test coverage and peer review."
- **PT:** Na faculdade trabalho com Scrum e Kanban nos projetos em grupo. Gosto de comunicação clara: cada um sabe o que é seu, e nada é dado como pronto sem ser conferido com evidências e testes.

### 10. "Onde você se vê daqui a 2 anos?" / "Where do you see yourself in 2 years?"
- **EN:** "Certified in enterprise platforms and accessibility (e.g., IAAP CPACC / WAS certifications or senior developer tracks), working as a high-impact engineer building AI-driven, accessible digital products that serve millions of diverse users worldwide."
- **PT:** Certificado, trabalhando em projetos de tecnologia de grande impacto com IA e acessibilidade, ajudando empresas a elevar o padrão de qualidade de software e conformidade com os usuários.

### 11. "Qual o seu ponto fraco?" / "What is your greatest weakness?"
- **EN:** "First, my spoken English is intermediate-to-advanced technical (B1+), though I read and write documentation fluently. I am closing this gap through immersive live conversation tools and daily practice. Second, I sometimes have the urge to automate every edge case immediately; I have learned to prioritize minimum viable automation and validate high-risk paths first."
- **PT:** Meu inglês falado é intermediário: leio documentação todo dia com tranquilidade, e estou desenvolvendo a conversação contínua. O segundo ponto: às vezes quero automatizar tudo rápido, mas aprendi a validar o essencial primeiro.

### 12. "Disponibilidade" / "Availability & Logistics"
- **Availability:** Immediate availability for remote contracts, full-time or part-time (30h/40h).
- **Time Zone:** UTC-3 (São Paulo), easily overlapping with US Eastern/Pacific and European business hours.
- **Hardware:** Lenovo LOQ 15, Intel Core i5, 16GB DDR5 RAM, NVIDIA RTX 2050 (4GB VRAM, CUDA enabled), dedicated dual-channel audio setup.

---

## 4. Key Takeaways & Operational Rules (Consolidated from ENTREVISTA_AIR_LLIA.md & COLA_ENTREVISTA.md)

### 4.1 Pitch de 60 Segundos (Elevator Pitch)
1. Yago, São Paulo/Guarulhos, ADS Senac SP, pesquisador PICTA (acessibilidade digital WCAG + IA).
2. Bagagem de atendimento e conformidade operacional: LATAM Airlines (2 anos SGSO), Nike e Rappi.
3. Engenharia de automação autoral: Caçador de Vagas (Python, Playwright, CI/CD, 64 candidaturas comprovadas) e CRM de 5.839+ contatos (n8n, Meta API, SQLite).
4. Foco internacional: Engenharia de Acessibilidade Web (WCAG 2.1/2.2, NVDA, Axe DevTools) e Co-Pilotos de IA em tempo real.

### 4.2 Mini-Glossário de Mapeamento Técnico
| Conceito / Ferramenta | O que é | Projeto Real de Yago |
|---|---|---|
| WCAG 2.1/2.2 Level AA | Padrão global de acessibilidade web | Auditorias PICTA, conformidade semântica HTML5 |
| NVDA Screen Reader | Leitor de tela para Windows | Testes manuais diários de navegação, foco e landmarks |
| Axe DevTools / WAVE | Motores de varredura estática de a11y | Testes automatizados e triagem de falso-positivos |
| SGSO (LATAM Airlines) | Sistema de Gerenciamento da Segurança Operacional | 2 anos de rigor de conformidade, auditoria e rastreabilidade |
| Playwright / Python | Automação e web scraping de navegadores | Caçador de Vagas com gates de evidência |
| n8n / REST APIs | Orquestração de workflows 24/7 | Campanha 4090 (5.839+ leads integrados via Meta API) |
| Faster-Whisper + Groq | Transcrição local CUDA + inferência <400ms | VoiceBridge AI (co-piloto e teleprompter stealth) |

### 4.3 Checklist de Entrevista ao Vivo (Live Interview Execution)
1. Câmera alinhada na altura dos olhos (o teleprompter PyQt6 fica colado logo abaixo da lente física para garantir contato visual natural).
2. Stealth overlay ativado (`WDA_EXCLUDEFROMCAPTURE`), garantindo invisibilidade total em compartilhamento de tela no Zoom/Teams/Meet.
3. Fone de ouvido conectado antes de iniciar o loopback WASAPI.
4. Pausas de 1.75s configuradas para aguardar o término real das perguntas do entrevistador.
5. Formatação de fala concisa: 1ª linha de abertura contextualizada + 2 a 3 tópicos de no máximo 14 palavras cada com pausas marcadas por `|`.
