# MARWOC Seller SMS: GHL Workflow Bundle

This is built to the client spec as written. There are six workflows, built for both SFI Investing and Clark Home Improvement (spec Part 1). They import as **draft**, so nothing sends until someone reads it and publishes it.

The JSON matches GHL's own workflow export format. It was checked against a real export, and every step and trigger type used here appears in it.

```
dist/sfi-investing.zip             6 workflows in a "MARWOC SMS" folder
dist/clark-home-improvement.zip    same set
dist/<account>/*.json              the same files unzipped
BUILD-SHEET.md                     every step and message in plain English
build.py / messages.py             generator + the client's messages
accounts/*.json                    per-account IDs (fill these in)
```

## The six workflows, mapped to the spec

| # | Workflow | What it does | Spec |
|---|----------|--------------|------|
| 01 | Seller SMS Drip | Trigger: tag `sms-drip-start`. Gate: `sms-consent-verified` present, not suppressed, SMS DND off. Throttle, then a random split across the client's 5 messages. 5 touches on days 0, 12, 24, 36, 48. Each recipient gets all 5 messages, in a different starting order per track, so at every touch the list is spread across all 5 wordings. Sends only 8am-9pm, contact's local time. Stop on response is on. | Parts 1, 2, 3, 5, 10 |
| 02 | Reply Router | Any SMS reply from someone in the drip. Stop / not interested: removed from the drip, nothing else. Yes / interested, or any other reply: round robin to setters, opportunity created or moved, tag, task and a notification to the assigned setter. | Part 5 |
| 03 | STOP Opt-Out | Reply STOP / STOPALL / UNSUBSCRIBE: DND all channels, tag `dnc-permanent`, removed from all workflows. Account-wide. | Parts 1, 4 |
| 04 | HELP | Reply HELP: auto-response with business identity. | Part 4 |
| 05 | Reply: Not Interested | Not interested, wrong number, etc.: tag `sms-not-interested` + SMS DND, permanently. | Parts 1, 5 |
| 06 | Reply: Yes / Interested | Yes, maybe, how much, etc.: tag `sms-interested`, which 02 uses to route. | Part 5 |

## Before you import (each sub-account)

1. **Confirm the locationId** and put it in `accounts/<account>.json`.
2. **Custom values:**
   - `sms_rep_name` (the rep, "[name]" in the messages)
   - `sms_business_name` and `sms_business_phone` (used by HELP)
3. **Pipeline** with stages *Replied - Interested* and *Replied*. Put the pipeline and stage IDs in the account file.
4. **Setter user IDs** for the round robin go in the account file.
5. Run `python3 build.py`, then import the zip.

## One manual add: shared DNC across both sub-accounts (spec Part 4)

Your export had no webhook steps, so this isn't in the import.

1. In each account, create a workflow with an **Inbound Webhook** trigger. Steps:
   - Create/Update Contact (match on phone)
   - DND all channels
   - Add tag `dnc-permanent`
2. In each account's **03 STOP Opt-Out**, add a **Webhook** action that POSTs phone and email to the other account's inbound webhook URL.

## How a lead gets in

Import the list, then add tag `sms-drip-start`. Only contacts with `sms-consent-verified` get through. That tag is the Part 10 green light: nobody applies it until the consent basis is settled.

Only import rows that have a first name and a property address. Messages go out exactly as written, so a blank field leaves a gap in the text.

## Not built (outside what a GHL workflow can do)

From the spec:

- A2P 10DLC registration
- number pool rotation and warmup
- true delivered-vs-filtered reporting
- auto-pause
- number health
- pre-send content scanner
- list scrubbing
- skip tracing
- per-state flags
- reporting dashboards (Part 7)
- the Part 8 stretch items

These are Part 9 questions for the build team.
