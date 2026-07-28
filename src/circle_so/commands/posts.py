"""Post and comment management commands."""
import click
from circle_so.config import Config

pass_config = click.make_pass_decorator(Config)


def register(group):
    group.add_command(create)
    group.add_command(update)
    group.add_command(comment)
    group.add_command(comments)
    group.add_command(delete_comment)


@click.command()
@click.option("--space", "space_id", required=True, type=int, help="Space ID to post to")
@click.option("--title", required=True, help="Post title")
@click.option("--body-file", type=click.Path(exists=True), help="Plain-text file for the post body")
@click.option("--body", help="Post body as a plain-text string (alternative to --body-file)")
@click.option("--no-comments", is_flag=True, help="Disable comments on this post")
@click.option("--no-likes", is_flag=True, help="Disable likes on this post")
@pass_config
def create(config, space_id, title, body_file, body, no_comments, no_likes):
    """Create a post. Body is plain text, auto-converted to tiptap (paragraphs
    on blank lines, hard breaks on single newlines)."""
    text = _read_body(body_file, body)
    client = config.get_client()
    result = client.admin.posts.create_post(
        space_id=space_id, name=title, body=text,
        status="published",
        is_comments_enabled=not no_comments, is_liking_enabled=not no_likes,
    )
    click.echo(f"Created: {result.post.name} (id={result.post.id})")
    client.close()


@click.command()
@click.argument("post_id", type=int)
@click.option("--title", help="New title")
@click.option("--body-file", type=click.Path(exists=True), help="Plain-text file for the new body")
@click.option("--body", help="New body as a plain-text string (alternative to --body-file)")
@pass_config
def update(config, post_id, title, body_file, body):
    """Update a post's title and/or body in place."""
    kwargs = {}
    if title:
        kwargs["name"] = title
    text = _read_body(body_file, body, required=False)
    if text is not None:
        kwargs["body"] = text
    if not kwargs:
        raise click.UsageError("Provide --title and/or --body/--body-file")
    client = config.get_client()
    client.admin.posts.update_post(post_id, **kwargs)
    fetched = client.admin.posts.show_post(post_id)
    click.echo(f"Updated: {fetched.name} (id={post_id})")
    client.close()


@click.command()
@click.argument("post_id", type=int)
@click.argument("body")
@pass_config
def comment(config, post_id, body):
    """Add a comment to a post. Body is auto-flattened to a single plain-text
    line -- Circle's comment API has no rich-text support and strips all
    newlines with no replacement (see circle-so-python-sdk AGENTS.md)."""
    client = config.get_client()
    result = client.admin.posts.create_comment(body=body, post_id=post_id)
    click.echo(f"Commented: id={result.id}")
    client.close()


@click.command("comments")
@click.argument("post_id", type=int)
@pass_config
def comments(config, post_id):
    """List comments on a post."""
    client = config.get_client()
    result = client.admin.posts.list_comments(post_id=post_id, per_page=100)
    for c in result.records:
        author = c.user.name if c.user else "?"
        body = c.body.body if c.body else ""
        click.echo(f"[{c.id}] {author}: {body}")
    client.close()


@click.command("delete-comment")
@click.argument("comment_id", type=int)
@pass_config
def delete_comment(config, comment_id):
    """Delete a comment (no edit endpoint exists -- delete and re-add instead)."""
    client = config.get_client()
    client.admin.posts.delete_comment(comment_id=comment_id)
    click.echo(f"Deleted: comment {comment_id}")
    client.close()


def _read_body(body_file, body, required=True):
    if body_file and body:
        raise click.UsageError("Pass only one of --body-file or --body")
    if body_file:
        with open(body_file) as f:
            return f.read()
    if body:
        return body
    if required:
        raise click.UsageError("Provide --body-file or --body")
    return None
