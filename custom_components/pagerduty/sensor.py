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
    user_id = coordinator.data.get("user_id", "")
    sensors = []

    _LOGGER.debug("Setting up PagerDuty incident sensors")

    services_data = coordinator.data["services"]

    for service in services_data:
        service_id = service["id"]
        service_name = service["summary"]
        team_name = service.get("team_name", None)
        team_id = service.get("team_id", None)
        if team_name:
            _LOGGER.debug("User is part of team, using team_name")
            sensor_name = f"PD-{team_name}-{service_name}"
        else:
            _LOGGER.debug("Skipping team name")
            sensor_name = f"PD-{service_name}"
        sensor = PagerDutyIncidentSensor(
            coordinator, service_id, sensor_name, team_id
        )
        sensors.append(sensor)

    total_incidents_sensor = PagerDutyTotalIncidentsSensor(
        coordinator, user_id
    )
    sensors.append(total_incidents_sensor)

    assigned_incidents_sensor = PagerDutyAssignedIncidentsSensor(
        coordinator, user_id
    )
    sensors.append(assigned_incidents_sensor)

    async_add_entities(sensors, True)


class PagerDutyIncidentSensor(SensorEntity, CoordinatorEntity):
    def __init__(self, coordinator, service_id, sensor_name, team_id):
        super().__init__(coordinator)
        _LOGGER.debug("Initializing PagerDutyIncidentSensor: %s", sensor_name)
        self._service_id = service_id
        self._attr_name = sensor_name
        self._incidents_count = None
        if team_id:
            self._attr_unique_id = f"pagerduty_{team_id}_{service_id}"
        else:
            self._attr_unique_id = f"pagerduty_{service_id}"
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
            1
            for inc in incidents_data
            if inc["service"]["id"] == self._service_id
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
    def __init__(self, coordinator, user_id):
        super().__init__(coordinator)
        _LOGGER.debug("Initializing PagerDutyTotalIncidentsSensor")
        self._attr_name = "PagerDuty Total Incidents"
        self._attr_unique_id = f"pagerduty_total_incidents{user_id}"
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


class PagerDutyAssignedIncidentsSensor(SensorEntity, CoordinatorEntity):
    def __init__(self, coordinator, user_id):
        super().__init__(coordinator)
        self._user_id = user_id
        self._attr_name = "PagerDuty Assigned Incidents"
        self._assigned_incidents_count = None
        self._attr_unique_id = f"pagerduty_assigned_{user_id}"
        self._assigned_incidents = []
        self._urgency_counts = defaultdict(int)
        self._status_counts = defaultdict(int)
        _LOGGER.debug(
            f"Initializing PagerDutyAssignedIncidentsSensor for user {user_id}"
        )

    @property
    def native_value(self):
        return self._assigned_incidents_count

    @property
    def native_unit_of_measurement(self):
        return "incidents"

    @property
    def state_class(self):
        return "measurement"

    @property
    def extra_state_attributes(self):
        return {
            "incidents": self._assigned_incidents,
            "urgency_low": self._urgency_counts["low"],
            "urgency_high": self._urgency_counts["high"],
            "status_triggered": self._status_counts["triggered"],
            "status_acknowledged": self._status_counts["acknowledged"],
        }

    def _handle_coordinator_update(self):
        assigned_incidents = [
            incident
            for incident in self.coordinator.data.get("incidents", [])
            for assignee in incident.get("assignments", [])
            if assignee.get("assignee", {}).get("id") == self._user_id
        ]
        _LOGGER.debug(
            f"Updating PagerDutyAssignedIncidentsSensor Incidents. Sample: {assigned_incidents[:2]}"
        )
        self._urgency_counts = defaultdict(int)
        self._status_counts = defaultdict(int)
        self._assigned_incidents.clear()
        for incident in assigned_incidents:
            urgency = incident.get("urgency", "unknown")
            status = incident.get("status", "unknown")
            self._urgency_counts[urgency] += 1
            self._status_counts[status] += 1
            incident_to_add = {}
            if (
                "service" in incident
                and incident["service"] is not None
                and "summary" in incident["service"]
            ):
                incident_to_add.update(
                    {"impacted_service": incident["service"]["summary"]}
                )
                _LOGGER.debug(
                    f'"impacted_service": {incident["service"]["summary"]}'
                )

            if "title" in incident:
                incident_to_add.update({"title": incident["title"]})
                _LOGGER.debug(f'"title": {incident["title"]}')

            if "description" in incident:
                incident_to_add.update(
                    {"description": incident["description"]}
                )
                _LOGGER.debug(f'"description": {incident["description"]}')

            if "status" in incident:
                incident_to_add.update({"status": incident["status"]})
                _LOGGER.debug(f'"status": {incident["status"]}')

            self._assigned_incidents.append(incident_to_add)

        self._assigned_incidents_count = len(assigned_incidents)
        _LOGGER.debug(
            f"Assigned incidents count: {self._assigned_incidents_count}"
        )
        super()._handle_coordinator_update()
