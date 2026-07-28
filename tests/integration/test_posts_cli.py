"""Integration tests for `circle-so posts` against the CKAD 030 test space.
Run with: pytest tests/integration/ -m integration
"""
import pytest
from click.testing import CliRunner
from circle_so.cli import main
from tests.integration.conftest import requires_circle

CKAD_030_SPACE_ID = "1761803"


@pytest.mark.integration
@requires_circle
class TestPostsCLISmoke:
    def test_create_update_comment_delete_round_trip(self):
        runner = CliRunner()

        created = runner.invoke(main, [
            "posts", "create", "--space", CKAD_030_SPACE_ID,
            "--title", "circle-so CLI integration test post",
            "--body", "original body",
        ])
        assert created.exit_code == 0, created.output
        # "Created: <name> (id=<id>)"
        post_id = created.output.strip().rsplit("id=", 1)[1].rstrip(")")

        try:
            updated = runner.invoke(main, [
                "posts", "update", post_id, "--title", "circle-so CLI integration test post (updated)",
            ])
            assert updated.exit_code == 0, updated.output
            assert "updated" in updated.output.lower()

            commented = runner.invoke(main, [
                "posts", "comment", post_id, "**Bold** line.\n\n- item one",
            ])
            assert commented.exit_code == 0, commented.output

            listed = runner.invoke(main, ["posts", "comments", post_id])
            assert listed.exit_code == 0, listed.output
            # confirm the comment-flatten path applied: no raw markdown/newlines survive
            assert "**" not in listed.output
            assert "•" in listed.output

            comment_id = listed.output.split("[", 1)[1].split("]", 1)[0]
            deleted = runner.invoke(main, ["posts", "delete-comment", comment_id])
            assert deleted.exit_code == 0, deleted.output
        finally:
            import os
            from circle import CircleClient
            client = CircleClient(
                api_token=os.environ["CIRCLE_API_TOKEN"],
                community_url=os.environ.get("CIRCLE_COMMUNITY_URL"),
            )
            client.admin.posts.delete_post(int(post_id))
            client.close()
