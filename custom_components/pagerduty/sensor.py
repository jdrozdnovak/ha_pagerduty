"""PagerDuty Service Incident Sensor for Home Assistant."""

import logging
from collections import defaultdict
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


# Setup platform remains largely the same, but without passing incidents
def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the PagerDuty incident sensors."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    sensors = []

    _LOGGER.debug("Setting up PagerDuty incident sensors")

    services_data = coordinator.data["services"]

    for service in services_data:
        service_id = service["id"]
        service_name = service["summary"]
        team_name = service.get("team_name", "Unknown")
        sensor_name = f"PD-{team_name}-{service_name}"
        sensor = PagerDutyIncidentSensor(coordinator, service_id, sensor_name)
        sensors.append(sensor)

    add_entities(sensors, True)


class PagerDutyIncidentSensor(SensorEntity, CoordinatorEntity):
    def __init__(self, coordinator, service_id, sensor_name):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._service_id = service_id
        self._attr_name = sensor_name
        self._attr_unique_id = f"pagerduty_{service_id}"
        self._incidents = []  # Initialize an empty list for incidents

        _LOGGER.debug(f"Initializing PagerDuty incident sensor: {self._attr_name}")

    @property
    def state(self):
        """Return the state of the sensor (total count of incidents)."""
        return len(self._incidents)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "incidents"

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        urgency_counts = defaultdict(int)
        status_counts = defaultdict(int)
        for incident in self._incidents:
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

    def _handle_coordinator_update(self):
        """Handle an update from the coordinator."""
        _LOGGER.debug(f"Updating PagerDuty incident sensor: {self._attr_name}")

        # Fetch new incidents for this service
        incidents_data = self.coordinator.data["incidents"]
        self._incidents = [
            inc for inc in incidents_data if inc["service"]["id"] == self._service_id
        ]

        _LOGGER.debug(f"Updated incidents count: {len(self._incidents)}")

        self.async_write_ha_state()

        super()._handle_coordinator_update()
