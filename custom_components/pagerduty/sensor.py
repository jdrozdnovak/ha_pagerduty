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

    teams = coordinator.data["teams"]
    incidents_data = coordinator.data["incidents"]
    services_data = coordinator.data["services"]

    for team_id, team_name in teams.items():
        team_services = services_data.get(team_id, {})
        team_incidents = incidents_data.get(team_id, defaultdict(list))

        for service_id, service in team_services.items():
            service_name = service["summary"]
            incidents = team_incidents[service_id]
            sensor = PagerDutyIncidentSensor(
                coordinator, team_id, team_name, service_id, service_name, incidents
            )
            sensors.append(sensor)

    add_entities(sensors, True)


class PagerDutyIncidentSensor(SensorEntity, CoordinatorEntity):
    def __init__(
        self, coordinator, team_id, team_name, service_id, service_name, incidents
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._team_id = team_id
        self._service_id = service_id
        self._incidents = incidents
        self._attr_name = f"PagerDuty {team_name} - {service_name}"
        self._attr_unique_id = f"{team_id}-{service_id}"

        # Add a debug statement to log the structure of the first incident
        if incidents:
            _LOGGER.debug(f"First incident structure: {incidents[0]}")
        else:
            _LOGGER.debug("No incidents for this sensor")

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
            if isinstance(incident, dict):
                urgency_counts[incident.get("urgency", "unknown")] += 1
                status_counts[incident.get("status", "unknown")] += 1
            else:
                _LOGGER.error(f"Incorrect incident data format: {incident}")

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
