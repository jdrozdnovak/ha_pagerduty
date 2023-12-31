import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from .const import DOMAIN
from pdpyras import APISession, PDClientError


class PagerDutyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PagerDuty integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            api_base_url = self._get_api_url(
                user_input.get("api_server", "US")
            )

            valid = await self.hass.async_add_executor_job(
                self._test_api_key, user_input[CONF_API_KEY], api_base_url
            )
            if valid:
                user_input["api_base_url"] = api_base_url
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
                    vol.Optional("ignored_team_ids", default=""): str,
                    vol.Optional("api_server", default="US"): vol.In(
                        ["US", "EU"]
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    def _get_api_url(api_server):
        """Return the API base URL based on the server choice."""
        return (
            "https://api.pagerduty.com"
            if api_server == "US"
            else "https://api.eu.pagerduty.com"
        )

    def _test_api_key(self, api_key, api_base_url):
        """Test if the API key is valid."""
        session = APISession(api_key)
        session.url = api_base_url
        try:
            session.rget("abilities")
            return True
        except PDClientError:
            return False
