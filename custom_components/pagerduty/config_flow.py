import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_API_KEY
from datetime import timedelta
from .const import DOMAIN, UPDATE_INTERVAL
from pdpyras import APISession, PDClientError


class PagerDutyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PagerDuty integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            valid = await self.hass.async_add_executor_job(
                self._test_api_key, user_input[CONF_API_KEY]
            )
            if valid:
                return self.async_create_entry(
                    title="PagerDuty", data=user_input
                )
            else:
                errors["base"] = "invalid_api_key"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )

    def _test_api_key(self, api_key):
        """Test the API key is valid."""
        session = APISession(api_key)
        try:
            session.rget("abilities")
            return True
        except PDClientError:
            return False

    async def async_step_import(self, user_input=None):
        """Handle a flow initialized by import from configuration.yaml."""
        return await self.async_step_user(user_input)

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
        interval = timedelta(seconds=UPDATE_INTERVAL)
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("update_interval", default=interval): int,
                }
            ),
        )
