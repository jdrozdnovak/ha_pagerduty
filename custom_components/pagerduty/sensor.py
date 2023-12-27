"""PagerDuty Service Incident Sensor for Home Assistant."""

import logging
from collections import defaultdict
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the PagerDuty sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    sensors = []

    _LOGGER.debug("Setting up PagerDuty incident sensors")

    services_data = coordinator.data["services"]

    for service in services_data:
        service_id = service["id"]
        service_name = service["summary"]
        team_name = service.get("team_name", "Unknown")
        team_id = service.get("team_id", "Unknown")
        sensor_name = f"PD-{team_name}-{service_name}"
        sensor = PagerDutyIncidentSensor(coordinator, service_id, sensor_name, team_id)
        sensors.append(sensor)

    total_incidents_sensor = PagerDutyTotalIncidentsSensor(coordinator)
    sensors.append(total_incidents_sensor)

    async_add_entities(sensors, True)


class PagerDutyIncidentSensor(SensorEntity, CoordinatorEntity):
    def __init__(self, coordinator, service_id, sensor_name, team_id):
        super().__init__(coordinator)
        _LOGGER.debug("Initializing PagerDutyIncidentSensor: %s", sensor_name)
        self._service_id = service_id
        self._attr_name = sensor_name
        self._incidents_count = None
        self._attr_unique_id = f"pagerduty_{team_id}{service_id}"
        self._urgency_counts = defaultdict(int)
        self._status_counts = defaultdict(int)

    @property
    def native_value(self):
        return self._incidents_count

    @property
    def native_unit_of_measurement(self):
        return "incidents"

    @property
    def state_class(self):
        return "measurement"

    @property
    def extra_state_attributes(self):
        return {
            "urgency_low": self._urgency_counts["low"],
            "urgency_high": self._urgency_counts["high"],
            "status_triggered": self._status_counts["triggered"],
            "status_acknowledged": self._status_counts["acknowledged"],
        }

    def _handle_coordinator_update(self):
        _LOGGER.debug("Updating PagerDutyIncidentSensor: %s", self._attr_name)
        incidents_data = self.coordinator.data.get("incidents", [])
        self._incidents_count = sum(
            1 for inc in incidents_data if inc["service"]["id"] == self._service_id
        )
        self._urgency_counts = defaultdict(int)
        self._status_counts = defaultdict(int)
        for incident in incidents_data:
            if incident["service"]["id"] == self._service_id:
                urgency = incident.get("urgency", "unknown")
                status = incident.get("status", "unknown")
                self._urgency_counts[urgency] += 1
                self._status_counts[status] += 1
        _LOGGER.debug("PagerDutyIncidentSensor updated: %s", self._attr_name)
        super()._handle_coordinator_update()


class PagerDutyTotalIncidentsSensor(SensorEntity, CoordinatorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        _LOGGER.debug("Initializing PagerDutyTotalIncidentsSensor")
        self._attr_name = "PagerDuty Total Incidents"
        self._attr_unique_id = "pagerduty_total_incidents"
        self._total_incidents = None
        self._urgency_counts = defaultdict(int)
        self._status_counts = defaultdict(int)

    @property
    def native_value(self):
        return self._total_incidents

    @property
    def native_unit_of_measurement(self):
        return "incidents"

    @property
    def state_class(self):
        return "measurement"

    @property
    def extra_state_attributes(self):
        return {
            "urgency_low": self._urgency_counts["low"],
            "urgency_high": self._urgency_counts["high"],
            "status_triggered": self._status_counts["triggered"],
            "status_acknowledged": self._status_counts["acknowledged"],
        }

    def _handle_coordinator_update(self):
        _LOGGER.debug("Updating PagerDutyTotalIncidentsSensor")
        self._total_incidents = len(self.coordinator.data.get("incidents", []))
        self._urgency_counts = defaultdict(int)
        self._status_counts = defaultdict(int)
        for incident in self.coordinator.data.get("incidents", []):
            urgency = incident.get("urgency", "unknown")
            status = incident.get("status", "unknown")
            self._urgency_counts[urgency] += 1
            self._status_counts[status] += 1
        _LOGGER.debug("PagerDutyTotalIncidentsSensor updated")
        super()._handle_coordinator_update()
