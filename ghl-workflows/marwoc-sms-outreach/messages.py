"""Seller SMS copy: 8 touches x 5 voice tracks (A-E).

Rules this copy follows on purpose:
- Plain GSM-7 characters only (straight apostrophes, no em dashes, no emoji).
  One curly quote or em dash flips the whole message to UCS-2, which cuts a
  segment from 160 to 70 characters and roughly doubles the per-text cost.
- No links, no ALL-CAPS, no exclamation points, no urgency.
- Business identity + opt-out language in touch 1 and touch 8; identity again in touch 4.
"""

F = "{{contact.first_name}}"
S = "{{contact.address1}}"
R = "{{custom_values.sms_rep_name}}"
B = "{{custom_values.sms_business_name}}"
PHONE = "{{custom_values.sms_business_phone}}"

# (day offset from enrollment, short label)
TOUCHES = [
    (0, "Opener"),
    (3, "Bump"),
    (7, "Plans question"),
    (14, "Who we are"),
    (21, "Timing"),
    (30, "Permission check"),
    (40, "Light check-in"),
    (49, "Close the loop"),
]

TRACKS = ["A", "B", "C", "D", "E"]

MESSAGES = {
    "A": [
        f"Hey {F}, it's {R} with {B}. Real person here, not a call center, I promise. I came across your place on {S} and figured I'd just ask, ever thought about selling it? Totally fine if not. Reply STOP and I'll leave you be.",
        f"Hey {F}, {R} again. Just floating this back up in case it got buried. Any thoughts on {S}? Even a quick 'not now' helps me out.",
        f"{F}, quick question if you don't mind. Are you living at {S} right now, renting it out, or is it sitting empty?",
        f"Hi {F}, {R} with {B}. Figured I should say a little more about us. We're a small, veteran-owned team, we're local, and we keep things simple. If {S} is ever on the table, I'm easy to reach right here.",
        f"Hey {F}, timing question. If you ever did sell {S}, would it be in the next few months, next year, or no time soon?",
        f"{F}, I don't want to be that guy who won't stop texting. Should I keep you on my list for {S}, or take you off? Either's fine.",
        f"Hi {F}, {R} here. Just thinking about {S} again. If anything's come up with the house, I'm around.",
        f"{F}, this is my last text about {S}. If you ever want to talk, just reply here and it comes straight to me. Thanks for putting up with me. - {R}, {B}. Reply STOP to opt out.",
    ],
    "B": [
        f"Hi {F}, {R} with {B} here. I know you probably get a hundred of these. I'm not here to lowball you or waste your time, we're a small veteran-owned outfit that buys houses around here. Mind if I ask what your plans are for {S}? Reply STOP to opt out.",
        f"Hi {F}, following up on my text about {S}. No rush at all, just wanted to make sure it actually reached you.",
        f"Hey {F}, just curious, what's the long-term plan for {S}? Keep it, rent it, sell it someday? No wrong answer.",
        f"{F}, it's {R} from {B}. We're not a big national outfit, just a few of us who buy houses around here. If you ever want to talk about {S}, text back anytime.",
        f"Hi {F}, {R} here. Is now just a bad time to think about {S}? If so, tell me when would be better and I'll check back then.",
        f"Hey {F}, {R} here. Want me to keep checking in about {S} every so often, or would you rather I stop? Either answer is fine.",
        f"Hey {F}, no agenda, just checking in. If you ever want to talk about selling {S}, we're still here.",
        f"Hi {F}, {R} with {B}. I'll stop reaching out about {S} after this one. If things change down the road, my door's open. Reply STOP to opt out.",
    ],
    "C": [
        f"Hey {F}, it's {R} with {B}. Totally cool if this isn't for you, I'd just rather ask than assume. Is the house on {S} something you've thought about selling, or are you planning to hang onto it? Reply STOP to opt out.",
        f"{F}, it's {R}. I know texts from strangers get ignored, fair enough. If you've got a minute, I'd still like to hear your plans for {S}.",
        f"Hi {F}, if you did sell {S}, would you fix it up first or sell it the way it is? Just trying to understand how you see it.",
        f"Hey {F}, {R} with {B}. A lot of folks ask who we are before they reply, which makes sense. We're veteran-owned and local, and we only buy a few houses at a time. Happy to answer anything about {S}.",
        f"{F}, sometimes the answer is 'not yet' and that's fine. Want me to circle back on {S} in a few months instead?",
        f"Hi {F}, quick check. Is it okay if I keep reaching out about {S}, or should I leave you be? No hard feelings either way.",
        f"{F}, it's been a few weeks. Anything new with {S}? Even if the answer's no, I appreciate you reading these.",
        f"Hey {F}, closing the loop on {S} so I'm not cluttering your phone. If selling ever makes sense, text this number anytime. - {R} with {B}. Reply STOP to opt out.",
    ],
    "D": [
        f"{F}, it's {R} with {B}. Real talk, if the timing's off or you're just not interested, reply STOP and I'll quit bugging you. But if you've even thought about selling {S}, I'd love to see if we can make it easy on you.",
        f"Hey {F}, circling back on {S}. If selling's not on your mind, totally fine, just tell me and I'll stop.",
        f"{F}, not trying to push here. If {S} ever turned into more hassle than it's worth, would you want someone local to talk to about it?",
        f"Hi {F}, {R} here with {B}. We're veterans and we're local. No pressure on {S}, just want you to know there's a real person on this end.",
        f"Hey {F}, quick one. Has anything changed with {S} since I first reached out, or is it pretty much the same?",
        f"{F}, I've reached out a few times about {S} and I don't want to overdo it. Still worth staying in touch, or should I back off?",
        f"Hi {F}, {R} with {B} checking in. Still happy to talk about {S} whenever it suits you.",
        f"{F}, last one from me, I promise. If {S} is ever something you want to talk about, I'm a text away. Take care. - {R}, {B}. Reply STOP to opt out.",
    ],
    "E": [
        f"Hi {F}, it's {R} with {B}. No fancy sales pitch here, we're local, we're veterans, and we buy a few houses around town. Just wondering if you'd ever want to talk about {S}. If not, no worries at all. Reply STOP to opt out.",
        f"Hi {F}, {R} here again. Didn't want my last text to just sit there. Any interest in talking about {S}, now or down the road?",
        f"Hey {F}, honest question. Is {S} a someday-maybe thing for you, or a definitely-keeping-it thing? Either answer helps me.",
        f"{F}, it's {R} from {B}. In case it helps, we're a small local team, veteran-owned, and we'd rather have one honest conversation than send you twenty texts. Any interest on {S}?",
        f"Hi {F}, I'll keep it short. If selling {S} ever makes sense for you, what would the timing look like?",
        f"Hey {F}, being respectful of your time here. Do you want to hear from me again about {S}, or should I close this out?",
        f"Hey {F}, hope things are good. If your plans for {S} have shifted at all, I'd be glad to hear about it.",
        f"Hi {F}, it's {R} with {B}. I'll leave you be after this. Thanks for reading, and if anything changes with {S}, you know where to find me. Reply STOP to opt out.",
    ],
}

HELP_REPLY = (
    f"{B}: you're getting texts from {R} about your property. "
    f"Questions? Call {PHONE}. Msg & data rates may apply. Reply STOP to opt out."
)

# Keyword lists for the customer_reply triggers ("Contains phrase", any of).
# Matching is substring-based, so single words that hide inside normal words
# (END, QUIT, CANCEL) are left to GHL's built-in carrier keyword handling.
OPT_OUT_PHRASES = [
    "stop", "stopall", "unsubscribe", "remove me", "take me off", "opt out", "optout",
    "do not text", "don't text", "dont text", "do not contact", "don't contact", "dont contact",
    "lose my number", "leave me alone", "no more texts", "revoke",
]
WRONG_NUMBER_PHRASES = [
    "wrong number", "wrong person", "don't own", "dont own", "do not own",
    "never owned", "not my house", "not my property",
]
HARD_NO_PHRASES = [
    "not interested", "no thanks", "no thank you", "not selling", "not for sale",
    "already sold", "sold it", "not looking to sell", "never selling",
]
POSITIVE_PHRASES = [
    "yes", "yeah", "yep", "sure", "maybe", "how much", "what would you",
    "make an offer", "make me an offer", "your offer", "price", "depends",
    "call me", "possibly", "thinking about it", "open to", "what's your number",
]
HELP_PHRASES = ["help"]
