"""PagerDuty Service Incident Sensor for Home Assistant."""

import logging
from collections import defaultdict
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the PagerDuty incident sensors."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    sensors = []

    _LOGGER.debug("Setting up PagerDuty incident sensors")

    services_data = coordinator.data["services"]
    incidents_data = coordinator.data["incidents"]

    for service in services_data:
        service_id = service["id"]
        service_name = service["summary"]  # Corrected here from 'summay' to 'summary'
        incidents = [
            inc for inc in incidents_data if inc["service"]["id"] == service_id
        ]

        sensor = PagerDutyIncidentSensor(
            coordinator, service_id, service_name, incidents
        )
        sensors.append(sensor)
        _LOGGER.debug(
            f"Created sensor for service {service_id} with {len(incidents)} incidents"
        )

    add_entities(sensors, True)


class PagerDutyIncidentSensor(SensorEntity, CoordinatorEntity):
    def __init__(self, coordinator, service_id, service_name, incidents):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._service_id = service_id
        self._incidents = incidents
        self._attr_name = f"PagerDuty - {service_name}"
        self._attr_unique_id = f"pagerduty_{service_id}"

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

    def update(self):
        """Update the sensor."""
        _LOGGER.debug(f"Updating PagerDuty incident sensor: {self._attr_name}")
        # The update is handled by the CoordinatorEntity
        pass
