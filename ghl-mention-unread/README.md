# GHL mention → mark unread

When `WATCH_USER_ID` is @mentioned in an internal comment in the `LOCATION_ID`
sub-account, this marks that conversation unread so it lands back in their
Unread tab.

## Why a poller and not a GHL AI agent

GHL Workflows have no trigger for internal comments or @mentions, so an Agent
Studio agent "invoked by an automation" would never get invoked. An LLM also
adds nothing here: the check is an exact string match on
`<userId>O04SuA629fM8CQVYHk9P</userId>` in the comment body.

## How it works

Every minute (Cloudflare cron):

1. `GET /conversations/search?mentions=<user>` sorted by last message date.
2. For conversations with activity in the last 15 minutes, read the last 30
   messages and find `TYPE_INTERNAL_COMMENT` messages that contain the mention.
3. If `unreadCount` is 0 → `PUT /conversations/{id}` with `unreadCount: 1`.
   If it's already unread → log it, no change.

Each handled comment ID is stored in KV for 3 days so the same mention never
re-marks a conversation after the teammate reads it. A failed call isn't
stored, so the next run retries it. Only the last 15 minutes are scanned, so old
mentions are never back-filled.

## Cost

Fits the Cloudflare Workers free plan. A quiet minute is 1 GHL call and no KV
operations; KV is only written when a mention is handled (free limit is 1,000
writes/day). 1,440 cron runs/day vs. 100,000 requests/day free.

Log lines (Workers → Logs) use the spec's wording:
`<conversationId>: Conversation marked unread.` /
`Conversation was already unread.` / the failure reason.

Touches nothing else: no tags, contacts, opportunities, appointments, and no
outbound messages.

## Deploy

```sh
cd ghl-mention-unread
npx wrangler kv namespace create STATE        # paste the id into wrangler.toml
npx wrangler secret put GHL_TOKEN
npx wrangler secret put MANUAL_RUN_KEY
npx wrangler deploy                           # starts in DRY_RUN
```

Watch the logs for a few mentions, then set `DRY_RUN = "false"` and redeploy.

## Limits

- Up to 1 minute delay after the comment.
- If the worker is down for more than 15 minutes, mentions in that gap are missed.
- Editing an existing comment to add a mention isn't caught (no new message).
- If 30+ messages land in one conversation between runs, an older comment can
  scroll out of the window. Unlikely at one-minute polling.
