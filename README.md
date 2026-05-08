# circle-so

CLI toolkit for managing Circle.so communities at scale.

Built on top of [circle-so-python-sdk](https://github.com/boiyelove/circle-so-python-sdk).

## Installation

```bash
pip install circle-so
```

## Quick Start

```bash
export CIRCLE_API_TOKEN="your_token"

# Spaces
circle-so spaces list --prefix kcna
circle-so spaces search "KCNA 048"
circle-so spaces lock --prefix kcna
circle-so spaces rename 1761784 --name "KCNA 072" --slug "kcna-072"

# Members
circle-so members import learners.csv
circle-so members audit --prefix kcna --cache
circle-so members add learners.csv --space "KCNA 048"
circle-so members fix-missing --dry-run
circle-so members move --from "KCNA 046" --to "KCNA 073" --max 100

# Moderators
circle-so moderators verify moderators.csv
circle-so moderators add moderators.csv

# Reports
circle-so report counts --prefix kcna
circle-so report inactive
circle-so report missing
circle-so report export moves
```

## Configuration

Set via environment variables or `.env` file:

```bash
CIRCLE_API_TOKEN=your_token
CIRCLE_COMMUNITY_URL=https://your-community.circle.so
CIRCLE_SO_DB=./circle-so.db
CIRCLE_SO_DATA_DIR=~/Documents/Andela-K8s
```

### Token Types

Different commands require different tokens:

| Commands | Token needed | Source |
|----------|-------------|--------|
| `spaces`, `members`, `moderators`, `report` | Admin API token | Circle Admin > Settings > API |
| `chat` (list, read, send, unread) | Headless Auth token | Circle Admin > Developers > Headless Auth |

The `chat` commands also require your Circle email via `--email` or `CIRCLE_USER_EMAIL`:

```bash
export CIRCLE_API_TOKEN="your_headless_token"
export CIRCLE_USER_EMAIL="you@example.com"

circle-so chat list
circle-so chat unread
circle-so chat read <uuid>
circle-so chat send <uuid> "Your message"
```

The headless token generates a short-lived Bearer access token for your account, giving access to your DMs, notifications, and posts as yourself.

## License

MIT
