"""Generate GoHighLevel workflow JSON for the MARWOC seller SMS system.

    python3 build.py

Reads accounts/*.json and writes, per account:
  dist/<account>/NN-<workflow>.json   one workflow per file
  dist/<account>.zip                  same files in a "MARWOC SMS" folder
plus BUILD-SHEET.md (human-readable copy of every step and message).

The JSON matches GHL's own workflow export (workflowData.templates[] +
_triggers[]), copied field-for-field from a real export of 72 workflows.
Only step and trigger types that appear in that export are used here.
"""

import json
import uuid
import zipfile
from pathlib import Path

import messages as c

HERE = Path(__file__).parent
NS = uuid.UUID("5f0e3c1e-8a7b-4c52-9a51-6d8b3f1c2a10")
SMS_CHANNEL = 2  # message.type value GHL uses for SMS in customer_reply triggers

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
    "dnc": "dnc-permanent",
}
TRACK_TAG = "sms-track-{}"
IN_OUTREACH = [TAG["active"], TAG["complete"]]

# Workflow-level time window. days: 0 = Sunday ... 6 = Saturday.
DRIP_WINDOW = {"condition": "when", "start": "10:00", "end": "19:00", "days": [1, 2, 3, 4, 5, 6]}


# ---------- step definitions (abstract) ----------

def step(type_, name, attributes, **extra):
    return {"type": type_, "name": name, "attributes": attributes, **extra}


def add_tags(*tags):
    return step("add_contact_tag", "Add tag: " + ", ".join(tags), {"tags": list(tags)})


def remove_tags(*tags):
    return step("remove_contact_tag", "Remove tag: " + ", ".join(tags),
                {"tags": list(tags), "type": "remove_contact_tag"})


def sms(name, body):
    return step("sms", name, {"body": body, "attachments": []})


def wait(value, unit, name):
    return step("wait", name, {
        "type": "time",
        "startAfter": {"type": unit, "value": value, "when": "after"},
        "name": name, "cat": "", "isHybridAction": True, "hybridActionType": "wait",
        "convertToMultipath": False, "transitions": [],
    })


def dnd_all():
    return step("dnd_contact", "DND: all channels", {"type": "dnd_contact", "dnd_contact": "enable"})


def dnd_sms():
    return step("dnd_contact", "DND: SMS only",
                {"type": "dnd_contact", "dnd_contact": "enable_specific", "specific_channels": ["SMS"]})


def note(name, html):
    return step("add_notes", name, {"html": html, "type": "add_notes"})


def drip(batch, minutes):
    return step("drip", f"Throttle: {batch} every {minutes} min",
                {"batchSize": batch, "interval": {"timeUnit": "minutes", "value": minutes}, "type": "drip"})


def remove_from_all_workflows():
    return step("remove_from_workflow", "Remove from all other workflows",
                {"type": "remove_from_workflow", "allWorkflows": True, "includeCurrent": False})


def assign_round_robin(user_ids):
    return step("assign_user", "Round robin to setters", {
        "only_unassigned_contact": True,
        "total_index": len(user_ids),
        "traffic_split": "equally",
        "traffic_weightage": {u: 1 for u in user_ids},
        "traffic_index": [{"id": u, "indexes": [i + 1]} for i, u in enumerate(user_ids)],
        "user_list": list(user_ids),
        "type": "assign_user",
    })


def opportunity(name, pipeline_id, stage_id, status="open"):
    return step("create_opportunity", name, {
        "fields": [], "type": "create_opportunity",
        "pipeline_id": pipeline_id, "pipeline_stage_id": stage_id,
        "opportunity_name": "{{contact.first_name}} {{contact.last_name}} - {{contact.address1}}",
        "opportunity_status": status, "opportunity_source": "Seller SMS Outreach", "monetary_value": "",
    })


def notify_sms(body):
    return step("internal_notification", "Text the assigned setter",
                {"type": "sms", "sms": {"userType": "assign", "body": body, "attachments": []}})


def notify_push(title, body):
    return step("internal_notification", "Push notification to assigned setter", {
        "type": "notification",
        "notification": {"type": "send_notification", "redirectPage": "conversation",
                         "body": body, "title": title, "userType": "assign"},
    })


def task(title, body, due_days):
    return step("task-notification", "Task for setter", {
        "title": title, "body": body, "assignedTo": "contact.assigned_user",
        "dueDate": str(due_days), "type": "task_notification", "__customInputs__": {},
    }, workflowsActionType="INTERNAL")


def has_tags(tags):
    return {"conditionType": "contact_detail", "conditionSubType": "tags",
            "conditionOperator": "index-of-true", "conditionValue": list(tags),
            "__customFieldType__": "standard"}


def lacks_tags(tags):
    return {"conditionType": "contact_detail", "conditionSubType": "tags",
            "conditionOperator": "index-of-false", "conditionValue": list(tags),
            "__customFieldType__": "standard"}


def sms_dnd_off():
    return {"conditionType": "contact_detail", "conditionSubType": "dnd_channels",
            "conditionOperator": "index-of-false", "conditionValue": ["SMS"],
            "__customFieldType__": "standard"}


def in_pipeline(pipeline_id):
    return {"conditionType": "opportunities", "conditionSubType": "pipelineId",
            "conditionOperator": "==", "conditionValue": pipeline_id,
            "__customFieldType__": "standard"}


def if_else(name, branches, none_steps):
    """branches: [(branch name, [conditions ANDed], [steps])]."""
    return {"type": "if_else", "name": name, "branches": branches, "none": none_steps}


def split(name, paths):
    """paths: [(path name, percent, [steps])]."""
    return {"type": "workflow_split", "name": name, "paths": paths}


# ---------- triggers ----------

def tag_trigger(tag):
    return {"type": "contact_tag", "name": "Contact Tag", "conditions": [
        {"operator": "index-of-true", "field": "tagsAdded", "value": tag,
         "title": "Tag Added", "type": "select", "id": "tag-added"}]}


def reply_trigger(phrases=None):
    conds = [{"operator": "==", "field": "message.type", "value": SMS_CHANNEL,
              "title": "Reply channel", "type": "select"}]
    if phrases:
        conds.append({"operator": "string-contains-any-of", "field": "message.body", "value": list(phrases),
                      "title": "Contains phrase", "type": "string", "id": "message-contains-phrase"})
    return {"type": "customer_reply", "name": "Customer Replied", "conditions": conds}


# ---------- workflows ----------

def settings(window=None, timezone="account", stop_on_response=False, allow_multiple=True):
    return {"window": window, "timezone": timezone, "stopOnResponse": stop_on_response,
            "allowMultiple": allow_multiple}


def wf_drip(a):
    paths = []
    for t in c.TRACKS:
        steps = [add_tags(TRACK_TAG.format(t))]
        prev_day = 0
        for i, ((day, label), body) in enumerate(zip(c.TOUCHES, c.MESSAGES[t])):
            if i:
                steps.append(wait(day - prev_day, "days", f"Wait {day - prev_day} days (to day {day})"))
            steps.append(sms(f"Touch {i + 1} / Day {day} - {label} ({t})", body))
            prev_day = day
        steps += [wait(7, "days", "Wait 7 days for a late reply"),
                  remove_tags(TAG["active"]), add_tags(TAG["complete"])]
        paths.append((f"Track {t}", 20, steps))

    return {
        "key": "01-seller-sms-drip",
        "name": "MARWOC | 01 Seller SMS Drip (7 wk, 8 touches)",
        "settings": settings(window=DRIP_WINDOW, timezone="contact", stop_on_response=True, allow_multiple=False),
        "trigger": tag_trigger(TAG["start"]),
        "steps": [if_else("Gate: consent + not suppressed", [
            ("Clear to send",
             [has_tags([TAG["consent"]]),
              lacks_tags([TAG["dnc"], TAG["not_interested"]]),
              sms_dnd_off()],
             [drip(a["drip_batch_size"], a["drip_interval_minutes"]),
              remove_tags(TAG["start"]),
              add_tags(TAG["active"]),
              split("Split: 5 voice tracks", paths)]),
        ], [remove_tags(TAG["start"]), add_tags(TAG["blocked"])])],
    }


def wf_router(a):
    def to_setter(stage_id, stage_label, hot):
        prefix = "HOT - " if hot else ""
        return [
            remove_tags(*IN_OUTREACH),
            add_tags(TAG["replied"]),
            assign_round_robin(a["setter_user_ids"]),
            opportunity(f"Create/update opportunity: {stage_label}", a["pipeline_id"], stage_id),
            notify_sms(f"{prefix}SMS reply from {{{{contact.first_name}}}} about {{{{contact.address1}}}}. "
                       "Open the conversation and reply fast."),
            notify_push(f"{prefix}Seller replied: {{{{contact.first_name}}}}",
                        "{{contact.first_name}} replied to the seller SMS about {{contact.address1}}."),
            task(("Call now: " if hot else "Review reply: ") + "{{contact.first_name}} - {{contact.address1}}",
                 "Replied to seller SMS outreach. Read the conversation, then call or reply.", 1),
        ]

    return {
        "key": "02-sms-reply-router",
        "name": "MARWOC | 02 SMS Reply Router (round robin)",
        "settings": settings(),
        "trigger": reply_trigger(),
        "steps": [
            wait(1, "minutes", "Wait 1 min (let taggers 03/05/06 run first)"),
            if_else("Route the reply", [
                ("Suppressed (opt-out / not interested)",
                 [has_tags([TAG["dnc"], TAG["not_interested"]]), has_tags(IN_OUTREACH)],
                 [remove_tags(*IN_OUTREACH), add_tags(TAG["replied"])]),
                ("Interested",
                 [has_tags([TAG["interested"]]), has_tags(IN_OUTREACH)],
                 to_setter(a["stage_interested_id"], "Replied - Interested", True)),
                ("Other reply from outreach",
                 [has_tags(IN_OUTREACH)],
                 [add_tags(TAG["review"])] + to_setter(a["stage_review_id"], "Replied - Needs Review", False)),
            ], []),
        ],
    }


def wf_optout(a):
    return {
        "key": "03-opt-out-suppression",
        "name": "MARWOC | 03 Opt-Out + Permanent Suppression",
        "settings": settings(),
        "trigger": reply_trigger(c.OPT_OUT_PHRASES),
        "steps": [
            dnd_all(),
            add_tags(TAG["dnc"]),
            remove_tags(TAG["active"], TAG["start"]),
            note("Audit note: opt-out",
                 "Opted out by SMS reply: \"{{message.body}}\". DND all channels + dnc-permanent applied by workflow."),
            remove_from_all_workflows(),
            if_else("Has an outreach opportunity?", [
                ("Yes", [in_pipeline(a["pipeline_id"])],
                 [opportunity("Move opportunity to Suppressed (lost)", a["pipeline_id"],
                              a["stage_suppressed_id"], status="lost")]),
            ], []),
        ],
    }


def wf_help(a):
    return {
        "key": "04-help-keyword",
        "name": "MARWOC | 04 HELP Keyword Auto-Reply",
        "settings": settings(),
        "trigger": reply_trigger(c.HELP_PHRASES),
        "steps": [sms("HELP auto-reply (business identity)", c.HELP_REPLY)],
    }


def wf_not_interested(a):
    return {
        "key": "05-reply-tagger-not-interested",
        "name": "MARWOC | 05 Reply Tagger: Not Interested / Wrong Number",
        "settings": settings(),
        "trigger": reply_trigger(c.HARD_NO_PHRASES + c.WRONG_NUMBER_PHRASES),
        "steps": [if_else("From outreach?", [
            ("Yes", [has_tags(IN_OUTREACH + [TAG["replied"]])],
             [add_tags(TAG["not_interested"]),
              dnd_sms(),
              note("Note: not interested / wrong number",
                   "SMS suppressed. Seller replied: \"{{message.body}}\"")]),
        ], [])],
    }


def wf_interested(a):
    return {
        "key": "06-reply-tagger-interested",
        "name": "MARWOC | 06 Reply Tagger: Interested",
        "settings": settings(),
        "trigger": reply_trigger(c.POSITIVE_PHRASES),
        "steps": [if_else("From outreach and not suppressed?", [
            ("Yes", [has_tags(IN_OUTREACH + [TAG["replied"]]), lacks_tags([TAG["dnc"], TAG["not_interested"]])],
             [add_tags(TAG["interested"])]),
        ], [])],
    }


WORKFLOWS = [wf_drip, wf_router, wf_optout, wf_help, wf_not_interested, wf_interested]


# ---------- emit in GHL export format ----------

def emit_workflow(wf, a, account_key):
    def nid(path):
        return str(uuid.uuid5(NS, f"{account_key}/{wf['key']}/{path}"))

    templates = []

    def chain(steps, path, parent_key, parent, order):
        """Emit a linear list of steps. Returns the first node's id."""
        prev = None
        first = None
        for i, s in enumerate(steps):
            node_id = nid(f"{path}/{i}")
            first = first or node_id
            node = {"id": node_id, "order": order + i, "name": s["name"], "type": s["type"]}
            if parent:
                node["parent"] = parent
            pk = prev["id"] if prev else parent_key
            if pk:
                node["parentKey"] = pk
            if prev:
                prev["next"] = node_id
            templates.append(node)

            if s["type"] == "if_else":
                branch_ids = [nid(f"{path}/{i}/b{bi}") for bi in range(len(s["branches"]))]
                none_id = nid(f"{path}/{i}/none")
                all_ids = branch_ids + [none_id]
                node.update({
                    "attributes": {
                        "operator": "and", "segments": [], "if": True, "conditionName": s["name"],
                        "branches": [{
                            "id": bid, "name": bname,
                            "segments": [{"__segmentId": nid(f"{path}/{i}/b{bi}/seg"), "operator": "and",
                                          "conditions": [dict(cnd, __conditionId=nid(f"{path}/{i}/b{bi}/c{ci}"),
                                                              ifElseNodeId="", isWait=False)
                                                         for ci, cnd in enumerate(conds)]}],
                            "operator": "and", "showErrors": False,
                            "branchNameError": "Branch name cannot be empty!",
                        } for bi, (bid, (bname, conds, _)) in enumerate(zip(branch_ids, s["branches"]))],
                        "version": 2,
                    },
                    "cat": "conditions", "nodeType": "condition-node", "next": all_ids,
                })
                for bi, (bname, _, bsteps) in enumerate(s["branches"]):
                    bnode = {"id": branch_ids[bi], "parent": node_id, "parentKey": node_id,
                             "order": order + i + 1, "name": bname, "type": "if_else", "cat": "conditions",
                             "attributes": {"if": False, "conditionName": "Condition", "operator": "and",
                                            "branches": []},
                             "sibling": [x for x in all_ids if x != branch_ids[bi]],
                             "comments": [], "nodeType": "branch-yes"}
                    templates.append(bnode)
                    child = chain(bsteps, f"{path}/{i}/b{bi}", branch_ids[bi], branch_ids[bi], order + i + 2)
                    if child:
                        bnode["next"] = child
                nnode = {"id": none_id, "parent": node_id, "parentKey": node_id, "order": order + i + 1,
                         "name": "None", "type": "if_else", "cat": "conditions", "attributes": {"else": True},
                         "sibling": branch_ids, "nodeType": "branch-no"}
                templates.append(nnode)
                child = chain(s["none"], f"{path}/{i}/none", none_id, none_id, order + i + 2)
                if child:
                    nnode["next"] = child
                break  # GHL branches don't merge back

            if s["type"] == "workflow_split":
                path_ids = [nid(f"{path}/{i}/p{pi}") for pi in range(len(s["paths"]))]
                node.update({
                    "attributes": {
                        "name": "Split", "cat": "multi-path",
                        "transitions": [{"id": pid, "name": pname, "condition": pname, "conditionType": "default",
                                         "isPrimaryBranch": False, "description": "", "attributes": {}}
                                        for pid, (pname, _, _) in zip(path_ids, s["paths"])],
                        "type": "workflow_split",
                        "paths": [{"name": pname, "id": pid} for pid, (pname, _, _) in zip(path_ids, s["paths"])],
                        "condition": "random-split",
                        "extras": {"weightDistribution": {pid: pct for pid, (_, pct, _) in zip(path_ids, s["paths"])}},
                    },
                    "cat": "multi-path", "next": path_ids,
                })
                for pi, (pname, _, psteps) in enumerate(s["paths"]):
                    tnode = {"id": path_ids[pi], "parentKey": node_id, "parent": node_id, "type": "transition",
                             "name": pname, "attributes": {}, "order": order + i + 1, "cat": "transition"}
                    templates.append(tnode)
                    child = chain(psteps, f"{path}/{i}/p{pi}", path_ids[pi], path_ids[pi], order + i + 2)
                    if child:
                        tnode["next"] = child
                break

            node["attributes"] = s["attributes"]
            for k in ("workflowsActionType",):
                if k in s:
                    node[k] = s[k]
            prev = node
        return first

    chain(wf["steps"], "root", None, None, 0)

    wf_id = nid("workflow")
    trig = wf["trigger"]
    st = wf["settings"]
    return {
        "_id": wf_id,
        "locationId": a["location_id"],
        "name": wf["name"],
        "status": "draft",
        "version": 1,
        "dataVersion": 1,
        "allowMultiple": st["allowMultiple"],
        "timezone": st["timezone"],
        "removeContactFromLastStep": True,
        "stopOnResponse": st["stopOnResponse"],
        "autoMarkAsRead": False,
        "type": "workflow",
        "parentId": None,
        "deleted": False,
        "allowMultipleOpportunity": True,
        "creationSource": "builder",
        "originType": "user",
        "eventStartDate": None,
        "window": st["window"],
        "workflowNote": None,
        "id": wf_id,
        "workflowData": {"templates": templates},
        "scheduledPauseDates": [],
        "_triggers": [{
            "id": uuid.uuid5(NS, f"{account_key}/{wf['key']}/trigger").hex[:20],
            "deleted": False,
            "active": True,
            "actions": [{"workflow_id": wf_id, "type": "add_to_workflow"}],
            "conditions": trig["conditions"],
            "type": trig["type"],
            "masterType": "highlevel",
            "workflow_id": wf_id,
            "location_id": a["location_id"],
            "name": trig["name"],
            "belongs_to": "workflow",
            "schedule_config": {},
            "last_conditions_change_at": "",
        }],
    }


# ---------- build sheet ----------

def sheet_lines(steps, depth=0):
    pad = "  " * depth
    out = []
    for s in steps:
        out.append(f"{pad}- **{s['name']}** `{s['type']}`")
        if s["type"] == "sms":
            out.append(f"{pad}  > {s['attributes']['body']}")
        elif s["type"] == "if_else":
            for bname, conds, bsteps in s["branches"]:
                desc = "; ".join(f"{x['conditionSubType']} {x['conditionOperator']} {x['conditionValue']}" for x in conds)
                out.append(f"{pad}  - _Branch: {bname}_ ({desc})")
                out += sheet_lines(bsteps, depth + 2)
            out.append(f"{pad}  - _Branch: None_")
            out += sheet_lines(s["none"], depth + 2)
        elif s["type"] == "workflow_split":
            for pname, pct, psteps in s["paths"]:
                out.append(f"{pad}  - _Path: {pname} ({pct}%)_")
                out += sheet_lines(psteps, depth + 2)
    return out


def trigger_text(t):
    parts = []
    for x in t["conditions"]:
        if x["field"] == "message.type":
            parts.append("reply channel = SMS")
        else:
            parts.append(f"{x['title']}: {x['value']}")
    return f"{t['name']} (`{t['type']}`) - " + "; ".join(parts)


def main():
    dist = HERE / "dist"
    unfilled = {}
    sheet = ["# MARWOC Seller SMS - Build Sheet", "",
             "Generated by build.py from the same definitions as the JSON. "
             "If the importer skips a step, build it from here.", ""]
    for i, acct_file in enumerate(sorted((HERE / "accounts").glob("*.json"))):
        a = json.loads(acct_file.read_text())
        key = acct_file.stem
        out_dir = dist / key
        out_dir.mkdir(parents=True, exist_ok=True)
        for old in out_dir.glob("*.json"):
            old.unlink()
        files = []
        for fn in WORKFLOWS:
            wf = fn(a)
            path = out_dir / f"{wf['key']}.json"
            path.write_text(json.dumps(emit_workflow(wf, a, key), indent=2, ensure_ascii=True) + "\n")
            files.append(path)
            if i == 0:
                st = wf["settings"]
                sheet += [f"## {wf['name']}", "",
                          f"**Trigger:** {trigger_text(wf['trigger'])}  ",
                          f"**Settings:** timezone `{st['timezone']}`, stop on response `{st['stopOnResponse']}`, "
                          f"allow re-entry `{st['allowMultiple']}`, time window `{st['window']}`", ""]
                sheet += sheet_lines(wf["steps"]) + [""]
        with zipfile.ZipFile(dist / f"{key}.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for p in files:
                z.write(p, f"MARWOC SMS/{p.name}")
        unfilled[key] = sorted({v for v in json.dumps(a).split('"') if v.startswith("REPLACE_")})
    (HERE / "BUILD-SHEET.md").write_text("\n".join(sheet) + "\n")

    for key, vals in unfilled.items():
        if vals:
            print(f"[{key}] still has placeholders: {', '.join(vals)}")
    print("Wrote", ", ".join(str(p.relative_to(HERE)) for p in sorted(dist.rglob("*.*"))))


if __name__ == "__main__":
    main()
