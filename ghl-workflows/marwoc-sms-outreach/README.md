# MARWOC Seller SMS: GHL Workflow Bundle

There are six workflows, built for both SFI Investing and Clark Home Improvement. They import as **draft**. Nothing sends until someone reads it and publishes it.

The JSON matches GHL's own workflow export format. It was checked against a real export of 72 workflows, and every step and trigger type used here appears in that export.

```
dist/sfi-investing.zip             6 workflows in a "MARWOC SMS" folder
dist/clark-home-improvement.zip    same set
dist/<account>/*.json              the same files unzipped
BUILD-SHEET.md                     every step and all 40 messages in plain English
build.py / messages.py             generator + copy (edit, then re-run)
accounts/*.json                    per-account IDs (fill these in)
```

## The six workflows

| # | Name | Trigger | What it does |
|---|------|---------|--------------|
| 01 | Seller SMS Drip | Tag added `sms-drip-start` | Gate: must have `sms-consent-verified`, no `dnc-permanent` or `sms-not-interested` tag, and SMS DND off. Then a throttle (20 every 30 min), then a random split into 5 voice tracks. Each track sends 8 touches on days 0, 3, 7, 14, 21, 30, 40 and 49. The workflow time window is Mon-Sat 10am-7pm in the contact's timezone. Stop on response is on. If there's still no reply 7 days after the last touch, it tags `sms-drip-complete-no-reply`. |
| 02 | SMS Reply Router | Any SMS reply | Waits 1 min so 03/05/06 can tag first, then routes. Suppressed: just clears the outreach tags. Interested (hot) or any other reply from outreach: round robin to setters, opportunity in the matching stage, SMS + push to the setter, and a task. Contacts who aren't from outreach are ignored. |
| 03 | Opt-Out + Suppression | Reply contains stop / unsubscribe / remove me / don't text / etc. | DND on all channels, `dnc-permanent`, an audit note, removal from all workflows, and the opportunity moved to Suppressed (lost). Runs for every contact in the account, not only outreach leads. |
| 04 | HELP | Reply contains "help" | One SMS with business name, rep, phone and opt-out. |
| 05 | Tagger: Not Interested | Reply contains "not interested", "wrong number", etc. | Outreach leads only. Adds `sms-not-interested`, SMS DND, and a note with their words. |
| 06 | Tagger: Interested | Reply contains yes / maybe / how much / make an offer, etc. | Outreach leads only. Adds `sms-interested` so 02 routes it as hot. |

## Before you import (each sub-account)

1. **Confirm the locationId** and put it in `accounts/<account>.json`.
2. **Custom values** (Settings → Custom Values): `sms_rep_name`, `sms_business_name`, `sms_business_phone`.
3. **Pipeline** with stages *Replied - Interested*, *Replied - Needs Review*, *Suppressed*. Put the pipeline and stage IDs in the account file.
4. **Setter user IDs** for the round robin go in the account file.
5. Run `python3 build.py`. It prints any `REPLACE_` values still unfilled. Then import the zip.

If you'd rather not run the script, import as-is and pick the pipeline, stage and users in the builder after import. Only 02 and 03 have those fields.

## Two manual adds (about 5 min per account)

Your export had no webhook steps, so I left them out of the import rather than guess at the format.

1. **In 03 Opt-Out**, add a **Webhook** action right after the audit note.
   - Method POST, URL = the other account's inbound webhook (from step 2).
   - Body: `phone`, `email`, `first_name`, `last_name`, `reason=sms_opt_out`, `source_account=<this account>`.
2. **New workflow "07 DNC Sync Receiver"** in each account. Trigger: **Inbound Webhook**. Steps:
   - Create/Update Contact, matched on phone
   - DND all channels
   - Add tags `dnc-permanent` and `dnc-synced-from-partner`
   - Add note
   - Remove from all workflows

   Copy its webhook URL into the other account's step 1.

That's what makes an opt-out in one sub-account suppress the contact in the other one too.

## How a lead gets in

Import the list, then add tag `sms-drip-start`. Only `sms-consent-verified` contacts get through.

**`sms-consent-verified` is the Part 10 switch.** Nobody applies it until Austin/Eric (and counsel) have settled the consent basis. When you tag someone, record the consent source and date on the contact.

**List hygiene before import:**
- Only import rows that have a first name and a property address. The gate can't check for blank fields with any condition I could confirm from your export.
- Scrub landlines, invalid numbers and DNC first. Your existing Number Validation workflow may help here.

## What this covers from the spec

**Built:**
- 7-week multi-step drip with merge fields
- 5-way message variation (40 messages; `sms-track-A`..`E` tags let you compare tracks)
- quiet-hours window in the contact's timezone, and the throttle
- STOP and plain-language opt-out with permanent suppression, plus HELP
- round robin on reply, pipeline stage, setter notification and task
- keyword routing, auto-pull from the drip on reply
- non-responder tag for a call or mail fallback list

**Not something a workflow can do** (LC Phone / carrier / account-level, or a different tool):

- A2P 10DLC registration
- number pool rotation and warmup
- true delivered-vs-filtered reporting
- auto-pause on a delivery drop
- number health
- skip tracing
- RVM

AI qualification is possible. Your export shows Conversation AI and "matches intent" conditions in use, but that's a separate setup. These go back to Part 9.

## Choices to check

- `{{contact.address1}}` is used for {{street}}. If the property address is a custom field, swap it in `messages.py`.
- The time window is 10am-7pm Mon-Sat, narrower than the spec's 8am-9pm on purpose. Per-state rules aren't built in. Counsel should confirm.
- **Phrase matching is "contains."**
  - END, QUIT and CANCEL are left to GHL's built-in carrier keyword handling, because they hide inside normal words ("weekend").
  - "stop" will also catch "don't stop".
  - "help" will also catch "can you help me sell". That lead gets the HELP text, but 02 still routes them to a setter.
- No STOP confirmation text is sent. LC Phone handles carrier keywords natively, and a second confirmation would double up. If your other accounts send one on purpose, copy that step in.
- All 40 messages are plain GSM-7 text: no em dashes, no curly quotes. Openers and closers are 2 segments because they carry identity and STOP. Most follow-ups are 1.
- The copy says "veteran-owned," "local," and "buy houses around here." Confirm that's true **for each account**. Clark Home Improvement probably needs different wording.
