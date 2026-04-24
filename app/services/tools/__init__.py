"""
Tools package — LangChain @tool functions split by domain.

Exports get_all_tools() for dynamic tool registration.
"""

from app.services.tools.events import (
    search_events,
    get_event_details,
    get_similar_events,
    get_trending_events,
)
from app.services.tools.users import (
    get_user_profile,
    get_recommendations,
)
from app.services.tools.tickets import (
    get_user_tickets,
    get_user_orders,
    lookup_ticket_by_code,
)
from app.services.tools.support import (
    open_support_case,
    get_support_case,
    get_user_support_cases,
)
from app.services.tools.reviews import (
    submit_review,
    get_event_reviews,
)
from app.services.tools.organizer import (
    get_organizer_events,
    get_event_analytics,
    get_event_reviews_organizer,
)
from app.services.tools.interactions import (
    log_interaction,
)

# Grouped tool lists
event_tools = [search_events, get_event_details, get_similar_events, get_trending_events]
user_tools = [get_user_profile, get_recommendations]
ticket_tools = [get_user_tickets, get_user_orders, lookup_ticket_by_code]
support_tools = [open_support_case, get_support_case, get_user_support_cases]
review_tools = [submit_review, get_event_reviews]
organizer_tools = [get_organizer_events, get_event_analytics, get_event_reviews_organizer]
interaction_tools = [log_interaction]


def get_all_tools():
    """Return all tools as a flat list for LLM binding."""
    return [
        *event_tools,
        *user_tools,
        *ticket_tools,
        *support_tools,
        *review_tools,
        *organizer_tools,
        *interaction_tools,
    ]


# Backward-compatible export
ALL_TOOLS = get_all_tools()
