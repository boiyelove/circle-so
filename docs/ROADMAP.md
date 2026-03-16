# Roadmap

## Phase 1: Core CLI (Current)
- [x] Project scaffolding
- [ ] CLI framework with click
- [ ] Config management (env vars, .env, flags)
- [ ] DB schema with versioned migrations
- [ ] `spaces` commands: list, search, rename, lock/unlock
- [ ] `members` commands: import, audit, add, fix-missing
- [ ] `moderators` commands: verify, add
- [ ] `report` commands: counts, inactive, missing, export

## Phase 2: Caching Layer
- [ ] `--cache` flag on read commands
- [ ] TTL-based cache in SQLite (default 1 hour)
- [ ] `--refresh` flag to force fresh fetch
- [ ] Cache invalidation on write operations
- [ ] Cache stats command (`circle-so cache stats`, `circle-so cache clear`)

## Phase 3: Member Movement
- [ ] `members move` with engagement detection (posts, comments)
- [ ] Move planning with local preview (zero API calls)
- [ ] Move execution with verification
- [ ] Rollback support for failed moves
- [ ] Move history and audit trail in DB

## Phase 4: Bulk Operations
- [ ] Batch member invitations with progress bar
- [ ] Batch space creation from CSV/template
- [ ] Batch moderator assignment (when Circle API supports per-space moderators)
- [ ] Rate limit awareness with ETA display

## Phase 5: Observability
- [ ] `--verbose` and `--debug` flags on all commands
- [ ] Structured JSON logging option
- [ ] Operation audit log in DB (who did what, when)
- [ ] Diff reports (before/after state comparison)

## Phase 6: Multi-Community
- [ ] Named profiles (`circle-so --profile staging`)
- [ ] Profile management (`circle-so profile add/list/switch`)
- [ ] Per-profile DB and cache isolation

## Phase 7: Advanced Reports
- [ ] Member engagement scoring per space
- [ ] Inactive member detection with configurable thresholds
- [ ] Space health dashboard (member count, activity, moderator coverage)
- [ ] CSV/JSON/Markdown export formats

## Phase 8: Plugin System
- [ ] Hook system for pre/post command execution
- [ ] Custom command registration
- [ ] Webhook receiver for real-time sync

## Non-Goals
- Replacing the Circle.so web UI for day-to-day operations
- Real-time chat or notification management
- Content creation or moderation workflows
