### Como montar o cenário de teste agora (2 minutos)

1. **No PowerShell (`C:\VoiceBridgeAI`):** Rode `.\.venv\Scripts\python.exe main.py --mode interview`
    
2. **No Safari do iPhone 13:** Abra `[http://192.168.15.71:8000](http://192.168.15.71:8000)` e apoie o celular bem abaixo da webcam do Lenovo LOQ 15.
    
3. **Na sua máquina de áudio (Azure TTS):** Cole **uma pergunta por vez** abaixo e dê **Play** nos alto-falantes do notebook.
    
    - **O que você vai validar:** O sistema precisa ouvir a Sarah nos alto-falantes, travar seu microfone durante a fala dela (`Echo Gate`), esperar `1.75s` de silêncio e disparar os tópicos da resposta direto na tela do seu **iPhone 13**.
        

### Roteiro da Entrevistadora: Sarah Miller (Tech Recruiter — US Accessibility Role)

**Pergunta 1 — Quebra-gelo e Transição de Carreira (Fácil)**

> **Áudio para a Azure TTS:**
> 
> _"Hi Yago, thanks for joining today! I reviewed your resume and loved your background. Could you briefly walk me through your journey and how you transitioned from aviation safety compliance into web accessibility and software development?"_

- **Cola de Resposta Falada (para você ler olhando para a câmera):**
    
    - "Sure! I started in aviation safety compliance at LATAM Airlines | auditing critical operational standards."
        
    - "That rigor led me into Systems Analysis | and scientific research on digital accessibility at Senac."
        
    - "Today I combine front-end development | with WCAG 2.2 auditing using NVDA, Axe, and Lighthouse."
        

**Pergunta 2 — Auditoria Manual vs. Automatizada (Técnica Core)**

> **Áudio para a Azure TTS:**
> 
> _"In this role, you will audit web applications against WCAG 2.1 and 2.2 standards. When you test a page with NVDA alongside automated tools like Axe or Lighthouse, what kind of issues do you catch manually that automated scanners usually miss?"_

- **Cola de Resposta Falada:**
    
    - "Automated tools catch around thirty percent of issues | like missing alt text or low color contrast."
        
    - "With NVDA, I catch real user blockers | such as keyboard focus traps and broken tab order."
        
    - "I also verify dynamic `aria-live` announcements | and whether screen readers read meaningful context."
        

**Pergunta 3 — Remediação de Código HTML/JS (Prática)**

> **Áudio para a Azure TTS:**
> 
> _"Imagine a client built a custom modal dialog using only div elements, so keyboard users cannot close it with the Escape key and screen readers do not announce it. How would you document this and recommend a clean fix?"_

- **Cola de Resposta Falada:**
    
    - "First, I document the WCAG failure criterion | with reproduction steps and NVDA output."
        
    - "For the fix, I recommend replacing generic divs | with the native HTML `<dialog>` element."
        
    - "If custom code is required, we add `role='dialog'`, `aria-modal='true'` | and JavaScript focus management."
        

**Pergunta 4 — Rigor e Resolução de Problemas (Método STAR)**

> **Áudio para a Azure TTS:**
> 
> _"Working with US engineering teams requires high precision. Can you share a concrete example where your debugging or compliance mindset prevented a major failure?"_

- **Cola de Resposta Falada:**
    
    - "In a recent automation project, an integration suite was failing | with over four hundred test errors."
        
    - "Instead of patching symptoms, I isolated dirty test states | and refactored the validation flow."
        
    - "That reduced failures by over ninety percent | bringing the exact audit discipline I learned at LATAM."
        

**Pergunta 5 — Fechamento e Horário US Eastern Time (Logística)**

> **Áudio para a Azure TTS:**
> 
> _"This is a full-time remote contractor position working during US Eastern Time business hours. How comfortable are you collaborating with US stakeholders in English, and do you have any questions for me?"_

- **Cola de Resposta Falada:**
    
    - "US Eastern Time aligns very well with my schedule in Brazil | so real-time collaboration is easy."
        
    - "I am very comfortable documenting issues in English | and syncing with developers to verify fixes."
        
    - "My question is: how big is the accessibility team | and which tech stack do your clients use most?"