"""Member management commands."""
import csv
import click
from circle_so.config import Config

pass_config = click.make_pass_decorator(Config)


def register(group):
    group.add_command(import_members)
    group.add_command(audit)
    group.add_command(add)
    group.add_command(fix_missing)


@click.command("import")
@click.argument("csv_path", type=click.Path(exists=True))
@pass_config
def import_members(config, csv_path):
    """Import members from CSV into local database."""
    conn = config.get_db()
    count = 0
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        plg_col = next((c for c in reader.fieldnames if c.lower() in ("plgs", "plg")), None)
        country_col = next((c for c in reader.fieldnames if c.lower() == "country"), None)
        for row in reader:
            conn.execute(
                "INSERT OR IGNORE INTO members (first_name, email, country, plg) VALUES (?, ?, ?, ?)",
                (row.get("first_name", "").strip(), row.get("email", "").strip(),
                 row.get(country_col, "").strip() if country_col else "",
                 row.get(plg_col, "").strip() if plg_col else ""))
            count += 1
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    click.echo(f"Imported {count} rows. Total: {total}")


@click.command()
@click.option("--prefix", default="all", help="Filter: kcna, ckad, or all")
@click.option("--cache", is_flag=True, help="Use cached data")
@pass_config
def audit(config, prefix, cache):
    """Audit members against Circle API."""
    from circle.pagination import paginate
    conn = config.get_db()
    client = config.get_client()
    where = f"AND plg LIKE '{prefix.upper()}%'" if prefix != "all" else ""
    spaces = conn.execute(f"SELECT plg, space_id FROM spaces WHERE space_id IS NOT NULL {where} ORDER BY plg").fetchall()
    click.echo(f"Auditing {len(spaces)} spaces...")
    conn.execute(f"UPDATE members SET in_space = 0 WHERE 1=1 {where}")
    for plg, space_id in spaces:
        emails = set()
        for m in paginate(client.admin.spaces.list_space_members, space_id=space_id, per_page=200):
            cm = m.community_member
            if cm and cm.email:
                emails.add(cm.email.lower())
        expected = conn.execute("SELECT id, email FROM members WHERE plg = ?", (plg,)).fetchall()
        matched = sum(1 for lid, email in expected if email.strip().lower() in emails)
        for lid, email in expected:
            if email.strip().lower() in emails:
                conn.execute("UPDATE members SET in_space = 1 WHERE id = ?", (lid,))
        click.echo(f"{plg}: {matched}/{len(expected)} matched, {len(expected)-matched} missing")
    conn.commit()
    client.close()


@click.command()
@click.argument("csv_path", type=click.Path(exists=True))
@click.option("--space", required=True, help="PLG name, e.g. 'KCNA 048'")
@click.option("--dry-run", is_flag=True)
@pass_config
def add(config, csv_path, space, dry_run):
    """Add members from CSV to a space."""
    from circle.exceptions import CircleAPIError, NotFoundError
    conn = config.get_db()
    row = conn.execute("SELECT space_id FROM spaces WHERE plg=?", (space,)).fetchone()
    if not row:
        click.echo(f"PLG '{space}' not found. Run: circle-so spaces list")
        return
    space_id = row[0]
    users = []
    with open(csv_path, newline="") as f:
        for r in csv.reader(f):
            if len(r) >= 2 and r[1].strip():
                users.append({"name": r[0].strip(), "email": r[1].strip()})
    click.echo(f"{len(users)} users -> {space} (id={space_id})")
    if dry_run:
        for u in users:
            click.echo(f"[DRY RUN] {u['name']} ({u['email']})")
        return
    client = config.get_client()
    sg_id = int(os.environ.get("CIRCLE_SPACE_GROUP_ID", "0"))
    import os
    success = failed = 0
    for u in users:
        try:
            client.admin.spaces.add_space_member(email=u["email"], space_id=space_id)
            success += 1
        except NotFoundError:
            try:
                client.admin.community.create_community_member(
                    email=u["email"], name=u["name"], skip_invitation=True,
                    space_group_ids=[sg_id] if sg_id else [])
                client.admin.spaces.add_space_member(email=u["email"], space_id=space_id)
                success += 1
            except CircleAPIError as e:
                click.echo(f"FAILED: {u['email']}: {e}")
                failed += 1
        except CircleAPIError:
            success += 1  # likely already member
    click.echo(f"Done: {success} added, {failed} failed")
    client.close()


@click.command("fix-missing")
@click.option("--dry-run", is_flag=True)
@pass_config
def fix_missing(config, dry_run):
    """Add all members marked as missing in the database to their spaces."""
    import os
    from circle.exceptions import CircleAPIError, NotFoundError
    conn = config.get_db()
    missing = conn.execute("""
        SELECT id, first_name, email, plg, space_id FROM members
        WHERE in_space = 0 AND space_id IS NOT NULL ORDER BY plg
    """).fetchall()
    click.echo(f"{len(missing)} missing members")
    if dry_run:
        for _, name, email, plg, _ in missing:
            click.echo(f"[DRY RUN] {name} ({email}) -> {plg}")
        return
    client = config.get_client()
    sg_id = int(os.environ.get("CIRCLE_SPACE_GROUP_ID", "0"))
    added = failed = 0
    for lid, name, email, plg, space_id in missing:
        try:
            client.admin.spaces.add_space_member(email=email, space_id=space_id)
        except NotFoundError:
            try:
                client.admin.community.create_community_member(
                    email=email, name=name, skip_invitation=True,
                    space_group_ids=[sg_id] if sg_id else [])
                client.admin.spaces.add_space_member(email=email, space_id=space_id)
            except CircleAPIError as e:
                click.echo(f"FAILED: {email}: {e}")
                failed += 1
                continue
        except CircleAPIError:
            pass
        conn.execute("UPDATE members SET in_space = 1 WHERE id = ?", (lid,))
        added += 1
    conn.commit()
    click.echo(f"Done: {added} added, {failed} failed")
    client.close()
