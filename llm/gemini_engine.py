"""LLM Engine — TinyLlama (low RAM) + template fallback."""
from loguru import logger

MODEL = "tinyllama"

FALLBACK_TEMPLATES = {
    "maintenance": (
        "{turbine_id} requires maintenance. "
        "Anomaly score: {anomaly_score:.3f}. "
        "RUL: {rul_hours:.0f}h. Priority: {priority}. "
        "Action: {action}. Crew: {assigned_crew}. "
        "Revenue impact: ${revenue_loss_usd:,.0f}."
    )
}


def call(prompt: str, temperature: float = 0.2,
         max_tokens: int = 200) -> str:
    """Call TinyLlama with short response limit."""
    try:
        import ollama
        r = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature" : temperature,
                "num_predict" : max_tokens,
                "num_ctx"     : 512,    # ← small context = less RAM
            },
        )
        return r["message"]["content"].strip()
    except Exception as e1:
        logger.warning(f"chat failed: {e1} — trying generate")
        try:
            import ollama
            r = ollama.generate(
                model=MODEL,
                prompt=prompt[:500],    # ← truncate prompt
                options={"temperature": temperature,
                         "num_predict": max_tokens,
                         "num_ctx": 512},
            )
            return r["response"].strip()
        except Exception as e2:
            logger.error(f"Ollama failed: {e2}")
            return ""   # Return empty — caller uses fallback


def call_structured(prompt: str, output_format: str = "json") -> str:
    return call(f"{prompt}\nRespond in {output_format} only.",
                temperature=0.0)


if __name__ == "__main__":
    r = call("What does a wind turbine gearbox do? One sentence.")
    print(f"Response: {r}")