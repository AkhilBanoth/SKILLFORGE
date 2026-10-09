
import json
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"


def generate_questions(
    topic: str,
    difficulty: str = "medium",
    number_of_questions: int = 5,
):
    if not topic or not topic.strip():
        raise ValueError("Topic cannot be empty")

    difficulty = difficulty.lower()

    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("Difficulty must be easy, medium, or hard")

    if not 1 <= number_of_questions <= 20:
        raise ValueError("Number of questions must be between 1 and 20")

    prompt = f"""
Create exactly {number_of_questions} distinct multiple-choice questions
about {topic.strip()} at {difficulty} difficulty.

Return one valid JSON object with a "questions" array containing exactly
{number_of_questions} question objects.

Each question object must follow this structure:
{{
  "question": "A clear question",
  "options": {{
    "A": "First complete answer choice",
    "B": "Second complete answer choice",
    "C": "Third complete answer choice",
    "D": "Fourth complete answer choice"
  }},
  "correct_answer": "A",
  "explanation": "Why the correct answer is right"
}}

Important rules:
- Generate exactly {number_of_questions} questions.
- Every question must be different.
- Every option must contain actual answer text, not just A, B, C, or D.
- All four options must be non-empty strings.
- correct_answer must be A, B, C, or D.
- The correct answer must match the corresponding option.
- Do not include Markdown or text outside the JSON.
"""

    for attempt in range(2):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.2},
                },
                timeout=120,
            )
            response.raise_for_status()

            content = response.json().get("response", "")
            data = json.loads(content)

            if isinstance(data, dict):
                questions = data.get("questions", [])
            elif isinstance(data, list):
                questions = data
            else:
                questions = []

            valid_questions = isinstance(questions, list)
            valid_questions = valid_questions and (
                len(questions) == number_of_questions
            )

            if valid_questions:
                for question in questions:
                    if not isinstance(question, dict):
                        valid_questions = False
                        break

                    options = question.get("options")

                    if not isinstance(options, dict):
                        valid_questions = False
                        break

                    if set(options.keys()) != {"A", "B", "C", "D"}:
                        valid_questions = False
                        break

                    if not all(
                        isinstance(options[key], str)
                        and options[key].strip()
                        and options[key].strip() not in {"A", "B", "C", "D"}
                        for key in ("A", "B", "C", "D")
                    ):
                        valid_questions = False
                        break

                    if not all(
                        isinstance(question.get(key), str)
                        and question[key].strip()
                        for key in ("question", "explanation")
                    ):
                        valid_questions = False
                        break

                    if question.get("correct_answer") not in {
                        "A", "B", "C", "D"
                    }:
                        valid_questions = False
                        break

            if valid_questions:
                return questions

            prompt = f"""
Your previous response did not satisfy the requirements.

Generate exactly {number_of_questions} distinct {difficulty} multiple-choice
questions about {topic.strip()}.

Return a JSON object with a "questions" array. Every question must have:
- "question": a non-empty string
- "options": an object with keys A, B, C, D and four complete answer texts
- "correct_answer": one of A, B, C, D
- "explanation": a non-empty string

Never use just the letters A, B, C, D as option values.
Generate exactly {number_of_questions} questions.
Return JSON only.
"""

        except requests.RequestException as exc:
            raise RuntimeError(
                "Unable to connect to Ollama. Check that Ollama is running."
            ) from exc
        except json.JSONDecodeError:
            if attempt == 1:
                raise RuntimeError(
                    "Ollama returned invalid JSON after two attempts."
                )

    raise RuntimeError(
        "Ollama could not generate the requested number of valid questions. "
        "Try fewer questions or a more specific topic."
    )