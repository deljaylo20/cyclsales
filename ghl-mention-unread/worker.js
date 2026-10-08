// Marks a GHL conversation unread when a watched user is @mentioned in an
// internal comment. Runs on a Cloudflare cron trigger (every minute).
//
// GHL has no workflow trigger for internal comments, so this polls instead:
//   1. Search conversations where WATCH_USER_ID is mentioned, newest first.
//   2. For any with activity since the last run, read recent messages and look
//      for TYPE_INTERNAL_COMMENT bodies containing <userId>WATCH_USER_ID</userId>.
//   3. If the conversation is read (unreadCount 0), set unreadCount to 1.
//
// It only ever calls GET search, GET messages, and PUT unreadCount. No tags,
// contacts, opportunities, or messages are touched.

const API = 'https://services.leadconnectorhq.com';
const OVERLAP_MS = 2 * 60 * 1000; // re-scan a little behind the watermark
const SEEN_TTL_S = 3 * 24 * 60 * 60; // per-comment dedupe, 3 days
const SEARCH_LIMIT = 50;
const MESSAGE_LIMIT = 30;

export default {
  async scheduled(_event, env, ctx) {
    ctx.waitUntil(run(env));
  },
  // GET /?key=MANUAL_RUN_KEY triggers one pass by hand, for testing.
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.searchParams.get('key') !== env.MANUAL_RUN_KEY || !env.MANUAL_RUN_KEY) {
      return new Response('Not found', { status: 404 });
    }
    const results = await run(env);
    return Response.json(results);
  },
};

export async function run(env, now = Date.now()) {
  const log = [];
  const stored = Number(await env.STATE.get('watermark'));
  // First run: start from now so we don't back-fill every old mention.
  const watermark = Number.isFinite(stored) && stored > 0 ? stored : now;
  const since = watermark - OVERLAP_MS;
  const marker = `<userId>${env.WATCH_USER_ID}</userId>`;
  let failed = false;

  let conversations;
  try {
    const q = new URLSearchParams({
      locationId: env.LOCATION_ID,
      mentions: env.WATCH_USER_ID,
      sortBy: 'last_message_date',
      sort: 'desc',
      limit: String(SEARCH_LIMIT),
    });
    const data = await ghl(env, `/conversations/search?${q}`);
    conversations = data.conversations || [];
  } catch (err) {
    log.push(`Search failed: ${err.message}`);
    console.log(log.join('\n'));
    return log;
  }

  const recent = conversations.filter((c) => Number(c.lastMessageDate) >= since);
  if (recent.length === SEARCH_LIMIT) {
    log.push(`Warning: ${SEARCH_LIMIT} conversations active since last run, some may be missed.`);
  }

  for (const convo of recent) {
    // Only act inside the configured sub-account.
    if (convo.locationId && convo.locationId !== env.LOCATION_ID) continue;

    let comments;
    try {
      const data = await ghl(env, `/conversations/${convo.id}/messages?limit=${MESSAGE_LIMIT}`);
      const messages = data.messages?.messages || data.messages || [];
      comments = messages.filter(
        (m) =>
          m.messageType === 'TYPE_INTERNAL_COMMENT' &&
          Date.parse(m.dateAdded) >= since &&
          (m.body || '').includes(marker),
      );
    } catch (err) {
      failed = true;
      log.push(`${convo.id}: could not read messages to check for the mention (${err.message}).`);
      continue;
    }

    const fresh = [];
    for (const c of comments) {
      if (!(await env.STATE.get(`seen:${c.id}`))) fresh.push(c);
    }
    if (fresh.length === 0) continue;

    let outcome;
    if (Number(convo.unreadCount) > 0) {
      outcome = 'Conversation was already unread.';
    } else if (env.DRY_RUN === 'true') {
      outcome = 'Dry run: would mark conversation unread.';
    } else {
      try {
        await ghl(env, `/conversations/${convo.id}`, {
          method: 'PUT',
          body: JSON.stringify({ unreadCount: 1 }),
        });
        outcome = 'Conversation marked unread.';
      } catch (err) {
        failed = true;
        log.push(`${convo.id}: mark unread failed (${err.message}).`);
        continue;
      }
    }

    log.push(`${convo.id}: ${outcome}`);
    if (env.DRY_RUN !== 'true') {
      for (const c of fresh) {
        await env.STATE.put(`seen:${c.id}`, '1', { expirationTtl: SEEN_TTL_S });
      }
    }
  }

  // Hold the watermark on failure so the next run retries; seen: keys stop
  // anything that already succeeded from being repeated.
  if (!failed && env.DRY_RUN !== 'true') await env.STATE.put('watermark', String(now));

  if (log.length) console.log(log.join('\n'));
  return log;
}

async function ghl(env, path, init = {}) {
  const res = await fetch(API + path, {
    ...init,
    headers: {
      Authorization: `Bearer ${env.GHL_TOKEN}`,
      Version: '2021-07-28',
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
  });
  if (!res.ok) {
    const text = (await res.text()).slice(0, 200);
    throw new Error(`HTTP ${res.status} ${text}`);
  }
  return res.json();
}
