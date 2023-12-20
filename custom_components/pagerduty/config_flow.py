import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_NAME
from .const import DOMAIN, CONF_API_TOKEN


class PagerDutyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PagerDuty."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate user input
            # You may want to verify the API token's validity here

            return self.async_create_entry(title="PagerDuty", data=user_input)

        # Specify the data needed for setup
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_API_TOKEN): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return PagerDutyOptionsFlowHandler(config_entry)


class PagerDutyOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle PagerDuty options."""

    def __init__(self, config_entry):
        """Initialize PagerDuty options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the PagerDuty options."""
        return self.async_show_form(
            step_id="init",
            # Add additional options here if needed
        )
