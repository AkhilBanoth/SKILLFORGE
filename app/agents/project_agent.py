
import requests

from app.agents.prompts import PROJECT_AGENT_SYSTEM_PROMPT
from app.agents.source_reader import read_project_sources


OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:latest"


def ask_project_agent(
    question: str,
    learner_context: dict | None = None,
) -> str:
    """
    Ask SkillForge AI using project source code and optional
    personalized learning data.
    """
    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    source_context = read_project_sources(question)

    
    enhanced_question = (
        f"USER QUESTION:\n{question}\n\n"
        f"LEARNER DATA (authoritative data from the database):\n"
        f"{learner_context if learner_context is not None else 'No learner data was requested.'}\n\n"
        f"PROJECT SOURCE CODE (reference only):\n{source_context}\n\n"
        "IMPORTANT RESPONSE RULES:\n"
        "1. Answer the USER QUESTION directly. Never say the question "
        "is unclear when it is understandable.\n"
        "2. If learner data is provided, analyze that data first.\n"
        "3. For learning-progress questions, summarize the recorded "
        "skill gaps, incomplete courses, and weak assessments.\n"
        "4. Recommend the next steps using only the provided data.\n"
        "5. If there are no recorded skill gaps, say so. Do not claim "
        "that the learner has mastered every skill.\n"
        "6. If data is empty or insufficient, clearly explain what "
        "is missing instead of inventing results.\n"
        "7. Use project source code only when the question requires it.\n"
        "8. Do not describe how to review the codebase unless asked.\n"
        "9. Give a concise, personalized answer in simple language."
    )


    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": PROJECT_AGENT_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": enhanced_question,
            },
        ],
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            "Could not connect to Ollama. Make sure Ollama is running "
            "and the llama3.2:latest model is available."
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Ollama returned an invalid response."
        ) from exc

    answer = data.get("message", {}).get("content", "").strip()

    if not answer:
        raise RuntimeError("The AI agent returned an empty response.")

    return answer
