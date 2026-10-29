"""Seller SMS copy: the client's 5 sample messages, verbatim from the MARWOC spec.

Merge fields: {{first name}} -> {{contact.first_name}}, {{street}} -> {{contact.address1}},
[name] (the rep) -> {{custom_values.sms_rep_name}}. No other wording changes.
"""

F = "{{contact.first_name}}"
S = "{{contact.address1}}"
R = "{{custom_values.sms_rep_name}}"
B = "{{custom_values.sms_business_name}}"
PHONE = "{{custom_values.sms_business_phone}}"

SAMPLES = [
    f"Hey {F}, it's {R} — real person here, not a call center, I promise. I came across your place on {S} and figured I'd just ask: ever thought about selling it? Totally fine if not. (Reply STOP and I'll leave you be.)",
    f"{F}, I know you probably get a hundred of these. I'm not here to lowball you or waste your time — we're a small, veteran-owned outfit that actually buys houses around here. Mind if I ask what your plans are for {S}?",
    f"Hey {F} — totally cool if this isn't for you, I'd just rather ask than assume. Is the house on {S} something you've thought about selling, or are you planning to hang onto it?",
    f"{F}, real talk — if the timing's off or you're just not interested, say the word and I'll quit bugging you. But if you've even thought about selling {S}, I'd love to see if we can make it easy on you.",
    f"Hi {F}, it's {R}. No fancy sales pitch here — we're local, we're veterans, and we buy a few houses around town. Just wondering if you'd ever want to talk about {S}. If not, no worries at all.",
]

# 5 touches spread across a 6-8 week run (spec Part 1/2). Day offsets from enrollment.
TOUCH_DAYS = [0, 12, 24, 36, 48]

# Each track sends all 5 samples, starting at a different one, so at every touch
# recipients are split across all 5 wordings (spec Part 2: no identical broadcast text).
TRACKS = ["A", "B", "C", "D", "E"]


def track_messages(track_index):
    return [SAMPLES[(track_index + k) % len(SAMPLES)] for k in range(len(TOUCH_DAYS))]


# HELP auto-response with business identity (spec Part 4).
HELP_REPLY = f"{B}: texts from {R} about your property. Questions? Call {PHONE}. Reply STOP to opt out."

# Opt-out keywords (spec Part 4: STOP / opt-out handling). END, QUIT and CANCEL are
# handled by GHL's built-in carrier keyword processing; as "contains" phrases they
# would also match ordinary words like "weekend".
OPT_OUT_PHRASES = ["stop", "stopall", "unsubscribe"]

# "stop/not interested" routing (spec Part 5) and "should not be contacted" (spec Part 1).
NOT_INTERESTED_PHRASES = [
    "not interested", "no thanks", "no thank you", "not selling", "not for sale",
    "already sold", "sold it", "wrong number", "wrong person", "don't own", "dont own",
]

# "yes/interested" routing (spec Part 5).
INTERESTED_PHRASES = [
    "yes", "yeah", "yep", "sure", "maybe", "interested", "how much", "offer", "price", "call me",
]

HELP_PHRASES = ["help"]
