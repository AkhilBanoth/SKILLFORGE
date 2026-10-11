from unittest.mock import Mock

import pytest
import requests

from app.agents import project_agent


def test_ask_project_agent_success(monkeypatch):
    monkeypatch.setattr(
        project_agent,
        "read_project_sources",
        lambda question: "SkillForge uses FastAPI.",
    )

    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["payload"] = json
        captured["timeout"] = timeout

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "message": {
                "content": "SkillForge is built with FastAPI."
            }
        }
        return response

    monkeypatch.setattr(project_agent.requests, "post", fake_post)

    answer = project_agent.ask_project_agent("What is SkillForge?")

    assert answer == "SkillForge is built with FastAPI."
    assert captured["payload"]["model"] == project_agent.OLLAMA_MODEL
    assert captured["payload"]["stream"] is False
    assert captured["payload"]["messages"][0]["role"] == "system"
    assert "What is SkillForge?" in captured["payload"]["messages"][1]["content"]
    assert "SkillForge uses FastAPI." in captured["payload"]["messages"][1]["content"]


@pytest.mark.parametrize("question", ["", "   ", "\n\t"])
def test_ask_project_agent_rejects_empty_question(question):
    with pytest.raises(ValueError, match="Question cannot be empty"):
        project_agent.ask_project_agent(question)


def test_ask_project_agent_handles_connection_failure(monkeypatch):
    monkeypatch.setattr(
        project_agent,
        "read_project_sources",
        lambda question: "Test source",
    )

    def fake_post(*args, **kwargs):
        raise requests.ConnectionError("Ollama is unavailable")

    monkeypatch.setattr(project_agent.requests, "post", fake_post)

    with pytest.raises(RuntimeError, match="Could not connect to Ollama"):
        project_agent.ask_project_agent("What is SkillForge?")


def test_ask_project_agent_rejects_empty_response(monkeypatch):
    monkeypatch.setattr(
        project_agent,
        "read_project_sources",
        lambda question: "Test source",
    )

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"message": {"content": "   "}}

    monkeypatch.setattr(
        project_agent.requests,
        "post",
        lambda *args, **kwargs: response,
    )

    with pytest.raises(RuntimeError, match="empty response"):
        project_agent.ask_project_agent("What is SkillForge?")
