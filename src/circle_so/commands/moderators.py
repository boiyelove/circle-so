"""Moderator management commands."""
import csv
import click
from circle_so.config import Config

pass_config = click.make_pass_decorator(Config)


def register(group):
    group.add_command(verify)
    group.add_command(add)


@click.command()
@click.argument("csv_path", type=click.Path(exists=True))
@pass_config
def verify(config, csv_path):
    """Verify moderators are in their spaces with moderator status."""
    from circle.exceptions import CircleAPIError
    conn = config.get_db()
    client = config.get_client()
    mods = _parse_moderators_csv(csv_path)
    click.echo(f"{'Name':<35} {'PLG':<12} {'In Space':<10} {'Moderator'}")
    click.echo("-" * 72)
    in_space = not_in = moderators = 0
    for m in mods:
        space = conn.execute("SELECT space_id FROM spaces WHERE plg=?", (m["plg"],)).fetchone()
        if not space:
            click.echo(f"{m['name']:<35} {m['plg']:<12} {'NO SPACE':<10} -")
            continue
        try:
            sm = client.admin.spaces.show_space_member(email=m["email"], space_id=space[0])
            is_mod = sm.moderator
            click.echo(f"{m['name']:<35} {m['plg']:<12} {'YES':<10} {'YES' if is_mod else 'NO'}")
            in_space += 1
            if is_mod:
                moderators += 1
        except CircleAPIError:
            click.echo(f"{m['name']:<35} {m['plg']:<12} {'NO':<10} -")
            not_in += 1
    click.echo(f"\n{in_space} in space, {not_in} missing, {moderators}/{in_space} moderators")
    client.close()


@click.command()
@click.argument("csv_path", type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True)
@pass_config
def add(config, csv_path, dry_run):
    """Add moderators to their spaces (membership only -- moderator role requires Circle UI)."""
    import os
    from circle.exceptions import CircleAPIError, NotFoundError
    conn = config.get_db()
    client = config.get_client()
    sg_id = int(os.environ.get("CIRCLE_SPACE_GROUP_ID", "0"))
    mods = _parse_moderators_csv(csv_path)
    click.echo(f"{len(mods)} moderators to process")
    added = already = failed = 0
    for m in mods:
        space = conn.execute("SELECT space_id FROM spaces WHERE plg=?", (m["plg"],)).fetchone()
        if not space:
            click.echo(f"SKIP: {m['name']} -> {m['plg']} (no space)")
            continue
        if dry_run:
            click.echo(f"[DRY RUN] {m['name']} -> {m['plg']}")
            continue
        try:
            client.admin.spaces.show_space_member(email=m["email"], space_id=space[0])
            already += 1
            continue
        except CircleAPIError:
            pass
        try:
            client.admin.spaces.add_space_member(email=m["email"], space_id=space[0])
            click.echo(f"Added: {m['name']} -> {m['plg']}")
            added += 1
        except NotFoundError:
            try:
                client.admin.community.create_community_member(
                    email=m["email"], name=m["name"], skip_invitation=True,
                    space_group_ids=[sg_id] if sg_id else [])
                client.admin.spaces.add_space_member(email=m["email"], space_id=space[0])
                click.echo(f"Invited+Added: {m['name']} -> {m['plg']}")
                added += 1
            except CircleAPIError as e:
                click.echo(f"FAILED: {m['name']}: {e}")
                failed += 1
        except CircleAPIError:
            already += 1
    click.echo(f"\nDone: {added} added, {already} already, {failed} failed")
    click.echo("NOTE: Moderator role must be assigned in Circle UI.")
    client.close()


def _parse_moderators_csv(csv_path):
    """Auto-detect CSV format for moderators."""
    mods = []
    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        first = next(reader)
        f.seek(0)
        if any("email" in c.lower() for c in first):
            for row in csv.DictReader(f):
                email = (row.get("email") or row.get("Email Address") or row.get("Email") or "").strip()
                name = f"{row.get('first_name', row.get('First Name', '')).strip()} {row.get('last_name', row.get('Last Name', '')).strip()}".strip()
                plg = (row.get("PLGs") or row.get("PLG") or "").strip()
                if email:
                    mods.append({"email": email, "name": name, "plg": plg})
        else:
            f.seek(0)
            for row in csv.reader(f):
                if len(row) >= 3:
                    mods.append({"email": row[0].strip(), "name": f"{row[1].strip()} {row[2].strip()}", "plg": row[-1].strip()})
    return mods
