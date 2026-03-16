"""Main CLI entry point."""
import click
from circle_so.config import Config

pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option("--db", envvar="CIRCLE_SO_DB", default="./circle-so.db", help="Path to SQLite database")
@click.option("--rate-limit", envvar="CIRCLE_SO_RATE_LIMIT", default=5, type=int, help="API requests per second")
@click.pass_context
def main(ctx, db, rate_limit):
    """CLI toolkit for managing Circle.so communities at scale."""
    ctx.ensure_object(Config)
    ctx.obj = Config(db_path=db, rate_limit=rate_limit)


@main.group()
@pass_config
def spaces(config):
    """Manage spaces."""


@main.group()
@pass_config
def members(config):
    """Manage members."""


@main.group()
@pass_config
def moderators(config):
    """Manage moderators."""


@main.group()
@pass_config
def report(config):
    """Generate reports."""


# Register subcommands
from circle_so.commands.spaces import register as register_spaces
from circle_so.commands.members import register as register_members
from circle_so.commands.moderators import register as register_moderators
from circle_so.commands.report import register as register_report

register_spaces(spaces)
register_members(members)
register_moderators(moderators)
register_report(report)
