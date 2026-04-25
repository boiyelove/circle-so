"""Chat commands -- list, read, send DMs via headless API."""
import re
from html import unescape

import click
from circle_so.config import Config

pass_config = click.make_pass_decorator(Config, ensure=True)


def _strip_html(html):
    if not html:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(html))).strip()


def _get_headless(config, email):
    """Authenticate as user and return (headless_namespace, my_community_member_id)."""
    client = config.get_client()
    token = client.auth.create_auth_token(email=email)
    from circle.http import SyncTransport
    from circle.api.headless_chat_notif_members import HeadlessChatNotifMembersClient
    url = config.community_url or "https://app.circle.so"
    transport = SyncTransport(
        api_token=token.access_token, base_url=url.rstrip("/"),
        auth_scheme="Bearer", rate_limit=config.rate_limit,
    )
    return HeadlessChatNotifMembersClient(transport), token.community_member_id, transport


def register(group):
    @group.command("list")
    @click.option("--email", envvar="CIRCLE_USER_EMAIL", required=True, help="Your Circle email")
    @click.option("--pages", default=2, help="Number of pages to fetch")
    @pass_config
    def list_rooms(config, email, pages):
        """List DM conversations."""
        chat, my_id, transport = _get_headless(config, email)
        try:
            for pg in range(1, pages + 1):
                rooms = chat.list_chat_rooms(page=pg, per_page=20)
                for room in (rooms.records or []):
                    unread = room.unread_messages_count or 0
                    name = room.chat_room_name or "?"
                    others = room.other_participants_preview or []
                    other_email = others[0].email if others else ""
                    marker = f" [{unread} unread]" if unread > 0 else ""
                    click.echo(f"  {room.uuid}  {name} ({other_email}){marker}")
                if not rooms.has_next_page:
                    break
        finally:
            transport.close()

    @group.command("read")
    @click.argument("uuid")
    @click.option("--email", envvar="CIRCLE_USER_EMAIL", required=True, help="Your Circle email")
    @click.option("--count", default=10, help="Number of messages to show")
    @pass_config
    def read_messages(config, uuid, email, count):
        """Read messages in a DM conversation."""
        chat, my_id, transport = _get_headless(config, email)
        try:
            msgs = chat.list_chat_messages(uuid, next_per_page=count)
            for m in (msgs.records or []):
                sender = m.sender.name if m.sender else "?"
                sid = m.sender.community_member_id if m.sender else None
                body = _strip_html(m.body or "")
                tag = " (you)" if sid == my_id else ""
                click.echo(f"  [{m.created_at[:16]}] {sender}{tag}: {body[:300]}")
        finally:
            transport.close()

    @group.command("send")
    @click.argument("uuid")
    @click.argument("message")
    @click.option("--email", envvar="CIRCLE_USER_EMAIL", required=True, help="Your Circle email")
    @pass_config
    def send_message(config, uuid, message, email):
        """Send a message to a DM conversation."""
        chat, my_id, transport = _get_headless(config, email)
        try:
            chat.create_chat_message(uuid, body=message)
            click.echo(f"Sent to {uuid}")
        finally:
            transport.close()

    @group.command("unread")
    @click.option("--email", envvar="CIRCLE_USER_EMAIL", required=True, help="Your Circle email")
    @click.option("--pages", default=3, help="Number of pages to scan")
    @pass_config
    def unread(config, email, pages):
        """Show DMs with unread messages or awaiting your reply."""
        chat, my_id, transport = _get_headless(config, email)
        try:
            needs_reply = []
            for pg in range(1, pages + 1):
                rooms = chat.list_chat_rooms(page=pg, per_page=20)
                for room in (rooms.records or []):
                    if not room.uuid:
                        continue
                    others = room.other_participants_preview or []
                    name = others[0].name if others else "?"
                    other_email = others[0].email if others else ""

                    msgs = chat.list_chat_messages(room.uuid, next_per_page=4)
                    recs = msgs.records or []
                    if not recs:
                        continue
                    last = recs[-1]
                    last_sid = last.sender.community_member_id if last.sender else None
                    if last_sid != my_id:
                        body = _strip_html(last.body or "")
                        needs_reply.append((name, other_email, room.uuid, body[:150], last.created_at))

                if not rooms.has_next_page:
                    break

            if not needs_reply:
                click.echo("No unread DMs.")
            else:
                click.echo(f"{len(needs_reply)} DMs awaiting reply:\n")
                for name, em, uuid, body, dt in needs_reply:
                    click.echo(f"  {name} ({em})")
                    click.echo(f"    {uuid}")
                    click.echo(f"    [{dt[:16]}] {body}")
                    click.echo()
        finally:
            transport.close()
