"""
Guardrails — domain scope control.

Determines whether the user's message is related to the
Events & Tickets platform using flexible intent detection.
"""

import re
import logging

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  Out-of-scope response messages
# ──────────────────────────────────────────────
OUT_OF_SCOPE_EN = (
    "I'm Tegy, your events assistant — I'm here to help you discover events, "
    "manage your tickets, and get support. Is there something I can help you find?"
)

OUT_OF_SCOPE_AR = (
    "أنا تيجي، مساعدك للفعاليات — هنا لمساعدتك في اكتشاف "
    "الفعاليات وإدارة تذاكرك والحصول على الدعم. هل هناك شيء أقدر أساعدك فيه؟"
)

PII_MESSAGE_EN = "For your security, please do not share personal information like credit card numbers, SSNs, phone numbers, or emails."
PII_MESSAGE_AR = "لحمايتك، يرجى عدم مشاركة معلومات شخصية مثل أرقام البطاقات الائتمانية أو أرقام الهواتف أو البريد الإلكتروني."

# ──────────────────────────────────────────────
#  PII Patterns
# ──────────────────────────────────────────────
_PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), # SSN
    re.compile(r"\b(?:\d[ -]*?){13,16}\b"), # Credit Card
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), # Email
    re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b") # Phone
]


# ──────────────────────────────────────────────
#  In-scope keywords (Events & Tickets domain)
# ──────────────────────────────────────────────
_IN_SCOPE_KEYWORDS_EN = [
    # Events
    "event", "events", "concert", "festival", "conference", "workshop",
    "webinar", "exhibition", "meetup", "show", "party", "seminar",
    "happening", "upcoming", "trending", "popular", "discover",
    "search", "find", "browse", "explore", "recommend", "suggest",
    "similar", "category", "music", "sports", "art", "business",
    "technology", "education", "food", "health", "travel", "fashion",
    "gaming", "science", "charity", "comedy", "theater", "photography",
    "literature", "networking",
    # Tickets
    "ticket", "tickets", "booking", "book", "buy", "purchase",
    "booking code", "seat", "available", "availability", "sold out",
    "price", "cost", "free", "paid", "affordable", "cheap", "expensive",
    # Orders
    "order", "orders", "payment", "paid", "receipt", "invoice",
    "purchase history", "transaction",
    # Support
    "support", "help", "issue", "problem", "refund", "cancel",
    "complaint", "wrong", "broken", "not received", "charged twice",
    "not working", "error", "bug", "case", "support case",
    # Reviews
    "review", "reviews", "rating", "ratings", "feedback", "rate",
    "stars", "opinion",
    # Organizer
    "organizer", "organiser", "create event", "my events",
    "analytics", "revenue", "sales", "sell-through", "attendees",
    "dashboard", "performance", "verified",
    # Account
    "account", "profile", "my account", "settings",
    # Platform
    "platform", "tegy", "how does", "how do", "how to", "what is",
    # Location
    "city", "online", "venue", "place", "location", "near me",
    # General interactions
    "love", "share", "view", "interested",
]

_IN_SCOPE_KEYWORDS_AR = [
    # Events
    "فعالية", "فعاليات", "حدث", "أحداث", "حفلة", "مهرجان", "مؤتمر",
    "ورشة", "ندوة", "معرض", "عرض", "قادم", "قادمة", "شائع",
    "اكتشف", "ابحث", "بحث", "توصية", "اقتراح", "مشابه",
    "موسيقى", "رياضة", "فن", "تكنولوجيا", "تعليم", "طعام",
    "صحة", "سفر", "أزياء", "ألعاب", "علوم", "خيري", "كوميدي",
    "مسرح", "تصوير",
    # Tickets
    "تذكرة", "تذاكر", "حجز", "احجز", "شراء", "اشتري",
    "كود الحجز", "مقعد", "متاح", "متاحة", "نفدت", "سعر",
    # Orders
    "طلب", "طلبات", "دفع", "فاتورة", "مشتريات",
    # Support
    "دعم", "مساعدة", "مشكلة", "استرجاع", "إلغاء", "شكوى",
    "خطأ", "لم يصل", "خصم مرتين",
    # Reviews
    "تقييم", "تقييمات", "مراجعة", "رأي", "نجوم",
    # Organizer
    "منظم", "إنشاء فعالية", "فعالياتي", "تحليلات", "إيرادات",
    "مبيعات", "حضور",
    # Account
    "حساب", "حسابي", "الملف الشخصي",
    # Platform
    "تيجي", "المنصة", "كيف", "ما هو", "ما هي",
    # Location
    "مدينة", "أونلاين", "مكان", "موقع", "قريب",
]

# Combine all keywords
_ALL_SCOPE_KEYWORDS = _IN_SCOPE_KEYWORDS_EN + _IN_SCOPE_KEYWORDS_AR

# ──────────────────────────────────────────────
#  Greeting patterns (always in-scope)
# ──────────────────────────────────────────────
_GREETING_PATTERNS = re.compile(
    r"^(hi|hello|hey|yo|sup|good\s*(morning|afternoon|evening|day)|"
    r"مرحبا|أهلا|السلام عليكم|صباح الخير|مساء الخير|هاي|هلا)"
    r"[!.,\s]*$",
    re.IGNORECASE | re.UNICODE,
)

# Short follow-up patterns (e.g., "yes", "no", "ok", "thanks")
_FOLLOWUP_PATTERNS = re.compile(
    r"^(yes|no|yeah|yep|nope|ok|okay|sure|thanks|thank you|please|"
    r"cool|great|alright|got it|understood|perfect|nice|awesome|"
    r"نعم|لا|أيوا|لأ|تمام|شكرا|من فضلك|طيب|ماشي|أوك|حلو|تمام كده)"
    r"[!.,\s]*$",
    re.IGNORECASE | re.UNICODE,
)

# ──────────────────────────────────────────────
#  Clearly off-topic patterns
# ──────────────────────────────────────────────
_OFF_TOPIC_PATTERNS = [
    re.compile(r"\b(what is the capital of|who is the president|solve this equation)\b", re.IGNORECASE),
    re.compile(r"\b(write me a (poem|essay|story|code|script|program))\b", re.IGNORECASE),
    re.compile(r"\b(weather in|forecast for|temperature in)\b", re.IGNORECASE),
    re.compile(r"\b(how to (cook|code|program|hack|build a))\b", re.IGNORECASE),
    re.compile(r"\b(medical advice|legal advice|diagnose|symptom)\b", re.IGNORECASE),
    re.compile(r"\b(translate .+ to|what does .+ mean in)\b", re.IGNORECASE),
]


# ──────────────────────────────────────────────
#  Scope Detection (flexible)
# ──────────────────────────────────────────────
def is_in_scope(user_message: str) -> bool:
    """
    Determine if the user's message is related to the Events & Tickets platform.

    Strategy (permissive — only blocks clearly off-topic messages):
    1. Empty / very short → allow (let LLM handle clarification)
    2. Greetings / follow-ups → always allow
    3. If any in-scope keyword found → allow
    4. If message is clearly off-topic (matches off-topic patterns) → block
    5. If uncertain → allow (let the LLM's system prompt handle scope)

    Returns True if in-scope, False only if clearly off-topic.
    """
    if not user_message or not user_message.strip():
        return True  # Empty → let the LLM ask for clarification

    text = user_message.strip().lower()

    # Greetings are always in-scope
    if _GREETING_PATTERNS.match(text):
        return True

    # Short follow-ups are always in-scope (contextual)
    if _FOLLOWUP_PATTERNS.match(text):
        return True

    # Very short messages (1-4 words) — almost always contextual, allow
    if len(text.split()) <= 4:
        return True

    # Keyword matching — if ANY scope keyword is found, allow
    for kw in _ALL_SCOPE_KEYWORDS:
        if kw.lower() in text:
            return True

    # Check for clearly off-topic patterns
    for pattern in _OFF_TOPIC_PATTERNS:
        if pattern.search(text):
            logger.warning(f"[GUARDRAILS] Out-of-scope (off-topic pattern): {user_message[:100]}")
            return False

    # When uncertain — be permissive and allow.
    # The LLM's system prompt already instructs it to stay on topic,
    # so it will redirect off-topic queries naturally.
    return True


def get_out_of_scope_message(language: str = "en") -> str:
    """Return the appropriate out-of-scope message based on language."""
    if language == "ar":
        return OUT_OF_SCOPE_AR
    return OUT_OF_SCOPE_EN

def has_pii(user_message: str) -> bool:
    """Check if message contains PII."""
    for pattern in _PII_PATTERNS:
        if pattern.search(user_message):
            logger.warning("[GUARDRAILS] PII detected in user message.")
            return True
    return False

def get_pii_message(language: str = "en") -> str:
    """Return the appropriate PII warning message based on language."""
    if language == "ar":
        return PII_MESSAGE_AR
    return PII_MESSAGE_EN
