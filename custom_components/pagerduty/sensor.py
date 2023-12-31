import logging
from collections import defaultdict
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up PagerDuty sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    user_id = coordinator.data.get("user_id", "")

    # Static sensor descriptions
    sensor_descriptions = [
        {
            "key": "total_incidents",
            "name": "PagerDuty Total Incidents",
            "value_fn": lambda data: len(data.get("incidents", [])),
            "unique_id": f"pagerduty_total_incidents_{user_id}",
            "attribute_fn": lambda data: calculate_attributes(data, None)
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
            "attribute_fn": lambda data: calculate_attributes(data, user_id)
        },
    ]

    # Dynamic sensor descriptions for each service
    services_data = coordinator.data.get("services", [])
    for service in services_data:
        service_id = service["id"]
        service_name = service["summary"]
        team_name = service["team_name"]
        team_id = service["team_id"]
        if team_id:
            unique_id = f"pagerduty_{team_id}_{service_id}"
        else:
            unique_id = f"pagerduty_{service_id}"
        if team_name:
            _LOGGER.debug("User is part of team, using team_name")
            sensor_name = f"PD-{team_name}-{service_name}"
        else:
            _LOGGER.debug("Skipping team name")
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
                "unique_id": unique_id,
                "attribute_fn": lambda data, service_id=service_id: calculate_attributes(data, service_id)
            }
        )

    # Create sensor entities
    sensors = [
        PagerDutySensor(coordinator, desc) for desc in sensor_descriptions
    ]
    _LOGGER.debug("PagerDuty sensors created: %s", sensors)
    async_add_entities(sensors, True)


def calculate_attributes(data, service_id):
    """Calculate attributes for a sensor."""
    urgency_counts = defaultdict(int)
    status_counts = defaultdict(int)
    for incident in data.get("incidents", []):
        if service_id is None or incident["service"]["id"] == service_id:
            urgency = incident.get("urgency", "unknown")
            status = incident.get("status", "unknown")
            urgency_counts[urgency] += 1
            status_counts[status] += 1
    return {
        "urgency_low": urgency_counts["low"],
        "urgency_high": urgency_counts["high"],
        "status_triggered": status_counts["triggered"],
        "status_acknowledged": status_counts["acknowledged"],
    }


class PagerDutySensor(SensorEntity, CoordinatorEntity):
    """Generic sensor for PagerDuty incidents."""

    def __init__(self, coordinator, description):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = description["name"]
        self._value_fn = description["value_fn"]
        self._attr_unique_id = description["unique_id"]
        self._attribute_fn = description["attribute_fn"]
        _LOGGER.debug("Initialized PagerDuty sensor: %s", self._attr_name)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self._value_fn(self.coordinator.data)
        _LOGGER.debug("Sensor '%s' native value: %s", self._attr_name, value)
        return value

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        attributes = self._attribute_fn(self.coordinator.data)
        _LOGGER.debug(
            "Sensor '%s' extra state attributes: %s",
            self._attr_name,
            attributes,
        )
        return attributes
