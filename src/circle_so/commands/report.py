"""Report commands."""
import csv
import os
import click
from circle_so.config import Config

pass_config = click.make_pass_decorator(Config)


def register(group):
    group.add_command(counts)
    group.add_command(inactive)
    group.add_command(missing)
    group.add_command(export)


@click.command()
@click.option("--prefix", default="all", help="Filter: kcna, ckad, or all")
@click.option("--over", default=0, type=int, help="Only show PLGs with more than N members")
@pass_config
def counts(config, prefix, over):
    """Show member counts per PLG."""
    conn = config.get_db()
    where = f"WHERE plg LIKE '{prefix.upper()}%'" if prefix != "all" else ""
    rows = conn.execute(f"""
        SELECT m.plg, COUNT(*) as cnt, s.space_id, s.slug
        FROM members m LEFT JOIN spaces s ON m.plg = s.plg
        {where} GROUP BY m.plg ORDER BY m.plg
    """).fetchall()
    click.echo(f"{'PLG':<12} {'Count':<8} {'Space ID':<10} {'Slug'}")
    click.echo("-" * 45)
    total = 0
    for plg, cnt, sid, slug in rows:
        if cnt > over:
            click.echo(f"{plg:<12} {cnt:<8} {sid or 'MISSING':<10} {slug or 'MISSING'}")
        total += cnt
    click.echo(f"\nTotal: {total}")


@click.command()
@pass_config
def inactive(config):
    """List inactive members from last audit."""
    conn = config.get_db()
    try:
        rows = conn.execute("""
            SELECT space_name, COUNT(*) FROM move_audit WHERE status='inactive'
            GROUP BY space_name ORDER BY space_name
        """).fetchall()
        for name, cnt in rows:
            click.echo(f"{name}: {cnt} inactive")
    except Exception:
        click.echo("No audit data. Run: circle-so members audit")


@click.command()
@pass_config
def missing(config):
    """List members not in their assigned space."""
    conn = config.get_db()
    rows = conn.execute("""
        SELECT plg, COUNT(*) FROM members
        WHERE in_space = 0 AND space_id IS NOT NULL
        GROUP BY plg ORDER BY plg
    """).fetchall()
    if not rows:
        click.echo("No missing members.")
        return
    for plg, cnt in rows:
        click.echo(f"{plg}: {cnt} missing")


@click.command()
@click.argument("report_type", type=click.Choice(["inactive", "missing", "moves", "plg_changes"]))
@click.option("--output", "-o", default=None, help="Output path (default: data dir)")
@pass_config
def export(config, report_type, output):
    """Export report to CSV."""
    conn = config.get_db()
    queries = {
        "inactive": "SELECT space_name, email, access_type, created_at FROM move_audit WHERE status='inactive' ORDER BY space_name",
        "missing": "SELECT plg, first_name, email FROM members WHERE in_space=0 AND space_id IS NOT NULL ORDER BY plg",
        "moves": "SELECT from_plg, to_plg, COUNT(*) FROM moves WHERE status='done' GROUP BY from_plg, to_plg",
        "plg_changes": "SELECT name, email, from_plg, to_plg FROM moves WHERE status='done' ORDER BY to_plg",
    }
    query = queries[report_type]
    rows = conn.execute(query).fetchall()
    cols = [d[0] for d in conn.execute(query).description]
    out_path = output or os.path.join(config.data_dir, f"{report_type}.csv")
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)
    click.echo(f"Exported {len(rows)} rows to {out_path}")
