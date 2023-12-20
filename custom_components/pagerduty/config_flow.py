import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from .const import CONF_API_TOKEN, CONF_TEAM_ID
from .const import DOMAIN


class PagerDutyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    hass: HomeAssistant

    async def validate_input(self, hass, token):
        """Validate the user input allows us to connect."""
        url = "https://api.pagerduty.com/abilities"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Token token={token}",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return False
                data = await response.json()
                return "incidents*" in data and "services*" in data

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            valid = await self.validate_input(self.hass, user_input[CONF_API_TOKEN])
            if not valid:
                errors["base"] = "invalid_auth"

            if not errors:
                return self.async_create_entry(title="PagerDuty", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_TOKEN): str,
                vol.Required(CONF_TEAM_ID): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PagerDutyOptionsFlowHandler(config_entry)


class PagerDutyOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle PagerDuty options."""

    def __init__(self, config_entry):
        """Initialize PagerDuty options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the PagerDuty options."""
        # Implement options flow if needed
        return self.async_show_form(
            step_id="init"
            # Define options schema here if needed
        )
