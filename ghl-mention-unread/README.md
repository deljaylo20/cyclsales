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

Each run stops at 45 calls (GHL + KV), under the free plan's 50 per run. In a
very busy minute the leftover conversations roll to the next run instead of
the run failing.

The account is on the Workers Free plan, where going over a limit makes
requests fail rather than adding charges. Billing only starts if someone
upgrades the account to Workers Paid ($5/mo minimum).

Log lines (Workers → Logs) use the spec's wording:
`<conversationId>: Conversation marked unread.` /
`Conversation was already unread.` / the failure reason.

Touches nothing else: no tags, contacts, opportunities, appointments, and no
outbound messages.

## Deploy

Live on Cloudflare as `ghl-mention-unread` (cron every minute, no public URL).
The KV namespace and `GHL_TOKEN` secret are already set. To redeploy after a
code change:

```sh
cd ghl-mention-unread
npx wrangler deploy
```

To pause writes without stopping it, set `DRY_RUN = "true"` and redeploy.
Cron schedules need the account's workers.dev subdomain to exist
(`cyclsales.workers.dev`), even though this worker doesn't use it.

## Limits

- Up to 1 minute delay after the comment.
- If the worker is down for more than 15 minutes, mentions in that gap are missed.
- Editing an existing comment to add a mention isn't caught (no new message).
- If 30+ messages land in one conversation between runs, an older comment can
  scroll out of the window. Unlikely at one-minute polling.
