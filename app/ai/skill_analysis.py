
import json
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"


def analyze_skill_gaps(
    current_skills: list[str],
    required_skills: list[str],
    target_career: str,
):
    if not target_career or not target_career.strip():
        raise ValueError("Target career cannot be empty")

    if not required_skills:
        raise ValueError("At least one required skill is needed")

    normalized_current = {
        skill.strip().casefold()
        for skill in current_skills
        if skill and skill.strip()
    }

    normalized_required = {
        skill.strip().casefold(): skill.strip()
        for skill in required_skills
        if skill and skill.strip()
    }

    if not normalized_required:
        raise ValueError("Required skills cannot be empty")

    matched_skills = [
        skill
        for key, skill in normalized_required.items()
        if key in normalized_current
    ]

    missing_skills = [
        skill
        for key, skill in normalized_required.items()
        if key not in normalized_current
    ]

    skill_coverage = round(
        len(matched_skills) / len(normalized_required) * 100,
        2,
    )

    profile = {
        "target_career": target_career.strip(),
        "current_skills": current_skills,
        "required_skills": list(normalized_required.values()),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "skill_coverage_percentage": skill_coverage,
    }

    prompt = f"""
You are the SkillForge career skill analysis assistant.

Analyze this learner profile:
{json.dumps(profile)}

Use only the supplied skills. Do not claim the learner has skills
that are not listed in current_skills.

Return only valid JSON in this structure:
{{
    "target_career": "{target_career.strip()}",
    "matched_skills": [],
    "missing_skills": [],
    "skill_coverage_percentage": 0,
    "improvement_plan": [
        {{
            "skill": "Skill to improve",
            "priority": "high",
            "action": "Specific practical learning activity"
        }}
    ],
    "summary": "Brief explanation of the learner's skill gaps"
}}

Use high, medium, or low for priority.
Keep matched skills, missing skills, and coverage consistent with the supplied profile.
Provide practical recommendations for missing skills.
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
        analysis = json.loads(content)

        if not isinstance(analysis, dict):
            raise ValueError("AI returned an invalid skill analysis")

        analysis["target_career"] = target_career.strip()
        analysis["matched_skills"] = matched_skills
        analysis["missing_skills"] = missing_skills
        analysis["skill_coverage_percentage"] = skill_coverage

        if not isinstance(analysis.get("improvement_plan"), list):
            raise ValueError("AI returned an invalid improvement plan")

        if not isinstance(analysis.get("summary"), str):
            raise ValueError("AI returned an invalid summary")

        return analysis

    except requests.RequestException as exc:
        raise RuntimeError(
            "Unable to connect to Ollama. Check that Ollama is running."
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Ollama returned invalid JSON for skill analysis."
        ) from exc