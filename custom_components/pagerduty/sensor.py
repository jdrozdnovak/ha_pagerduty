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

    # Aggregate incidents by team and service
    incidents_by_team_service = defaultdict(lambda: defaultdict(list))
    for team_id, incidents in coordinator.data["incidents"].items():
        for incident in incidents:
            service_id = incident["service"]["id"]
            incidents_by_team_service[team_id][service_id].append(incident)

    # Create sensors
    for team_id, services in incidents_by_team_service.items():
        team_name = coordinator.data["teams"].get(team_id)
        for service_id, incidents in services.items():
            service_name = incidents[0]["service"]["summary"]
            sensor = PagerDutyIncidentSensor(
                coordinator, team_id, team_name, service_id, service_name, incidents
            )
            sensors.append(sensor)

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
        """Return the state of the sensor (number of triggered or acknowledged incidents)."""
        return sum(
            1
            for incident in self._incidents
            if incident["status"] in ["triggered", "acknowledged"]
        )

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        urgency_low = sum(
            1 for incident in self._incidents if incident["urgency"] == "low"
        )
        urgency_high = sum(
            1 for incident in self._incidents if incident["urgency"] == "high"
        )
        status_triggered = sum(
            1 for incident in self._incidents if incident["status"] == "triggered"
        )
        status_acknowledged = sum(
            1 for incident in self._incidents if incident["status"] == "acknowledged"
        )

        return {
            "urgency_low": urgency_low,
            "urgency_high": urgency_high,
            "status_triggered": status_triggered,
            "status_acknowledged": status_acknowledged,
        }

    def update(self):
        """Update the sensor."""
        _LOGGER.debug(f"Updating PagerDuty incident sensor: {self._attr_name}")
        # The update is handled by the CoordinatorEntity
        pass
