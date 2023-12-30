import logging
from homeassistant.util import dt as dt_util
from datetime import datetime, timedelta
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)


class PagerDutyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching PagerDuty data."""

    def __init__(self, hass, session, update_interval, ignored_team_ids):
        """Initialize."""
        self.session = session
        self.ignored_team_ids = ignored_team_ids
        _LOGGER.debug(f"Ignored teams: {ignored_team_ids}")

        super().__init__(
            hass, _LOGGER, name="PagerDuty", update_interval=update_interval
        )

    async def async_first_config_entry(self):
        """Custom method to handle the first update of the config entry."""
        try:
            await self.async_refresh()
        except UpdateFailed:
            _LOGGER.warning(
                "Initial data update failed, will retry in background"
            )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            user = await self.hass.async_add_executor_job(self.fetch_user)
            _LOGGER.debug(f"Fetched user: {user}")

            user_id = user.get("id")
            _LOGGER.debug(f"User ID: {user_id}")

            on_calls = await self.hass.async_add_executor_job(
                self.fetch_on_calls, user_id
            )
            _LOGGER.debug(f"Fetched on calls: {on_calls}")

            self.teams = {
                team["id"]: team["name"] for team in user.get("teams", [])
            }

            team_ids = list(self.teams.keys())
            services = await self.hass.async_add_executor_job(
                self.fetch_services, team_ids
            )
            _LOGGER.debug(f"Existing services. Sample {services[:2]}")

            cleaned_ignored_team_ids = [
                team_id.strip() for team_id in self.ignored_team_ids.split(",")
            ]
            if cleaned_ignored_team_ids:
                filtered_services = [
                    service
                    for service in services
                    if not any(
                        team["id"] in cleaned_ignored_team_ids
                        for team in service.get("teams", [])
                    )
                ]
            else:
                filtered_services = services
            _LOGGER.debug(f"Filtered services: {filtered_services[:2]}")

            service_ids = [service["id"] for service in filtered_services]
            _LOGGER.debug(f"Service IDs: {service_ids}")

            incidents = await self.hass.async_add_executor_job(
                self.fetch_incidents, service_ids
            )
            _LOGGER.debug(f"Fetched incidents. Sample: {incidents[:2]}")

            return {
                "on_calls": on_calls,
                "services": services,
                "incidents": incidents,
                "user_id": user_id,
            }
        except Exception as e:
            _LOGGER.error(f"Error communicating with PagerDuty API: {e}")
            raise UpdateFailed(f"Error communicating with API: {e}")

    def fetch_user(self):
        """Fetch user data."""
        return self.session.rget("/users/me", params={"include[]": "teams"})

    def fetch_on_calls(self, user_id):
        """Fetch on-call data for the user."""
        _LOGGER.debug(f"Fetching on-call data for user_id: {user_id}")
        if not user_id:
            return []

        now = dt_util.now()

        until_date = now + timedelta(days=30)

        params = {
            "user_ids[]": user_id,
            "time_zone": str(now.tzinfo),
        }
        on_calls = self.session.rget("/oncalls", params=params)

        _LOGGER.debug(f"On-call data: {on_calls}")

        return on_calls

    def fetch_on_call_schedules(self, user_id, time_zone):
        """Fetch on-call schedules based on user_id from PagerDuty."""
        _LOGGER.debug(f"Fetching on-call schedules for user_id: {user_id}")

        if not user_id:
            return []

        now = dt_util.now()
        until_date = now + timedelta(days=30)

        on_call_params = {
            "user_ids[]": user_id,
            "time_zone": str(now.tzinfo),
            "until": until_date.strftime("%Y-%m-%d"),
        }
        response = self.session.rget("/oncalls", params=on_call_params)

        on_calls_data = response if response else []

        unique_schedule_ids = set()
        for on_call in on_calls_data:
            schedule_id = on_call.get("schedule", {}).get("id")
            if schedule_id:
                unique_schedule_ids.add(schedule_id)

        _LOGGER.debug(f"Unique schedule IDs: {unique_schedule_ids}")

        schedules = []
        schedule_params = {
            "time_zone": time_zone,
            "since": now.strftime("%Y-%m-%d"),
            "until": until_date.strftime("%Y-%m-%d"),
        }
        for schedule_id in unique_schedule_ids:
            schedule_url = f"/schedules/{schedule_id}"
            schedule_data = self.session.rget(
                schedule_url, params=schedule_params
            )
            if schedule_data:
                schedules.append(schedule_data)
                _LOGGER.debug(
                    f"Fetched schedule for schedule_id {schedule_id}: {schedule_data}"
                )

        return schedules

    def fetch_services(self, team_ids):
        """Fetch services for given team IDs."""
        all_services = []
        if team_ids:
            for team_id in team_ids:
                services = self.session.list_all(
                    "services", params={"team_ids[]": team_id}
                )
                for service in services:
                    service["team_name"] = self.teams.get(team_id, "Unknown")
                all_services.extend(services)
        else:
            all_services = self.session.list_all("services")
        return all_services

    def fetch_incidents(self, service_ids):
        """Fetch incidents for given service IDs."""
        all_incidents = []
        for service_id in service_ids:
            incidents = self.session.list_all(
                "incidents",
                params={
                    "service_ids[]": service_id,
                    "statuses[]": ["acknowledged", "triggered"],
                    "include[]": "users",
                },
            )
            all_incidents.extend(incidents)
        return all_incidents
