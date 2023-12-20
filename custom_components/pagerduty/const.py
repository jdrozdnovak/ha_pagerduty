# Domain identifier for the integration
DOMAIN = "pagerduty"

# Configuration keys
CONF_API_TOKEN = "api_token"
CONF_TEAM_ID = "team_id"

# Constants for data keys, sensor types, etc.
SENSOR_TYPE_SERVICE = "service"
SENSOR_TYPE_INCIDENT = "incident"

# Attributes for sensors
ATTR_SERVICE_NAME = "service_name"
ATTR_INCIDENT_COUNT = "incident_count"
ATTR_ACKNOWLEDGED_COUNT = "acknowledged_count"
ATTR_TRIGGERED_COUNT = "triggered_count"

# Update interval for fetching new data (in seconds)
UPDATE_INTERVAL = 60
