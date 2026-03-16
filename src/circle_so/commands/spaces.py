"""Space management commands."""
import click
from circle_so.config import Config

pass_config = click.make_pass_decorator(Config)


def register(group):
    group.add_command(list_spaces)
    group.add_command(search)
    group.add_command(rename)
    group.add_command(lock)


@click.command("list")
@click.option("--prefix", default="all", help="Filter by prefix: kcna, ckad, or all")
@click.option("--cache", is_flag=True, help="Use cached data instead of API")
@pass_config
def list_spaces(config, prefix, cache):
    """List all spaces."""
    from circle.pagination import paginate
    client = config.get_client()
    for s in paginate(client.admin.spaces.list_spaces, per_page=200):
        slug = s.slug or ""
        if prefix == "all" or slug.startswith(prefix.lower()):
            click.echo(f"{s.name:<16} id={s.id:<10} slug={slug}")
    client.close()


@click.command()
@click.argument("names", nargs=-1, required=True)
@pass_config
def search(config, names):
    """Search for spaces by name or slug."""
    from circle.pagination import paginate
    client = config.get_client()
    all_spaces = list(paginate(client.admin.spaces.list_spaces, per_page=200))
    for target in names:
        target_slug = target.lower().replace(" ", "-")
        click.echo(f"'{target}':")
        found = False
        for s in all_spaces:
            if (s.name and s.name.strip() == target) or (s.slug and s.slug.startswith(target_slug)):
                click.echo(f"  name='{s.name}' id={s.id} slug={s.slug} type={s.space_type}")
                found = True
        if not found:
            click.echo("  Not found")
    client.close()


@click.command()
@click.argument("space_id", type=int)
@click.option("--name", required=True, help="New space name")
@click.option("--slug", default=None, help="New slug (auto-generated if omitted)")
@pass_config
def rename(config, space_id, name, slug):
    """Rename a space."""
    client = config.get_client()
    kwargs = {"name": name}
    if slug:
        kwargs["slug"] = slug
    result = client.admin.spaces.update_space(space_id, **kwargs)
    click.echo(f"Renamed: {result.name} (slug={result.slug})")
    client.close()


@click.command()
@click.option("--prefix", default="all", help="Filter: kcna, ckad, or all")
@click.option("--unlock", is_flag=True, help="Unlock instead of lock")
@click.option("--dry-run", is_flag=True, help="Preview without changes")
@pass_config
def lock(config, prefix, unlock, dry_run):
    """Lock/unlock spaces: disable member posting and member-adding."""
    from circle.pagination import paginate
    client = config.get_client()
    action = "Unlocking" if unlock else "Locking"
    success = 0
    for s in paginate(client.admin.spaces.list_spaces, per_page=200):
        slug = s.slug or ""
        if prefix != "all" and not slug.startswith(prefix.lower()):
            continue
        if dry_run:
            click.echo(f"[DRY RUN] {action}: {s.name}")
            continue
        client.admin.spaces.update_space(s.id,
            is_post_disabled=not unlock,
            prevent_members_from_adding_others=not unlock)
        click.echo(f"{action}: {s.name}")
        success += 1
    click.echo(f"\nDone: {success} spaces")
    client.close()
