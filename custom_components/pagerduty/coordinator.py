import logging
from homeassistant.util import dt as dt_util
from datetime import timedelta
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)


class PagerDutyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching PagerDuty data."""

    def __init__(self, hass, session, ignored_team_ids):
        """Initialize."""
        self.session = session
        self.ignored_team_ids = ignored_team_ids
        _LOGGER.debug(f"Ignored teams: {ignored_team_ids}")

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL
        )

    async def async_first_config_entry(self):
        """Handle the first update of the config entry."""
        try:
            await self.async_refresh()
        except UpdateFailed:
            _LOGGER.warning(
                "Initial data update failed, will retry in background"
            )

    async def _async_update_data(self):
        """Fetch data from the PagerDuty API."""
        try:
            user = await self.hass.async_add_executor_job(self.fetch_user)
            _LOGGER.debug(f"Fetched user: {user}")

            user_id = user.get("id")
            _LOGGER.debug(f"User ID: {user_id}")

            self.teams = {
                team["id"]: team["name"] for team in user.get("teams", [])
            }

            team_ids = list(self.teams.keys())

            cleaned_ignored_team_ids = list(
                set(team_ids) - set(self.ignored_team_ids)
            )
            services = await self.hass.async_add_executor_job(
                self.fetch_services, cleaned_ignored_team_ids
            )
            _LOGGER.debug(f"Filtered services: {services[:2]}")

            service_ids = [service["id"] for service in services]
            _LOGGER.debug(f"Service IDs: {service_ids}")

            incidents = await self.hass.async_add_executor_job(
                self.fetch_incidents, service_ids
            )
            _LOGGER.debug(f"Fetched incidents. Sample: {incidents[:2]}")

            on_call_schedules = await self.hass.async_add_executor_job(
                self.fetch_on_call_schedules,
                user_id,
                str(dt_util.DEFAULT_TIME_ZONE),
            )

            return {
                "user_id": user_id,
                "services": services,
                "incidents": incidents,
                "on_call_schedules": on_call_schedules,
            }
        except Exception as e:
            _LOGGER.error(f"Error communicating with PagerDuty API: {e}")
            raise UpdateFailed(f"Error communicating with API: {e}")

    def fetch_user(self):
        """Fetch user data."""
        return self.session.rget("/users/me", params={"include[]": "teams"})

    def fetch_on_call_schedules(self, user_id, time_zone):
        """Fetch on-call schedules based on user_id from PagerDuty."""
        _LOGGER.debug(f"Fetching on-call schedules for user_id: {user_id}")

        if not user_id:
            return []

        now = dt_util.now()
        until_date = now + timedelta(days=14)

        on_call_params = {
            "user_ids[]": user_id,
            "time_zone": str(now.tzinfo),
            "until": until_date.strftime("%Y-%m-%d"),
        }
        response = self.session.rget("/oncalls", params=on_call_params)

        on_calls_data = response if response else []

        unique_schedule_ids = set()
        for on_call in on_calls_data:
            _LOGGER.debug(f"On Calls: {on_call}")
            schedule = on_call.get("schedule")
            if schedule is not None:
                schedule_id = schedule.get("id")
                if schedule_id:
                    unique_schedule_ids.add(schedule_id)
            else:
                _LOGGER.debug("Schedule is None")

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
        if team_ids:
            all_services = self.session.list_all(
                "services",
                params={"team_ids[]": team_ids, "include[]": "teams"},
            )
            for service in all_services:
                first_team = service["teams"][0]
                service["team_name"] = first_team.get("name", "Unknown")
                service["team_id"] = first_team.get("id", "Unknown")
        else:
            all_services = self.session.list_all("services")

        return all_services

    def fetch_incidents(self, service_ids):
        """Fetch incidents for given service IDs."""
        all_incidents = []
        all_incidents = self.session.list_all(
            "incidents",
            params={
                "service_ids[]": service_ids,
                "statuses[]": ["acknowledged", "triggered"],
                "include[]": "users",
            },
        )
        return all_incidents
