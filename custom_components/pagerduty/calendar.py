import logging
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.util import dt as dt_util
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the calendar entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    async_add_entities([PagerDutyCalendar(coordinator)], True)

class PagerDutyCalendar(CalendarEntity):
    """Representation of a PagerDuty calendar."""

    def __init__(self, coordinator):
        """Initialize the PagerDuty calendar."""
        self.coordinator = coordinator
        self.user_id = self.coordinator.data.get("user_id")
        self._attr_name = "PagerDuty On-Call Schedule"
        self._attr_unique_id = f"pd_oncall_calendar_{self.user_id}"
        self._events = []

    async def async_get_events(self, hass, start_date, end_date):
        """Return events between start_date and end_date."""
        new_schedules = self.coordinator.data.get("on_call_schedules", [])
        temp_events = []

        for schedule_details in new_schedules:
            schedule_entries = schedule_details.get("final_schedule", {}).get(
                "rendered_schedule_entries"
            ) or schedule_details.get("schedule_layers", [{}])[0].get(
                "rendered_schedule_entries", []
            )

            for entry in schedule_entries:
                if entry.get("user", {}).get("id") == self.user_id:
                    start = self._parse_datetime(entry.get("start"))
                    end = self._parse_datetime(entry.get("end"))
                    if start and end and start <= end_date and end >= start_date:
                        event = self._create_event(entry, schedule_details, start, end)
                        temp_events.append(event)

        self._events = self._rebuild_day_events(start_date, temp_events)
        return self._events

    def _create_event(self, entry, schedule_details, start, end):
        """Create a new event from schedule entry."""
        unique_id_part = self._get_unique_id_part(entry, schedule_details["id"])
        uid = f"{schedule_details['id']}-{unique_id_part}"
        return CalendarEvent(
            summary=schedule_details["name"],
            start=start,
            end=end,
            location=entry["user"]["summary"],
            description=f"Schedule ID: {schedule_details['id']}",
            uid=uid,
        )

    def _rebuild_day_events(self, start_date, temp_events):
        """Rebuild events for each day if there are any changes."""
        updated_events = []
        for event in temp_events:
            if event.start.date() >= start_date.date() and not self._event_exists(event):
                updated_events.append(event)
        return updated_events

    def _event_exists(self, new_event):
        """Check if the event already exists in the calendar."""
        for event in self._events:
            if event.uid == new_event.uid:
                return True
        return False

    def _get_unique_id_part(self, entry, schedule_id):
        """Generate a unique part of ID for each entry."""
        entry_date = self._parse_datetime(entry.get("start")).date()
        return f"{schedule_id}-{entry_date}"

    @staticmethod
    def _parse_datetime(date_str):
        """Parse datetime string to datetime."""
        if not date_str:
            return None
        return dt_util.parse_datetime(date_str)

    @property
    def event(self):
        """Return the next upcoming event."""
        now = dt_util.now()
        upcoming_events = [e for e in self._events if e.end > now]
        if upcoming_events:
            return sorted(upcoming_events, key=lambda e: e.start)[0]
        return None