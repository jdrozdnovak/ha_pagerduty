import logging
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.util import dt as dt_util
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PagerDutyCalendarData:
    """Class to handle the fetching and processing of PagerDuty events."""

    def __init__(self, coordinator, user_id):
        """Initialize the data object."""
        self.coordinator = coordinator
        self.user_id = user_id
        self.events = []

    async def fetch_all_events(self):
        """Fetch all events from the coordinator data."""
        self.events.clear()  # Clear existing events before fetching new ones
        new_schedules = self.coordinator.data.get("on_call_schedules", [])
        for schedule_details in new_schedules:
            self._process_schedule(schedule_details)
        return self.events

    def _process_schedule(self, schedule_details):
        """Process each schedule to extract events."""
        schedule_entries = schedule_details.get("final_schedule", {}).get(
            "rendered_schedule_entries"
        ) or schedule_details.get("schedule_layers", [{}])[0].get(
            "rendered_schedule_entries", []
        )
        for entry in schedule_entries:
            if entry.get("user", {}).get("id") == self.user_id:
                self._add_event(entry, schedule_details)

    def _add_event(self, entry, schedule_details):
        """Add an event to the events list."""
        start = self._parse_datetime(entry.get("start"))
        end = self._parse_datetime(entry.get("end"))
        event = self._create_event(entry, schedule_details, start, end)
        self.events.append(event)

    def _create_event(self, entry, schedule_details, start, end):
        """Create a new CalendarEvent from a schedule entry."""
        unique_id_part = self._get_unique_id_part(
            entry, schedule_details["id"]
        )
        uid = f"{schedule_details['id']}-{unique_id_part}"
        return CalendarEvent(
            summary=schedule_details["name"],
            start=start,
            end=end,
            location=entry["user"]["summary"],
            description=f"Schedule ID: {schedule_details['id']}",
            uid=uid,
        )

    @staticmethod
    def _get_unique_id_part(entry, schedule_id):
        """Generate a unique part of an ID for each entry."""
        entry_date = PagerDutyCalendarData._parse_datetime(
            entry.get("start")
        ).date()
        return f"{schedule_id}-{entry_date}"

    @staticmethod
    def _parse_datetime(date_str):
        """Parse datetime string to a datetime object."""
        if not date_str:
            return None
        return dt_util.parse_datetime(date_str)


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
        self.calendar_data = PagerDutyCalendarData(
            self.coordinator, self.user_id
        )
        self._events = []

    @property
    def device_info(self):
        """Return device info for linking this entity to the unique PagerDuty device."""
        unique_device_name = f"PagerDuty_{self.coordinator.data.get('user_id', 'default_user_id')}"
        return {
            "identifiers": {(DOMAIN, unique_device_name)},
            "name": unique_device_name,
            "manufacturer": "PagerDuty Inc.",
            "via_device": (DOMAIN, unique_device_name),
        }

    async def async_get_events(self, hass, start_date, end_date):
        """Return events between start_date and end_date."""
        all_events = await self.calendar_data.fetch_all_events()
        return [
            event
            for event in all_events
            if event.start <= end_date and event.end >= start_date
        ]

    async def async_update(self):
        """Fetch new events and update."""
        await self.calendar_data.fetch_all_events()
        self._events = self.calendar_data.events

    @property
    def event(self):
        """Return the next upcoming event."""
        now = dt_util.now()
        upcoming_events = [e for e in self._events if e.end > now]
        if upcoming_events:
            return sorted(upcoming_events, key=lambda e: e.start)[0]
        return None
