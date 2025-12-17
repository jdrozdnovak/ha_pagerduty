"""Constants for the PagerDuty integration."""
DOMAIN = "ha_pagerduty"
CONF_API_KEY = "api_key"
REQUIRED_ROLES = [
    "abilities.read",
    "oncalls.read",
    "schedules.read",
    "services.read",
]
