"""Tests for `circle-so posts` commands."""
from types import SimpleNamespace
from click.testing import CliRunner
from circle_so.cli import main
from circle_so.config import Config


class FakePostsClient:
    def __init__(self):
        self.calls = []
        self._next_post_id = 1

    def create_post(self, **kwargs):
        self.calls.append(("create_post", kwargs))
        post = SimpleNamespace(id=self._next_post_id, name=kwargs.get("name"))
        return SimpleNamespace(post=post)

    def update_post(self, post_id, **kwargs):
        self.calls.append(("update_post", post_id, kwargs))
        return SimpleNamespace(id=post_id)

    def show_post(self, post_id):
        self.calls.append(("show_post", post_id))
        return SimpleNamespace(id=post_id, name="Updated Title")

    def create_comment(self, *, body, post_id, **kwargs):
        self.calls.append(("create_comment", body, post_id))
        return SimpleNamespace(id=99)

    def list_comments(self, *, post_id, per_page=100):
        self.calls.append(("list_comments", post_id))
        return SimpleNamespace(records=[
            SimpleNamespace(id=1, user=SimpleNamespace(name="Alice"), body=SimpleNamespace(body="Hi")),
        ])

    def delete_comment(self, *, comment_id):
        self.calls.append(("delete_comment", comment_id))
        return {"success": True}


class FakeClient:
    def __init__(self):
        self.posts_calls = FakePostsClient()
        self.admin = SimpleNamespace(posts=self.posts_calls)

    def close(self):
        pass


def _patch_client(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(Config, "get_client", lambda self: fake)
    return fake


class TestPostsHelp:
    def test_main_help_lists_posts(self):
        result = CliRunner().invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "posts" in result.output

    def test_posts_help(self):
        result = CliRunner().invoke(main, ["posts", "--help"])
        assert result.exit_code == 0
        for cmd in ("create", "update", "comment", "comments", "delete-comment"):
            assert cmd in result.output


class TestPostsCreate:
    def test_create_with_body_string(self, monkeypatch):
        fake = _patch_client(monkeypatch)
        result = CliRunner().invoke(main, ["posts", "create", "--space", "123", "--title", "Hello", "--body", "World"])
        assert result.exit_code == 0
        assert "Created" in result.output
        name, kwargs = fake.posts_calls.calls[0]
        assert name == "create_post"
        assert kwargs["space_id"] == 123
        assert kwargs["name"] == "Hello"
        assert kwargs["body"] == "World"

    def test_create_with_body_file(self, monkeypatch, tmp_path):
        fake = _patch_client(monkeypatch)
        body_file = tmp_path / "body.txt"
        body_file.write_text("From a file")
        result = CliRunner().invoke(main, ["posts", "create", "--space", "123", "--title", "Hello", "--body-file", str(body_file)])
        assert result.exit_code == 0
        _, kwargs = fake.posts_calls.calls[0]
        assert kwargs["body"] == "From a file"

    def test_create_rejects_both_body_and_body_file(self, tmp_path, monkeypatch):
        _patch_client(monkeypatch)
        body_file = tmp_path / "body.txt"
        body_file.write_text("x")
        result = CliRunner().invoke(main, ["posts", "create", "--space", "123", "--title", "Hello", "--body", "x", "--body-file", str(body_file)])
        assert result.exit_code != 0

    def test_create_requires_body(self, monkeypatch):
        _patch_client(monkeypatch)
        result = CliRunner().invoke(main, ["posts", "create", "--space", "123", "--title", "Hello"])
        assert result.exit_code != 0


class TestPostsUpdate:
    def test_update_title_only(self, monkeypatch):
        fake = _patch_client(monkeypatch)
        result = CliRunner().invoke(main, ["posts", "update", "42", "--title", "New Title"])
        assert result.exit_code == 0
        assert "Updated" in result.output
        _, post_id, kwargs = fake.posts_calls.calls[0]
        assert post_id == 42
        assert kwargs == {"name": "New Title"}

    def test_update_requires_something(self, monkeypatch):
        _patch_client(monkeypatch)
        result = CliRunner().invoke(main, ["posts", "update", "42"])
        assert result.exit_code != 0


class TestPostsComment:
    def test_comment(self, monkeypatch):
        fake = _patch_client(monkeypatch)
        result = CliRunner().invoke(main, ["posts", "comment", "42", "Nice post"])
        assert result.exit_code == 0
        assert "Commented" in result.output
        assert fake.posts_calls.calls[0] == ("create_comment", "Nice post", 42)

    def test_comments_list(self, monkeypatch):
        _patch_client(monkeypatch)
        result = CliRunner().invoke(main, ["posts", "comments", "42"])
        assert result.exit_code == 0
        assert "Alice" in result.output
        assert "Hi" in result.output

    def test_delete_comment(self, monkeypatch):
        fake = _patch_client(monkeypatch)
        result = CliRunner().invoke(main, ["posts", "delete-comment", "99"])
        assert result.exit_code == 0
        assert "Deleted" in result.output
        assert fake.posts_calls.calls[0] == ("delete_comment", 99)
