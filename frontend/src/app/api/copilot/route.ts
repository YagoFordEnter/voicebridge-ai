import { NextRequest, NextResponse } from "next/server";

const PROFILE_CONTEXT = `Yago Santos Silva — Systems Analysis student at Senac SP.
PICTA Accessibility Researcher: WCAG 2.1/2.2, NVDA, Axe, WAVE, Lighthouse audits.
2 years at LATAM Airlines in SGSO (Safety Management System compliance).
Technical Skills: Python, Flutter, Java, Next.js, Playwright, n8n automation, AI agents.
Caçador de Vagas: 64 job submissions with verifiable evidence.
CRM Campaign: 5,839+ contacts organized via Meta API and n8n 24/7.
English level: B1+ technical proficiency.`;

const SYSTEM_PROMPT = `You are VoiceBridge AI — a discreet, real-time interview co-pilot for Yago Santos Silva.
ROLE: You receive the interviewer's question. Output a concise spoken-English answer that Yago can read aloud while maintaining eye contact.
FORMAT:
1. First line: complete opening sentence ready to speak aloud.
2. 2-3 short bullet points (max 14 words each) in order: what happened -> what I did -> result/learning.
3. Separate thoughts with "|" as breathing pause markers.
4. No markdown bolding, no headers, no labels (no "Situation:", "Action:").
5. Only use facts from the profile:
${PROFILE_CONTEXT}`;

export async function POST(req: NextRequest) {
  try {
    const { question } = await req.json();

    if (!question || typeof question !== "string") {
      return NextResponse.json({ error: "Question is required" }, { status: 400 });
    }

    const apiKey = process.env.GROQ_API_KEY;
    if (!apiKey) {
      return NextResponse.json(
        { error: "GROQ_API_KEY is not configured in environment" },
        { status: 500 }
      );
    }

    const models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"];
    let lastError: unknown = null;

    for (const model of models) {
      try {
        const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${apiKey}`,
          },
          body: JSON.stringify({
            model,
            messages: [
              { role: "system", content: SYSTEM_PROMPT },
              { role: "user", content: question },
            ],
            max_tokens: 350,
            temperature: 0.2,
          }),
        });

        if (!response.ok) {
          const errText = await response.text();
          throw new Error(`Groq model ${model} HTTP ${response.status}: ${errText}`);
        }

        const data = await response.json();
        const content = data.choices?.[0]?.message?.content?.trim();

        if (content) {
          return NextResponse.json({ answer: content, model });
        }
      } catch (err) {
        lastError = err;
        continue;
      }
    }

    return NextResponse.json(
      { error: `All models failed: ${lastError instanceof Error ? lastError.message : String(lastError)}` },
      { status: 502 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal Server Error" },
      { status: 500 }
    );
  }
}
