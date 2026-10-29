"""Generate GoHighLevel workflow JSON for the MARWOC seller SMS system.

    python3 build.py

Reads accounts/*.json, writes dist/<account>/NN-<workflow>.json (one workflow
per file), dist/<account>/_bundle.json (all five in one array) and BUILD-SHEET.md.

The workflow JSON follows the GHL builder's internal save shape
(name/status/settings, triggers[], workflowData.templates[] with
id/order/name/type/attributes/next/parentKey). If your importer wants a
different shape, change emit_workflow() only; the workflow logic above it
stays the same.
"""

import json
import uuid
from pathlib import Path

import messages as c

HERE = Path(__file__).parent
NS = uuid.UUID("5f0e3c1e-8a7b-4c52-9a51-6d8b3f1c2a10")

TAG = {
    "start": "sms-drip-start",
    "consent": "sms-consent-verified",
    "active": "sms-drip-active",
    "blocked": "sms-blocked-gate",
    "complete": "sms-drip-complete-no-reply",
    "replied": "sms-replied",
    "interested": "sms-interested",
    "review": "sms-reply-needs-review",
    "not_interested": "sms-not-interested",
    "wrong_number": "sms-wrong-number",
    "dnc": "dnc-permanent",
    "dnc_synced": "dnc-synced-from-partner",
}
TRACK_TAG = "sms-track-{}"

SEND_WINDOW = {
    "enabled": True,
    "timezone": "contact",
    "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
    "startTime": "10:00",
    "endTime": "19:00",
}


# ---------- step helpers ----------

def act(type_, name, **attributes):
    return {"type": type_, "name": name, "attributes": attributes}


def branch(type_, name, branches, **attributes):
    return {"type": type_, "name": name, "attributes": attributes, "branches": branches}


def cond(field, operator, value=None):
    d = {"field": field, "operator": operator}
    if value is not None:
        d["value"] = value
    return d


def add_tags(*tags):
    return act("add_contact_tag", "Add tag: " + ", ".join(tags), tags=list(tags))


def remove_tags(*tags):
    return act("remove_contact_tag", "Remove tag: " + ", ".join(tags), tags=list(tags))


def wait_days(days, label):
    return act("wait", label, type="time",
               startAfter={"value": days, "unit": "days", "when": "after"},
               advancedWindow=SEND_WINDOW)


def wait_window(label="Wait for send window"):
    return act("wait", label, type="time",
               startAfter={"value": 0, "unit": "minutes", "when": "after"},
               advancedWindow=SEND_WINDOW)


def sms(name, body):
    return act("sms", name, body=body, attachments=[], fromNumber="default")


def dnd(channels, label):
    return act("dnd_contact", label, dnd=True, channels=channels)


def phrase_any(phrases, mode="contains"):
    op = "contains_phrase" if mode == "contains" else "exact_match"
    return {"operator": "or", "conditions": [cond("message.body", op, p) for p in phrases]}


# ---------- workflows ----------

def wf_drip(a):
    tracks = []
    for t in c.TRACKS:
        steps = [add_tags(TRACK_TAG.format(t))]
        prev_day = 0
        for i, ((day, label), body) in enumerate(zip(c.TOUCHES, c.MESSAGES[t])):
            if i == 0:
                steps.append(wait_window())
            else:
                steps.append(wait_days(day - prev_day, f"Wait {day - prev_day} days (to day {day})"))
            steps.append(sms(f"Touch {i + 1} / Day {day} - {label} ({t})", body))
            prev_day = day
        steps += [
            act("wait", "Wait 7 days for a late reply", type="time",
                startAfter={"value": 7, "unit": "days", "when": "after"}),
            remove_tags(TAG["active"]),
            add_tags(TAG["complete"]),
        ]
        tracks.append({"name": f"Track {t}", "percent": 20, "steps": steps})

    gate = [
        cond("contact.tags", "contains", TAG["consent"]),
        cond("contact.tags", "not_contains", TAG["dnc"]),
        cond("contact.dnd.sms", "is_false"),
        cond("contact.phone", "is_not_empty"),
        cond("contact.first_name", "is_not_empty"),
        cond("contact.address1", "is_not_empty"),
    ]
    return {
        "key": "01-seller-sms-drip",
        "name": "MARWOC | 01 Seller SMS Drip (7 wk, 8 touches)",
        "settings": {"timezone": "contact", "stopOnResponse": True, "allowMultiple": False,
                     "removeContactFromLastStep": True, "autoMarkAsRead": False},
        "triggers": [{
            "type": "contact_tag", "name": f"Tag added: {TAG['start']}", "active": True,
            "conditions": [cond("tagsAdded", "index-of-true", TAG["start"])],
        }],
        "steps": [
            branch("if_else", "Gate: consent + clean data", [
                {"name": "Clear to send", "condition": {"operator": "and", "conditions": gate}, "steps": [
                    act("drip", f"Throttle: {a['drip_batch_size']} every {a['drip_interval_minutes']} min",
                        batchSize=a["drip_batch_size"],
                        interval={"value": a["drip_interval_minutes"], "unit": "minutes"}),
                    remove_tags(TAG["start"]),
                    add_tags(TAG["active"]),
                    branch("randomizer", "Split into 5 voice tracks", tracks),
                ]},
                {"name": "None (blocked)", "condition": None, "steps": [
                    remove_tags(TAG["start"]),
                    add_tags(TAG["blocked"]),
                ]},
            ]),
        ],
    }


def wf_reply(a):
    in_sequence = {"operator": "or", "conditions": [
        cond("contact.tags", "contains", TAG["active"]),
        cond("contact.tags", "contains", TAG["complete"]),
    ]}
    route_to_setter = lambda stage_id, stage_label, hot: [
        act("assign_user", "Round robin to setters", userIds=a["setter_user_ids"],
            trafficSplit="equally", onlyUnassignedContact=True),
        act("create_opportunity", f"Create/update opportunity: {stage_label}",
            pipelineId=a["pipeline_id"], pipelineStageId=stage_id,
            opportunityName="{{contact.first_name}} {{contact.last_name}} - {{contact.address1}}",
            status="open", allowBackward=False, allowDuplicate=False),
        act("internal_notification", "Text the assigned setter", type="sms", to="assigned_user",
            body=("{}SMS reply from {{{{contact.first_name}}}} ({{{{contact.address1}}}}): "
                  "\"{{{{message.body}}}}\" Reply fast.").format("HOT - " if hot else "")),
        act("internal_notification", "Email the assigned setter", type="email", to="assigned_user",
            subject=("HOT " if hot else "") + "SMS reply: {{contact.first_name}} - {{contact.address1}}",
            body="{{contact.first_name}} replied: \"{{message.body}}\"<br>Phone: {{contact.phone}}<br>Open the conversation in the inbox and respond."),
        act("add_task", "Task for setter", assignTo="assigned_user",
            title=("Call now: " if hot else "Review reply: ") + "{{contact.first_name}} - {{contact.address1}}",
            description="Replied to seller SMS: \"{{message.body}}\"",
            dueIn={"value": 1 if hot else 4, "unit": "hours"}),
    ]
    return {
        "key": "02-sms-reply-router",
        "name": "MARWOC | 02 SMS Reply Router (round robin)",
        "settings": {"timezone": "contact", "stopOnResponse": False, "allowMultiple": True,
                     "removeContactFromLastStep": True, "autoMarkAsRead": False},
        "triggers": [{
            "type": "customer_reply", "name": "Customer replied (SMS)", "active": True,
            "conditions": [cond("message.type", "==", "SMS")],
        }],
        "steps": [
            branch("if_else", "Came from the drip?", [
                {"name": "Yes", "condition": in_sequence, "steps": [
                    remove_tags(TAG["active"]),
                    add_tags(TAG["replied"]),
                    branch("if_else", "Classify reply", [
                        {"name": "Opt-out language (handled by 03)",
                         "condition": {"operator": "or", "conditions":
                                       phrase_any(c.OPT_OUT_EXACT, "exact")["conditions"]
                                       + phrase_any(c.OPT_OUT_PHRASES)["conditions"]},
                         "steps": []},
                        {"name": "Wrong number", "condition": phrase_any(c.WRONG_NUMBER_PHRASES), "steps": [
                            add_tags(TAG["wrong_number"]),
                            dnd(["sms"], "DND: SMS"),
                            act("add_note", "Note: wrong number",
                                body="Wrong number per SMS reply: \"{{message.body}}\". SMS suppressed."),
                        ]},
                        {"name": "Not interested", "condition": phrase_any(c.HARD_NO_PHRASES), "steps": [
                            add_tags(TAG["not_interested"]),
                            dnd(["sms"], "DND: SMS"),
                            act("add_note", "Note: not interested",
                                body="Not interested per SMS reply: \"{{message.body}}\". SMS suppressed."),
                        ]},
                        {"name": "Interested", "condition": phrase_any(c.POSITIVE_PHRASES),
                         "steps": [add_tags(TAG["interested"])]
                         + route_to_setter(a["stage_interested_id"], "Replied - Interested", True)},
                        {"name": "None (needs a human)", "condition": None,
                         "steps": [add_tags(TAG["review"])]
                         + route_to_setter(a["stage_review_id"], "Replied - Needs Review", False)},
                    ]),
                ]},
                {"name": "None (not an outreach lead)", "condition": None, "steps": []},
            ]),
        ],
    }


def wf_optout(a):
    trig_conditions = (phrase_any(c.OPT_OUT_EXACT, "exact")["conditions"]
                       + phrase_any(c.OPT_OUT_PHRASES)["conditions"])
    return {
        "key": "03-opt-out-suppression",
        "name": "MARWOC | 03 Opt-Out + Permanent Suppression",
        "settings": {"timezone": "contact", "stopOnResponse": False, "allowMultiple": True,
                     "removeContactFromLastStep": True, "autoMarkAsRead": False},
        "triggers": [{
            "type": "customer_reply", "name": "Customer replied with opt-out language", "active": True,
            "conditions": [cond("message.type", "==", "SMS"),
                           {"operator": "or", "conditions": trig_conditions}],
        }],
        "steps": [
            dnd(["all"], "DND: all channels"),
            add_tags(TAG["dnc"]),
            remove_tags(TAG["active"], TAG["start"]),
            act("add_note", "Audit note: opt-out",
                body="Opted out by SMS reply: \"{{message.body}}\". DND all channels + dnc-permanent applied automatically."),
            act("create_opportunity", "Move opportunity to Suppressed (if one exists)",
                pipelineId=a["pipeline_id"], pipelineStageId=a["stage_suppressed_id"],
                status="lost", allowBackward=True, allowDuplicate=False, onlyUpdateExisting=True),
            act("webhook", f"Sync DNC to {a['partner_label']}", method="POST",
                url=a["partner_dnc_webhook_url"], headers=[],
                customData=[
                    {"key": "phone", "value": "{{contact.phone}}"},
                    {"key": "email", "value": "{{contact.email}}"},
                    {"key": "first_name", "value": "{{contact.first_name}}"},
                    {"key": "last_name", "value": "{{contact.last_name}}"},
                    {"key": "reason", "value": "sms_opt_out"},
                    {"key": "source_account", "value": a["account_label"]},
                ]),
            act("remove_from_all_workflows", "Remove from all other workflows", excludeCurrent=True),
        ],
    }


def wf_help(a):
    return {
        "key": "04-help-keyword",
        "name": "MARWOC | 04 HELP Keyword Auto-Reply",
        "settings": {"timezone": "contact", "stopOnResponse": False, "allowMultiple": True,
                     "removeContactFromLastStep": True, "autoMarkAsRead": False},
        "triggers": [{
            "type": "customer_reply", "name": "Customer replied HELP / INFO", "active": True,
            "conditions": [cond("message.type", "==", "SMS"), phrase_any(c.HELP_EXACT, "exact")],
        }],
        "steps": [sms("HELP auto-reply (business identity)", c.HELP_REPLY)],
    }


def wf_dnc_receiver(a):
    return {
        "key": "05-partner-dnc-receiver",
        "name": f"MARWOC | 05 DNC Sync Receiver (from {a['partner_label']})",
        "settings": {"timezone": "account", "stopOnResponse": False, "allowMultiple": True,
                     "removeContactFromLastStep": True, "autoMarkAsRead": False},
        "triggers": [{
            "type": "inbound_webhook", "name": f"Inbound webhook from {a['partner_label']}", "active": True,
            "conditions": [],
        }],
        "steps": [
            act("create_update_contact", "Find or create contact by phone", matchBy="phone",
                fields={"phone": "{{inboundWebhookRequest.phone}}",
                        "email": "{{inboundWebhookRequest.email}}",
                        "first_name": "{{inboundWebhookRequest.first_name}}",
                        "last_name": "{{inboundWebhookRequest.last_name}}"}),
            dnd(["all"], "DND: all channels"),
            add_tags(TAG["dnc"], TAG["dnc_synced"]),
            act("add_note", "Audit note: partner opt-out",
                body="Opted out in {{inboundWebhookRequest.source_account}} ({{inboundWebhookRequest.reason}}). Suppressed here automatically."),
            act("remove_from_all_workflows", "Remove from all other workflows", excludeCurrent=True),
        ],
    }


WORKFLOWS = [wf_drip, wf_reply, wf_optout, wf_help, wf_dnc_receiver]


# ---------- emit ----------

def emit_workflow(wf, account_key):
    templates = []
    counter = [0]

    def nid(path):
        return str(uuid.uuid5(NS, f"{account_key}/{wf['key']}/{path}"))

    def chain(steps, path, parent_key, parent_branch):
        prev = None
        for i, s in enumerate(steps):
            node_id = nid(f"{path}/{i}")
            node = {
                "id": node_id,
                "order": counter[0],
                "name": s["name"],
                "type": s["type"],
                "attributes": dict(s["attributes"]),
                "parentKey": prev["id"] if prev else parent_key,
                "next": None,
            }
            if i == 0 and parent_branch:
                node["parent"] = parent_branch
            counter[0] += 1
            if prev:
                prev["next"] = node_id
            templates.append(node)
            if "branches" in s:
                branch_ids = []
                node["attributes"]["branches"] = []
                for bi, br in enumerate(s["branches"]):
                    bid = nid(f"{path}/{i}/b{bi}")
                    branch_ids.append(bid)
                    meta = {"id": bid, "name": br["name"]}
                    if "condition" in br:
                        meta["isNoneBranch"] = br["condition"] is None
                        if br["condition"] is not None:
                            meta["segments"] = [br["condition"]]
                    if "percent" in br:
                        meta["percentage"] = br["percent"]
                    node["attributes"]["branches"].append(meta)
                    first_child = chain(br["steps"], f"{path}/{i}/b{bi}", node_id, bid)
                    meta["next"] = first_child
                node["next"] = branch_ids
                break  # branches never merge back; a branch step ends its chain
            prev = node
        return nid(f"{path}/0") if steps else None

    chain(wf["steps"], "root", None, None)
    return {
        "name": wf["name"],
        "status": "draft",
        "version": 1,
        **wf["settings"],
        "triggers": wf["triggers"],
        "workflowData": {"templates": templates},
    }


def sheet_lines(steps, depth=0):
    pad = "  " * depth
    out = []
    for s in steps:
        line = f"{pad}- **{s['name']}** `{s['type']}`"
        body = s["attributes"].get("body")
        if s["type"] == "sms":
            out.append(line)
            out.append(f"{pad}  > {body}")
            continue
        out.append(line)
        for br in s.get("branches", []):
            extra = f" ({br['percent']}%)" if "percent" in br else ""
            out.append(f"{pad}  - _Branch: {br['name']}{extra}_")
            out += sheet_lines(br["steps"], depth + 2)
    return out


def main():
    dist = HERE / "dist"
    unfilled = {}
    sheet_done = False
    sheet = ["# MARWOC Seller SMS - Build Sheet", "",
             "Generated by build.py. Same logic as the JSON, readable by a human. "
             "If the importer misses a step, build it from here.", ""]
    for acct_file in sorted((HERE / "accounts").glob("*.json")):
        a = json.loads(acct_file.read_text())
        key = acct_file.stem
        out_dir = dist / key
        out_dir.mkdir(parents=True, exist_ok=True)
        bundle = []
        for fn in WORKFLOWS:
            wf = fn(a)
            data = emit_workflow(wf, key)
            bundle.append(data)
            (out_dir / f"{wf['key']}.json").write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n")
            if not sheet_done:
                sheet += [f"## {wf['name']}", ""]
                for t in wf["triggers"]:
                    sheet.append(f"**Trigger:** {t['name']} (`{t['type']}`)")
                sheet.append(f"**Settings:** `{json.dumps(wf['settings'])}`")
                sheet.append("")
                sheet += sheet_lines(wf["steps"])
                sheet.append("")
        (out_dir / "_bundle.json").write_text(json.dumps(bundle, indent=2, ensure_ascii=True) + "\n")
        sheet_done = True
        unfilled[key] = sorted({v for v in json.dumps(a).split('"') if v.startswith("REPLACE_")})
    (HERE / "BUILD-SHEET.md").write_text("\n".join(sheet) + "\n")

    for key, vals in unfilled.items():
        if vals:
            print(f"[{key}] still has placeholders: {', '.join(vals)}")
    print("Wrote", ", ".join(str(p.relative_to(HERE)) for p in sorted(dist.rglob("*.json"))))


if __name__ == "__main__":
    main()
