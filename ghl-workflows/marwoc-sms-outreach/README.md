# MARWOC Seller SMS: GHL Workflow Bundle

There are five workflows, built for both SFI Investing and Clark Home Improvement. Everything imports as **draft**. Nothing sends until someone reads it and publishes it.

```
dist/sfi-investing/            01..05 *.json + _bundle.json (all five in one array)
dist/clark-home-improvement/   same set; the DNC webhook points at the other account
BUILD-SHEET.md                 every step and every message in plain English
build.py / messages.py         the generator and the copy (edit, then re-run)
accounts/*.json                per-account IDs (fill these in)
```

## The five workflows

| # | Name | Trigger | What it does |
|---|------|---------|--------------|
| 01 | Seller SMS Drip | Tag added `sms-drip-start` | Consent and data gate, then a throttle, then a random split into 5 voice tracks. Each track sends 8 touches on days 0, 3, 7, 14, 21, 30, 40 and 49, inside a Mon-Sat 10am-7pm send window (contact's timezone). Stop-on-response is on. If there's still no reply 7 days after the last touch, it tags `sms-drip-complete-no-reply`. |
| 02 | SMS Reply Router | Customer replied (SMS) | Runs only for contacts that came through the drip. Classifies the reply in this order: opt-out (left to 03), wrong number, not interested, interested, everything else. Wrong number and not interested get SMS DND plus a note. Interested and everything else get round-robin to setters, an opportunity created or updated, a text and an email to the setter, and a task (due in 1 hr if hot, 4 hrs if not). |
| 03 | Opt-Out + Permanent Suppression | Reply with STOP / "remove me" / "don't text" etc. | DND on all channels, tag `dnc-permanent`, an audit note, moves the opportunity to Suppressed, POSTs the contact to the other sub-account, and removes them from all workflows. |
| 04 | HELP Keyword | Reply HELP / INFO | Sends one SMS with business name, rep, phone and opt-out. |
| 05 | DNC Sync Receiver | Inbound webhook | Receives 03's POST from the other account. It finds or creates the contact by phone, then applies DND, `dnc-permanent` and a note. |

## Before you import (per sub-account)

1. **Confirm the locationId** you're importing into. Put it in `accounts/<account>.json` so the file records which account it's for.
2. **Custom values** (Settings → Custom Values): `sms_rep_name`, `sms_business_name`, `sms_business_phone`.
3. **Pipeline** with three stages: *Replied - Interested*, *Replied - Needs Review*, *Suppressed*. Put the pipeline ID and stage IDs in the account file.
4. **Setter user IDs** for the round robin go in the account file.
5. Import **05 first** in each account and copy its inbound webhook URL into the *other* account's file as `partner_dnc_webhook_url`.
6. Run `python3 build.py`. It lists any `REPLACE_` placeholders still left. Then import from `dist/`.

If you'd rather not run the script, import as-is and pick the pipeline, stages, users and webhook URL in the builder dropdowns after import. Each step that needs one is named so it's easy to spot.

## How a lead gets in

Add tag `sms-drip-start`. The gate only lets the contact through if **all** of these are true:

- tag `sms-consent-verified` is present
- no `dnc-permanent` tag
- SMS DND is off
- phone, first name and `address1` are all filled

Anyone who fails gets tagged `sms-blocked-gate` and nothing is sent. The gate also blocks texts like "Hey , about your place on ." when a field is blank.

**`sms-consent-verified` is the Part 10 switch.** Nobody should apply it until Austin/Eric (and counsel) have settled the consent basis for the list. Record the source and date of consent on the contact when you tag it, because that's the audit trail a registration review or a lawsuit asks for.

## What this covers from the spec, honestly

**Built here:** multi-step drip over 7 weeks, merge fields, 5-way message variation (5 × 8 = 40 messages, also usable as an A/B test by `sms-track-*` tag), per-timezone send window, throttle (Drip action), STOP and plain-language opt-out with permanent suppression, HELP auto-reply, cross-sub-account DNC sync, round robin on reply, pipeline, tags, setter notification and task, keyword routing, auto-pull from the drip on reply, and a non-responder tag for a call or mail fallback list.

**Not something a workflow can do** (this is LC Phone / carrier / account-level, or a different tool):

- A2P 10DLC registration
- number pool rotation and warmup
- true delivered-vs-filtered reporting
- auto-pause on a delivery-rate drop
- number health dashboard
- landline/DNC list scrubbing before import
- skip tracing
- RVM
- AI conversational booking (GHL Conversation AI could cover that, but it's a separate setup)

These go back to Part 9 as questions for the build team. They aren't covered here.

## Choices I made that you should check

- `{{contact.address1}}` stands in for `{{street}}`. If the property address lives in a custom field (common with absentee owners, where address1 is the mailing address), swap it in `messages.py`.
- The send window is **10am-7pm Mon-Sat**. That's narrower than the spec's 8am-9pm on purpose, because some states are stricter. Per-state exclusions are not built in. Counsel should confirm.
- The throttle is 20 contacts every 30 minutes as a starting point. It controls entry pace only. Size it to your warmed number count.
- "Not interested" and "wrong number" get **SMS DND** (permanent per spec Part 1). STOP-type replies get **DND on all channels**.
- Every message is plain GSM-7 text with no em dashes or curly quotes. One of those flips the message to UCS-2 (70 characters per segment) and roughly doubles cost. Openers and closers are 2 segments because they carry identity plus STOP. Most follow-ups are 1.
- The copy says "veteran-owned," "local," and "buy houses around here." Confirm all of that is true **for each account**. Clark Home Improvement especially may need different wording.

## Import format caveat

The JSON follows the GHL builder's internal save shape (`workflowData.templates[]` with `id/order/type/attributes/next/parentKey`, triggers separate). I wrote it without seeing a real export, because the workflow API is off on these sub-accounts. If your importer rejects it or drops steps, export one existing workflow with the tool that has an if/else, a wait, an SMS and a tag action. I'll remap `emit_workflow()` in `build.py` to match it exactly.
