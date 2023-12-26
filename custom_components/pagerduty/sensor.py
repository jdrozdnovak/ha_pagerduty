"""PagerDuty Service Incident Sensor for Home Assistant."""

import logging
from collections import defaultdict
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity
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


class PagerDutyIncidentSensor(SensorEntity, CoordinatorEntity, RestoreEntity):
    def __init__(self, coordinator, service_id, sensor_name, team_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._service_id = service_id
        self._attr_name = sensor_name
        self._attr_unique_id = f"pagerduty_{team_id}{service_id}"
        self._incidents = None

        _LOGGER.debug(f"Initializing PagerDuty incident sensor: {self._attr_name}")

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        last_state = await self.async_get_last_state()
        if last_state:
            self._incidents_count = int(last_state.state)

        return self._incidents_count if self._incidents_count is not None else None

    @property
    def native_value(self):
        """Return the state of the sensor (total count of incidents)."""
        return len(self.coordinator.data.get("incidents", []))

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
        """Fetch new state data for the sensor asynchronously."""
        _LOGGER.debug(f"Updating PagerDuty incident sensor: {self._attr_name}")

        self._incidents = [
            inc
            for inc in self.coordinator.data.get("incidents", [])
            if inc["service"]["id"] == self._service_id
        ]

        _LOGGER.debug(
            f"Updated incidents count for {self._attr_name}: {len(self._incidents)}"
        )

        super()._handle_coordinator_update()


class PagerDutyTotalIncidentsSensor(SensorEntity, CoordinatorEntity, RestoreEntity):
    """Define a sensor for the total number of PagerDuty incidents."""

    def __init__(self, coordinator):
        """Initialize the total incidents sensor."""
        super().__init__(coordinator)
        self._attr_name = "PagerDuty Total Incidents"
        self._attr_unique_id = "pagerduty_total_incidents"
        self._total_incidents = None

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        last_state = await self.async_get_last_state()
        if last_state:
            self._total_incidents = int(last_state.state)

        # Inside the native_value property
        return self._total_incidents if self._total_incidents is not None else None

    @property
    def native_value(self):
        """Return the state of the sensor (total number of incidents)."""
        return self._total_incidents

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "incidents"

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        urgency_counts = defaultdict(int)
        status_counts = defaultdict(int)
        for incident in self.coordinator.data.get("incidents", []):
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
        _LOGGER.debug("Updating PagerDuty total incidents sensor")

        self._total_incidents = len(self.coordinator.data.get("incidents", []))

        _LOGGER.debug(f"Total incidents count updated: {self._total_incidents}")

        super()._handle_coordinator_update()
