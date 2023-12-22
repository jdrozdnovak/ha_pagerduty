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

    # Retrieve all teams and their respective incidents
    teams = coordinator.data["teams"]
    all_incidents = coordinator.data["incidents"]

    for team_id, team_name in teams.items():
        _LOGGER.debug(f"Processing team {team_name} (ID: {team_id})")
        team_incidents = all_incidents.get(team_id, [])

        # Create a dictionary to aggregate incidents by service
        incidents_by_service = defaultdict(list)
        for incident in team_incidents:
            service_id = incident["service"]["id"]
            incidents_by_service[service_id].append(incident)

        # Go through all aggregated incidents per service
        for service_id, incidents in incidents_by_service.items():
            service_name = (
                incidents[0]["service"]["summary"] if incidents else "Unknown Service"
            )
            sensor = PagerDutyIncidentSensor(
                coordinator, team_id, team_name, service_id, service_name, incidents
            )
            sensors.append(sensor)
            _LOGGER.debug(
                f"Created sensor for service {service_id} in team {team_id} with {len(incidents)} incidents"
            )

    add_entities(sensors, True)


class PagerDutyIncidentSensor(SensorEntity, CoordinatorEntity):
    """Representation of a PagerDuty Incident Sensor."""

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
            urgency_counts[incident["urgency"]] += 1
            status_counts[incident["status"]] += 1

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
