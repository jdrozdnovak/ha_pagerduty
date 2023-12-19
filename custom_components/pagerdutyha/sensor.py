import requests
import logging
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME, CONF_TOKEN
from homeassistant.util import Throttle
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from datetime import timedelta

# Constants
MIN_TIME_BETWEEN_SCANS = timedelta(seconds=60)
_LOGGER = logging.getLogger(__name__)
DOMAIN = "pagerduty"
CONF_TEAM_NAME = "team_name"
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_TOKEN): cv.string,
    vol.Required(CONF_TEAM_NAME): cv.string,
})

# Fetch Services from PagerDuty with Pagination
def fetch_pagerduty_services(token, team_name):
    services = []
    url = "https://api.pagerduty.com/services"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Token token={token}"
    }
    params = {"include[]": "teams"}
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            _LOGGER.error("Error fetching services from PagerDuty: %s", response.text)
            break
        data = response.json()
        for service in data.get("services", []):
            if any(team.get("summary") == team_name for team in service.get("teams", [])):
                services.append(service)
        if not data.get("more", False):
            break
        params["offset"] = data.get("offset", 0) + data.get("limit", 25)
    return services

# Setup Platform
def setup_platform(hass, config, add_entities, discovery_info=None):
    name = config[CONF_NAME]
    token = config[CONF_TOKEN]
    team_name = config[CONF_TEAM_NAME]

    services = fetch_pagerduty_services(token, team_name)
    entities = []
    for service in services:
        entities.append(PagerDutyServiceSensor(service, name))

    add_entities(entities)

class PagerDutyServiceSensor(SensorEntity):
    def __init__(self, service, name_prefix):
        """Initialize the sensor."""
        self._service = service
        self._name_prefix = name_prefix
        self._state = None
        self._attributes = {}

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        # Use a combination of the name prefix and the service name for uniqueness
        return f"{DOMAIN}_{self._name_prefix}_{self._service['name'].replace(' ', '_')}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name_prefix} {self._service['name']}"

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:bell-ring"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._attributes

    @Throttle(MIN_TIME_BETWEEN_SCANS)
    def update(self):
        """Fetch new state data for the sensor."""
        self._fetch_incidents_for_service()

    def _fetch_incidents_for_service(self):
        """Fetch incidents for the specific service and update state and attributes."""
        url = f"https://api.pagerduty.com/incidents?service_ids[]={self._service['id']}&statuses[]=triggered&statuses[]=acknowledged"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Token token={YOUR_API_TOKEN}"  # Replace with actual token
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            _LOGGER.error("Error fetching incidents from PagerDuty: %s", response.text)
            self._state = "Error"
            return

        data = response.json()
        incidents = data.get("incidents", [])
        triggered_count = sum(1 for incident in incidents if incident["status"] == "triggered")
        acknowledged_count = sum(1 for incident in incidents if incident["status"] == "acknowledged")

        # Update state and attributes
        self._state = f"{triggered_count} Triggered, {acknowledged_count} Acknowledged"
        self._attributes = {
            "triggered_incidents": triggered_count,
            "acknowledged_incidents": acknowledged_count
        }
