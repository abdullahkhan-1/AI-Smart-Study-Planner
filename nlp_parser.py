# =============================================================================
# nlp_parser.py — Natural Language Deadline Parser
# Smart Study Planner | SE Spring 2026
# =============================================================================
# Parses natural language deadline phrases into actual date objects.
#
# Strategy:
#   1. Custom pattern matcher — handles "next Friday", "end of month" etc.
#   2. dateparser library     — handles everything else
#   3. Returns None if unparseable so the UI can show a helpful error
#
# Examples:
#   "next Friday"      → nearest upcoming Friday
#   "in 3 days"        → today + 3
#   "end of month"     → last day of current month
#   "May 15"           → May 15 this/next year
#   "tomorrow"         → today + 1
#   "in 2 weeks"       → today + 14
# =============================================================================

import re
import dateparser
from datetime import date, datetime, timedelta
import calendar


# =============================================================================
# Helper: next occurrence of a weekday
# =============================================================================

WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    "mon": 0, "tue": 1, "wed": 2, "thu": 3,
    "fri": 4, "sat": 5, "sun": 6,
}

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

def _next_weekday(weekday_num: int) -> date:
    """Returns the next occurrence of weekday_num (0=Mon … 6=Sun) from today."""
    today = date.today()
    days_ahead = weekday_num - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)

def _end_of_month(year: int, month: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day)


# =============================================================================
# Custom pattern matching (handles what dateparser misses)
# =============================================================================

def _custom_parse(text: str) -> date | None:
    """
    Tries to match common NLP patterns manually before falling back
    to the dateparser library.
    """
    t     = text.strip().lower()
    today = date.today()

    # "tomorrow"
    if t in ("tomorrow", "tmrw", "tmr"):
        return today + timedelta(days=1)

    # "today" — not valid as deadline but handle gracefully
    if t == "today":
        return today + timedelta(days=1)   # treat as tomorrow

    # "next week"
    if t in ("next week", "in a week"):
        return today + timedelta(weeks=1)

    # "next month"
    if t in ("next month", "in a month"):
        month = today.month + 1 if today.month < 12 else 1
        year  = today.year if today.month < 12 else today.year + 1
        return date(year, month, today.day)

    # "end of month" / "end of the month"
    if re.match(r"end of (the )?month", t):
        return _end_of_month(today.year, today.month)

    # "end of [month name]" e.g. "end of April"
    m = re.match(r"end of (\w+)", t)
    if m and m.group(1) in MONTHS:
        month_num = MONTHS[m.group(1)]
        year      = today.year if month_num >= today.month else today.year + 1
        return _end_of_month(year, month_num)

    # "next [weekday]" e.g. "next Friday"
    m = re.match(r"next (\w+)", t)
    if m and m.group(1) in WEEKDAYS:
        d = _next_weekday(WEEKDAYS[m.group(1)])
        # "next" implies at least 7 days ahead if today is that weekday
        if d <= today + timedelta(days=1):
            d += timedelta(weeks=1)
        return d

    # "this [weekday]" e.g. "this Friday"
    m = re.match(r"this (\w+)", t)
    if m and m.group(1) in WEEKDAYS:
        return _next_weekday(WEEKDAYS[m.group(1)])

    # "[weekday]" alone e.g. "Friday"
    if t in WEEKDAYS:
        return _next_weekday(WEEKDAYS[t])

    # "in X days" / "in X day"
    m = re.match(r"in (\d+) days?", t)
    if m:
        return today + timedelta(days=int(m.group(1)))

    # "in X weeks"
    m = re.match(r"in (\d+) weeks?", t)
    if m:
        return today + timedelta(weeks=int(m.group(1)))

    # "in X months"
    m = re.match(r"in (\d+) months?", t)
    if m:
        n     = int(m.group(1))
        month = ((today.month - 1 + n) % 12) + 1
        year  = today.year + (today.month - 1 + n) // 12
        return date(year, month, today.day)

    # "X days from now"
    m = re.match(r"(\d+) days? from now", t)
    if m:
        return today + timedelta(days=int(m.group(1)))

    # "X weeks from now"
    m = re.match(r"(\d+) weeks? from now", t)
    if m:
        return today + timedelta(weeks=int(m.group(1)))

    return None   # No custom match — fall through to dateparser


# =============================================================================
# Main public function
# =============================================================================

def parse_deadline(text: str) -> dict:
    """
    Parse a natural language deadline string into a date.

    Returns a dict:
      {
        "success" : True/False,
        "date"    : date object or None,
        "date_str": "2026-05-15" or None,
        "method"  : "custom" | "dateparser" | "failed",
        "message" : human-readable explanation
      }
    """
    if not text or not text.strip():
        return {"success": False, "date": None, "date_str": None,
                "method": "failed", "message": "No input provided."}

    original = text.strip()
    today    = date.today()

    # --- Step 1: Try custom patterns ---
    result = _custom_parse(original)
    method = "custom"

    # --- Step 2: Fall back to dateparser ---
    if result is None:
        parsed = dateparser.parse(
            original,
            languages=["en"],
            settings={
                "PREFER_DATES_FROM"      : "future",
                "RELATIVE_BASE"          : datetime.now(),
                "RETURN_AS_TIMEZONE_AWARE": False,
            }
        )
        if parsed:
            result = parsed.date()
            method = "dateparser"

    # --- Step 3: Evaluate result ---
    if result is None:
        return {
            "success" : False,
            "date"    : None,
            "date_str": None,
            "method"  : "failed",
            "message" : f'Could not understand "{original}". Try: "in 5 days", "next Friday", "May 20".'
        }

    if result <= today:
        return {
            "success" : False,
            "date"    : None,
            "date_str": None,
            "method"  : "failed",
            "message" : f'Parsed "{result}" but that date is in the past. Please use a future date.'
        }

    days_away = (result - today).days
    return {
        "success"  : True,
        "date"     : result,
        "date_str" : str(result),
        "method"   : method,
        "message"  : f'Understood as {result.strftime("%B %d, %Y")} ({days_away} days away)'
    }
