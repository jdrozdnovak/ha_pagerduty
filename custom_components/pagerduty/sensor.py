import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import STATE_UNKNOWN
from .api import PagerDutyDataCoordinator
from .const import UPDATE_INTERVAL, CONF_API_TOKEN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the PagerDuty sensor from a config entry."""
    api_token = config_entry.data.get(CONF_API_TOKEN)

    coordinator = PagerDutyDataCoordinator(hass, api_token, UPDATE_INTERVAL)
    await coordinator.async_config_entry_first_refresh()

    sensors = []
    for key, data in coordinator.data.items():
        team_name = data["team_name"]
        service_name = data["service_name"]
        sensor_name = f"{team_name} {service_name}"
        sensors.append(PagerDutyServiceSensor(coordinator, key, sensor_name))

    async_add_entities(sensors, False)


class PagerDutyServiceSensor(SensorEntity):
    def __init__(self, coordinator, unique_key, sensor_name):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.unique_key = unique_key
        self.sensor_name = sensor_name
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.sensor_name

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{self.unique_key}"

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return "measurement"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "incidents"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        service_data = self.coordinator.data.get(self.service_id)
        return service_data.get("incident_count") if service_data else STATE_UNKNOWN

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        service_data = self.coordinator.data.get(self.service_id, {})
        return {
            "acknowledged_count": service_data.get("acknowledged_count", 0),
            "triggered_count": service_data.get("triggered_count", 0),
            "high_urgency_count": service_data.get("high_urgency_count", 0),
            "low_urgency_count": service_data.get("low_urgency_count", 0),
        }
