
import json
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"


def generate_learning_recommendations(
    skills: list[str],
    completed_courses: list[str] | None = None,
    target_career: str | None = None,
):
    if not skills:
        raise ValueError("At least one skill is required")

    payload = {
        "skills": skills,
        "completed_courses": completed_courses or [],
        "target_career": target_career or "General career development",
    }

    prompt = f"""
You are a learning recommendation assistant for SkillForge.

Analyze this learner profile:
{json.dumps(payload)}

Recommend exactly 5 practical learning recommendations.

Return only valid JSON with this structure:
{{
    "recommendations": [
        {{
            "topic": "Topic to learn",
            "reason": "Why this topic is useful",
            "priority": "high",
            "next_step": "A practical action"
        }}
    ]
}}

Priority must be high, medium, or low.
Do not invent completed courses or skills.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=120,
        )
        response.raise_for_status()

        result = response.json()
        content = result.get("response", "")
        data = json.loads(content)

        recommendations = data.get("recommendations")

        if not isinstance(recommendations, list) or len(recommendations) != 5:
            raise ValueError("AI returned an invalid recommendation list")

        for item in recommendations:
            if not isinstance(item, dict):
                raise ValueError("Invalid recommendation item")

            required_fields = {"topic", "reason", "priority", "next_step"}

            if not required_fields.issubset(item):
                raise ValueError("Recommendation is missing required fields")

            if item["priority"] not in {"high", "medium", "low"}:
                raise ValueError("Invalid recommendation priority")

        return recommendations

    except requests.RequestException as exc:
        raise RuntimeError(
            "Unable to connect to Ollama. Check that Ollama is running."
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Ollama returned invalid JSON for recommendations."
        ) from exc