"""
Integration tests for all Flask routes using the Flask test client.
All agent classes and external services are mocked so no real API
calls are made. These tests verify HTTP contract: status codes,
content-type, and that the right agent is called with the right args.
"""



def _stream_body(response) -> str:
    """Read a streaming response into a string."""
    return response.get_data(as_text=True)


# ── Health endpoint ───────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_returns_200(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_returns_json(self, client):
        r = client.get("/api/health")
        assert r.content_type.startswith("application/json")

    def test_response_has_status_ok(self, client):
        data = client.get("/api/health").get_json()
        assert data["status"] == "ok"

    def test_response_has_providers_key(self, client):
        data = client.get("/api/health").get_json()
        assert "providers" in data
        assert "groq" in data["providers"]
        assert "gemini" in data["providers"]
        assert "openrouter" in data["providers"]
        assert "github_token" in data["providers"]


# ── Context endpoint ──────────────────────────────────────────────────

class TestContextRoute:
    def test_missing_issue_url_returns_error_stream(self, client):
        r = client.post("/api/context", json={})
        body = _stream_body(r)
        assert "issue_url" in body.lower() or "required" in body.lower()

    def test_empty_issue_url_returns_error_stream(self, client):
        r = client.post("/api/context", json={"issue_url": "  "})
        body = _stream_body(r)
        assert "required" in body.lower() or "issue_url" in body.lower()

    def test_valid_url_calls_agent(self, client, mocker):
        mock_run = mocker.patch(
            "app.routes.context.ContextAgent.run",
            return_value=iter(["Brief output"]),
        )
        r = client.post(
            "/api/context",
            json={"issue_url": "https://github.com/o/r/issues/1"},
        )
        assert r.status_code == 200
        mock_run.assert_called_once()

    def test_include_comments_passed_to_agent(self, client, mocker):
        mock_run = mocker.patch(
            "app.routes.context.ContextAgent.run",
            return_value=iter([""]),
        )
        client.post(
            "/api/context",
            json={
                "issue_url": "https://github.com/o/r/issues/1",
                "include_comments": False,
            },
        )
        _, kwargs = mock_run.call_args
        assert kwargs.get("include_comments") is False

    def test_response_is_plain_text(self, client, mocker):
        mocker.patch(
            "app.routes.context.ContextAgent.run",
            return_value=iter(["ok"]),
        )
        r = client.post(
            "/api/context",
            json={"issue_url": "https://github.com/o/r/issues/1"},
        )
        assert "text/plain" in r.content_type

    def test_no_body_returns_error(self, client):
        r = client.post("/api/context", data="not json", content_type="text/plain")
        body = _stream_body(r)
        assert "required" in body.lower()


# ── Boilerplate endpoint ──────────────────────────────────────────────

class TestBoilerplateRoute:
    def test_missing_description_returns_error(self, client):
        r = client.post("/api/boilerplate", json={})
        body = _stream_body(r)
        assert "description" in body.lower()

    def test_valid_description_calls_agent(self, client, mocker):
        mock_run = mocker.patch(
            "app.routes.boilerplate.BoilerplateAgent.run",
            return_value=iter(["code output"]),
        )
        client.post("/api/boilerplate", json={"description": "Flask route"})
        mock_run.assert_called_once()

    def test_style_ref_forwarded_to_agent(self, client, mocker):
        mock_run = mocker.patch(
            "app.routes.boilerplate.BoilerplateAgent.run",
            return_value=iter([""]),
        )
        client.post(
            "/api/boilerplate",
            json={"description": "class", "style_ref": "https://raw.example.com/f.py"},
        )
        _, kwargs = mock_run.call_args
        assert kwargs.get("style_ref") == "https://raw.example.com/f.py"

    def test_empty_style_ref_becomes_none(self, client, mocker):
        mock_run = mocker.patch(
            "app.routes.boilerplate.BoilerplateAgent.run",
            return_value=iter([""]),
        )
        client.post(
            "/api/boilerplate",
            json={"description": "class", "style_ref": ""},
        )
        _, kwargs = mock_run.call_args
        assert kwargs.get("style_ref") is None


# ── Docs endpoint ─────────────────────────────────────────────────────

class TestDocsRoute:
    def test_missing_question_returns_error(self, client):
        r = client.post("/api/docs", json={"library": "Flask"})
        body = _stream_body(r)
        assert "question" in body.lower()

    def test_missing_library_and_url_returns_error(self, client):
        r = client.post("/api/docs", json={"question": "How?"})
        body = _stream_body(r)
        assert "library" in body.lower() or "custom_url" in body.lower()

    def test_valid_request_calls_agent(self, client, mocker):
        mock_run = mocker.patch(
            "app.routes.docs.DocsAgent.run",
            return_value=iter(["answer"]),
        )
        client.post("/api/docs", json={"library": "Flask", "question": "How?"})
        mock_run.assert_called_once()

    def test_custom_url_forwarded(self, client, mocker):
        mock_run = mocker.patch(
            "app.routes.docs.DocsAgent.run",
            return_value=iter([""]),
        )
        client.post(
            "/api/docs",
            json={
                "question": "How?",
                "custom_url": "https://docs.example.com/",
            },
        )
        _, kwargs = mock_run.call_args
        assert kwargs.get("custom_url") == "https://docs.example.com/"


# ── PR Draft endpoint ─────────────────────────────────────────────────

class TestPRDraftRoute:
    def test_missing_diff_returns_error(self, client):
        r = client.post("/api/pr-draft", json={})
        body = _stream_body(r)
        assert "diff" in body.lower()

    def test_valid_diff_calls_agent(self, client, mocker):
        mock_run = mocker.patch(
            "app.routes.pr_draft.PRDraftAgent.run",
            return_value=iter(["PR description"]),
        )
        client.post("/api/pr-draft", json={"diff": "diff --git a/f b/f\n+line"})
        mock_run.assert_called_once()

    def test_issue_number_int_forwarded(self, client, mocker):
        mock_run = mocker.patch(
            "app.routes.pr_draft.PRDraftAgent.run",
            return_value=iter([""]),
        )
        client.post(
            "/api/pr-draft",
            json={"diff": "diff --git a/f b/f\n+x", "issue_number": 42},
        )
        _, kwargs = mock_run.call_args
        assert kwargs.get("issue_number") == 42

    def test_invalid_issue_number_becomes_none(self, client, mocker):
        mock_run = mocker.patch(
            "app.routes.pr_draft.PRDraftAgent.run",
            return_value=iter([""]),
        )
        client.post(
            "/api/pr-draft",
            json={"diff": "diff --git a/f b/f\n+x", "issue_number": "not-a-number"},
        )
        _, kwargs = mock_run.call_args
        assert kwargs.get("issue_number") is None

    def test_whitespace_only_diff_returns_error(self, client):
        r = client.post("/api/pr-draft", json={"diff": "   "})
        body = _stream_body(r)
        assert "diff" in body.lower() or "required" in body.lower()
