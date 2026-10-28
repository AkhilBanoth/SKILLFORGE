import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:latest"


def generate_learning_guidance(
    learning_data: dict,
) -> str:
    prompt = f"""
You are the AI learning mentor for SkillForge.

Analyze the learner's actual learning data below.

Learning data:
{learning_data}

Your tasks:
1. Identify the learner's most important learning priorities.
2. Explain which skills or topics need improvement.
3. Recommend practical next steps based on the available data.
4. Consider course progress and assessment results.
5. Create a simple learning plan with three actionable steps.
6. Do not invent courses, skills, assessment results, or scores.
7. If data is missing, clearly mention that limitation.

Return clear, encouraging guidance using simple English.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )

    response.raise_for_status()

    result = response.json()

    return result.get(
        "response",
        "Unable to generate learning guidance.",
    ).strip()