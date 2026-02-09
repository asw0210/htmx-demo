"""Tests for the HTMX demo application."""

import pytest
from fastapi.testclient import TestClient

from main import app, todos, counter_value, counter_lock, todos_lock, next_todo_id


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state before each test."""
    global counter_value, next_todo_id
    with counter_lock:
        import main
        main.counter_value = 0
    with todos_lock:
        import main
        main.todos[:] = [
            {"id": 1, "text": "Skim the HTMX docs", "done": False},
            {"id": 2, "text": "Wire a form with hx-post", "done": False},
            {"id": 3, "text": "Try hx-swap-oob", "done": True},
        ]
        main.next_todo_id = 4
    yield


class TestHomeAndNavigation:
    def test_home_page_loads(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "HTMX Teaching App" in response.text
        assert "hx-get" in response.text

    def test_about_page_loads(self, client):
        response = client.get("/page/about")
        assert response.status_code == 200
        assert "About This Demo" in response.text


class TestHelloEndpoint:
    def test_hello_default_name(self, client):
        response = client.get("/hello")
        assert response.status_code == 200
        assert "Programmer" in response.text

    def test_hello_custom_name(self, client):
        response = client.get("/hello?name=Alice")
        assert response.status_code == 200
        assert "Alice" in response.text


class TestCounter:
    def test_counter_increments(self, client):
        response1 = client.get("/counter")
        assert response1.status_code == 200
        assert "1" in response1.text

        response2 = client.get("/counter")
        assert response2.status_code == 200
        assert "2" in response2.text


class TestSearch:
    def test_search_empty_returns_first_five(self, client):
        response = client.get("/search")
        assert response.status_code == 200
        assert "Alpine JS" in response.text

    def test_search_with_query(self, client):
        response = client.get("/search?q=poll")
        assert response.status_code == 200
        assert "Polling" in response.text

    def test_search_no_matches(self, client):
        response = client.get("/search?q=xyznonexistent")
        assert response.status_code == 200


class TestFormValidation:
    def test_validate_valid_email_and_zip(self, client):
        response = client.post(
            "/form/validate",
            data={"email": "test@example.com", "zipcode": "12345"}
        )
        assert response.status_code == 200

    def test_validate_invalid_email(self, client):
        response = client.post(
            "/form/validate",
            data={"email": "invalid", "zipcode": "12345"}
        )
        assert response.status_code == 200

    def test_validate_invalid_zipcode(self, client):
        response = client.post(
            "/form/validate",
            data={"email": "test@example.com", "zipcode": "abc"}
        )
        assert response.status_code == 200


class TestPollingAndLazy:
    def test_poll_endpoint(self, client):
        response = client.get("/poll")
        assert response.status_code == 200

    def test_lazy_endpoint(self, client):
        response = client.get("/lazy")
        assert response.status_code == 200


class TestFragments:
    def test_fragment_default_tab(self, client):
        response = client.get("/fragment")
        assert response.status_code == 200
        assert "overview" in response.text.lower()

    def test_fragment_details_tab(self, client):
        response = client.get("/fragment?tab=details")
        assert response.status_code == 200
        assert "details" in response.text.lower()


class TestOOB:
    def test_oob_endpoint(self, client):
        response = client.get("/oob")
        assert response.status_code == 200
        assert "hx-swap-oob" in response.text


class TestTodos:
    def test_add_todo(self, client):
        response = client.post("/todos", data={"text": "New task"})
        assert response.status_code == 200
        assert "New task" in response.text

    def test_add_empty_todo(self, client):
        response = client.post("/todos", data={"text": ""})
        assert response.status_code == 200
        assert "Enter a task" in response.text

    def test_toggle_todo(self, client):
        response = client.put("/todos/1")
        assert response.status_code == 200

    def test_toggle_nonexistent_todo(self, client):
        response = client.put("/todos/999")
        assert response.status_code == 404

    def test_delete_todo(self, client):
        response = client.delete("/todos/1")
        assert response.status_code == 200
        assert "Skim the HTMX docs" not in response.text

    def test_delete_nonexistent_todo(self, client):
        response = client.delete("/todos/999")
        assert response.status_code == 404


class TestSelectAndSync:
    def test_select_demo(self, client):
        response = client.get("/select-demo")
        assert response.status_code == 200

    def test_sync_demo(self, client):
        response = client.get("/sync-demo?item=Alpha")
        assert response.status_code == 200
        assert "Alpha" in response.text


class TestParams:
    def test_params_demo(self, client):
        response = client.get("/params-demo?focus=test&debug=ignored")
        assert response.status_code == 200
        assert "test" in response.text


class TestPreserve:
    def test_preserve_endpoint(self, client):
        response = client.get("/preserve")
        assert response.status_code == 200


class TestRedirect:
    def test_redirect_demo(self, client):
        response = client.get("/redirect-demo", follow_redirects=False)
        assert response.status_code == 200
        assert response.headers.get("HX-Redirect") == "/page/about"


class TestDisabledDemo:
    def test_disabled_demo(self, client):
        response = client.get("/disabled-demo")
        assert response.status_code == 200


class TestPatch:
    def test_patch_demo(self, client):
        response = client.patch("/patch-demo")
        assert response.status_code == 200


class TestValidateRequired:
    def test_validate_required(self, client):
        response = client.post("/validate-required", data={"username": "testuser"})
        assert response.status_code == 200
        assert "testuser" in response.text


class TestEncodingDemo:
    def test_encoding_demo(self, client):
        response = client.post(
            "/encoding-demo",
            data={"title": "Test"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200


class TestSelectOOB:
    def test_select_oob(self, client):
        response = client.get("/select-oob")
        assert response.status_code == 200


class TestRequestHeaders:
    def test_request_headers(self, client):
        response = client.get(
            "/request-headers",
            headers={"HX-Request": "true", "HX-Target": "#target"}
        )
        assert response.status_code == 200
        assert "HX-Request" in response.text


class TestResponseHeaders:
    def test_response_headers_push(self, client):
        response = client.get("/response-headers/push")
        assert response.status_code == 200
        assert response.headers.get("HX-Push-Url") == "/?pushed=1"

    def test_response_headers_replace(self, client):
        response = client.get("/response-headers/replace")
        assert response.status_code == 200
        assert response.headers.get("HX-Replace-Url") == "/?replaced=1"

    def test_response_headers_location(self, client):
        response = client.get("/response-headers/location")
        assert response.status_code == 200
        assert "HX-Location" in response.headers

    def test_response_headers_refresh(self, client):
        response = client.get("/response-headers/refresh")
        assert response.status_code == 200
        assert response.headers.get("HX-Refresh") == "true"

    def test_response_headers_reswap(self, client):
        response = client.get("/response-headers/reswap")
        assert response.status_code == 200
        assert response.headers.get("HX-Reswap") == "beforeend"

    def test_response_headers_retarget(self, client):
        response = client.get("/response-headers/retarget")
        assert response.status_code == 200
        assert response.headers.get("HX-Retarget") == "#response-retarget"

    def test_response_headers_trigger(self, client):
        response = client.get("/response-headers/trigger")
        assert response.status_code == 200
        assert "HX-Trigger" in response.headers


class TestPreload:
    def test_preload_info(self, client):
        response = client.get("/preload-info")
        assert response.status_code == 200


class TestHeadSupport:
    def test_head_support(self, client):
        response = client.get("/head-support")
        assert response.status_code == 200


class TestStatusDemo:
    def test_status_demo_ok(self, client):
        response = client.get("/status-demo/ok")
        assert response.status_code == 200
        assert "OK 200" in response.text

    def test_status_demo_error(self, client):
        response = client.get("/status-demo/error")
        assert response.status_code == 422
        assert "Error 422" in response.text


class TestMorphDemo:
    def test_morph_demo_toggles(self, client):
        response1 = client.get("/morph-demo")
        assert response1.status_code == 200

        response2 = client.get("/morph-demo")
        assert response2.status_code == 200


class TestAnimate:
    def test_animate_endpoint(self, client):
        response = client.get("/animate")
        assert response.status_code == 200
        assert "1" in response.text


class TestMultiSwap:
    def test_multi_swap(self, client):
        response = client.get("/multi-swap")
        assert response.status_code == 200


class TestItemDetail:
    def test_item_detail(self, client):
        response = client.get("/items/abc123")
        assert response.status_code == 200
        assert "abc123" in response.text


class TestJsonEnc:
    def test_json_encoding(self, client):
        response = client.post(
            "/json-enc",
            json={"key": "value"}
        )
        assert response.status_code == 200


class TestEventHeader:
    def test_event_header(self, client):
        response = client.post(
            "/event-header",
            headers={"Triggering-Event": "click"}
        )
        assert response.status_code == 200


class TestSlowEndpoint:
    def test_slow_endpoint(self, client):
        response = client.get("/slow")
        assert response.status_code == 200


class TestRequestInfo:
    def test_request_info(self, client):
        response = client.post(
            "/request-info",
            data={"note": "test note"},
            headers={"HX-Request": "true", "X-Demo": "htmx-demo"}
        )
        assert response.status_code == 200
        assert "htmx-demo" in response.text


class TestJinjaTemplates:
    def test_jinja_demo(self, client):
        response = client.get("/jinja-demo")
        assert response.status_code == 200
        assert "Context variables" in response.text

    def test_jinja_macros(self, client):
        response = client.get("/jinja-macros")
        assert response.status_code == 200

    def test_jinja_inheritance(self, client):
        response = client.get("/jinja-inheritance")
        assert response.status_code == 200
        assert "Inherited Fragment" in response.text
