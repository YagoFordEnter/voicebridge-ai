import os
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

QUESTIONS = [
    ("WCAG 2.2 & NVDA", "When auditing a web app with NVDA alongside Axe or Lighthouse, what issues do you catch manually that automated tools miss?"),
    ("Python & CUDA", "How did you architect VoiceBridge AI to run real-time speech transcription on an RTX 2050 with 4GB VRAM without blocking the UI?"),
    ("LATAM SGSO Rigor", "How does your 2-year background in aviation safety compliance at LATAM Airlines translate into software QA and accessibility auditing?"),
]

def get_active_agents():
    agents = []
    if os.getenv("GROQ_API_KEY"):
        agents.append(("Groq (openai/gpt-oss-120b)", OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1"), "openai/gpt-oss-120b"))
    if os.getenv("DEEPSEEK_API_KEY"):
        agents.append(("DeepSeek (deepseek-chat)", OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")), "deepseek-chat"))
    if os.getenv("OLLAMA_BASE_URL"):
        agents.append(("Ollama Local", OpenAI(api_key="ollama", base_url=os.getenv("OLLAMA_BASE_URL")), os.getenv("OLLAMA_MODEL", "qwen2.5:7b")))
    return agents

def run_benchmark():
    profile = Path("config/profile_context.md").read_text(encoding="utf-8")[:6000] if Path("config/profile_context.md").exists() else ""
    agents = get_active_agents()
    lines = ["# VoiceBridge AI — Multi-Agent QA Benchmark Report\n", f"- **Active Providers Tested:** {len(agents)}\n\n"]

    for name, client, model in agents:
        lines.append(f"## Provider: {name}\n\n| Scenario | Latency (ms) | Status | Sample Output |\n| :--- | :---: | :---: | :--- |\n")
        for topic, q in QUESTIONS:
            t0 = time.perf_counter()
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": f"You are an interview co-pilot. Reply in 3 short spoken-English bullet points (max 14 words each) using '|' as pause markers. Context:\n{profile}"},
                        {"role": "user", "content": q},
                    ],
                    max_tokens=180,
                    temperature=0.3,
                )
                ms = int((time.perf_counter() - t0) * 1000)
                text = resp.choices[0].message.content.strip().replace("\n", " ")
                lines.append(f"| {topic} | {ms} ms | PASS | {text[:120]}... |\n")
            except Exception as exc:
                ms = int((time.perf_counter() - t0) * 1000)
                lines.append(f"| {topic} | {ms} ms | FAIL | {str(exc)[:100]} |\n")
        lines.append("\n")

    Path("tests/QA_REPORT.md").write_text("".join(lines), encoding="utf-8")
    print("QA_REPORT.md gerado com sucesso!")

if __name__ == "__main__":
    run_benchmark()
