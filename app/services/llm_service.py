import ollama
from app.core.config import OLLAMA_MODEL, OLLAMA_HOST

_client = ollama.Client(host=OLLAMA_HOST)
_NO_FAB = (
    "You are a government policy analysis assistant with NO internet access and NO real "
    "economic/demographic databases. Never invent statistics, GDP figures, population "
    "counts, or historical outcome data not given in the prompt. If a real number is "
    "needed and not provided, say it requires research from official sources."
)


def generate(prompt: str, system: str = "", temperature: float = 0.3) -> str:
    try:
        r = _client.chat(model=OLLAMA_MODEL, messages=(
            ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        ), options={"temperature": temperature}, stream=False)
        return r["message"]["content"].strip()
    except Exception as e:
        return f"[Local LLM unavailable — is `ollama serve` running with model '{OLLAMA_MODEL}' pulled? Error: {e}]"


def is_available() -> bool:
    try:
        _client.list()
        return True
    except Exception:
        return False


def generate_policy_recommendation(scenario_name: str, description: str, impact_summary: str, stakeholder_summary: str) -> str:
    prompt = (
        f"Policy scenario: {scenario_name}\nDescription: {description}\n\n"
        f"Simulated impact (user-supplied ranges, Monte Carlo):\n{impact_summary}\n\n"
        f"Stakeholder network:\n{stakeholder_summary}\n\n"
        "In 4-5 sentences: summarize the projected impact range and its main drivers based "
        "ONLY on the numbers above, identify which stakeholder appears most central/affected, "
        "and note one implementation risk worth investigating. Do not invent any statistic "
        "beyond what was provided."
    )
    return generate(prompt, system=_NO_FAB)


def compare_scenarios_narrative(scenario_summaries: str) -> str:
    prompt = (
        f"Compare these policy scenarios based only on their simulated outcomes:\n{scenario_summaries}\n\n"
        "In 3-4 sentences, state which scenario shows the strongest projected outcome and "
        "note the key tradeoff between them. Do not invent data beyond what's given."
    )
    return generate(prompt, system=_NO_FAB)
