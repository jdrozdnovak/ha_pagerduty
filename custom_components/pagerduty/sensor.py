import logging
from collections import defaultdict
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import PagerDutyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up PagerDuty sensors from a config entry."""
    coordinator: PagerDutyDataUpdateCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]
    user_id = coordinator.data.get("user_id", "")

    # Static sensor descriptions
    sensor_descriptions = [
        {
            "key": "total_incidents",
            "name": "PagerDuty Total Incidents",
            "value_fn": lambda data: len(data.get("incidents", [])),
            "unique_id": f"pagerduty_total_incidents_{user_id}",
        },
        {
            "key": "assigned_incidents",
            "name": "PagerDuty Assigned Incidents",
            "value_fn": lambda data: sum(
                1
                for incident in data.get("incidents", [])
                for assignee in incident.get("assignments", [])
                if assignee.get("assignee", {}).get("id") == user_id
            ),
            "unique_id": f"pagerduty_assigned_incidents_{user_id}",
        },
    ]

    # Dynamic sensor descriptions for each service
    services_data = coordinator.data.get("services", [])
    for service in services_data:
        service_id = service["id"]
        service_name = service["summary"]
        sensor_name = f"PD-{service_name}"
        sensor_descriptions.append(
            {
                "key": f"service_{service_id}",
                "name": sensor_name,
                "value_fn": lambda data, service_id=service_id: sum(
                    1
                    for incident in data.get("incidents", [])
                    if incident["service"]["id"] == service_id
                ),
                "unique_id": f"pagerduty_service_{service_id}",
            }
        )

    # Create sensor entities
    sensors = [
        PagerDutySensor(coordinator, desc) for desc in sensor_descriptions
    ]
    async_add_entities(sensors, True)


class PagerDutySensor(SensorEntity, CoordinatorEntity):
    """Generic sensor for PagerDuty incidents."""

    def __init__(self, coordinator, description):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = description["name"]
        self._value_fn = description["value_fn"]
        self._attr_unique_id = description["unique_id"]
        self._urgency_counts = defaultdict(int)
        self._status_counts = defaultdict(int)
        self._assigned_incidents = []

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        # Update these attributes based on the coordinator's data
        self._update_extra_attributes()
        return {
            "urgency_low": self._urgency_counts["low"],
            "urgency_high": self._urgency_counts["high"],
            "status_triggered": self._status_counts["triggered"],
            "status_acknowledged": self._status_counts["acknowledged"],
        }

    def _update_extra_attributes(self):
        """Update urgency counts, status counts, and assigned incidents."""
        # Implement the logic to update these attributes based on the coordinator's data
        # Example (you need to adjust this according to your actual data structure):
        for incident in self.coordinator.data.get("incidents", []):
            urgency = incident.get("urgency", "unknown")
            status = incident.get("status", "unknown")
            self._urgency_counts[urgency] += 1
            self._status_counts[status] += 1
            # Add logic to update _assigned_incidents if applicable
