import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_API_KEY
from .const import DOMAIN, UPDATE_INTERVAL


class PagerDutyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PagerDuty integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # TODO: Validate the API key, consider making a test API call.
            # If valid, proceed to create the entry.
            return self.async_create_entry(title="PagerDuty", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PagerDutyOptionsFlowHandler(config_entry)


class PagerDutyOptionsFlowHandler(config_entries.OptionsFlow):
    """PagerDuty config flow options handler."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("update_interval", default=UPDATE_INTERVAL): int,
                }
            ),
        )
