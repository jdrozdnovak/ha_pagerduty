# PagerDuty Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

A custom component designed for [Home Assistant](https://www.home-assistant.io) to integrate with PagerDuty, providing insights and controls over incidents and on-call schedules.

## PagerDuty license requirements

At the moment, code requires advanced-permissions option, which is only available in **Business** and **Digital Operations** plans  
The plan is to add support for account-level access token later

## Features

- Monitor PagerDuty services and incidents.
- View on-call schedule of the API ovner.
- View assigned incident counts.
- Support for multiple PagerDuty teams.
- Allow notification to a service

## Install with HACS (recommended)

If you have [HACS][hacs] installed, search for the PagerDuty Integration and install it directly from HACS. HACS will manage updates, allowing you to easily keep track of the latest versions.

## Manual Installation

1. Open the directory (folder) for your HA configuration (where `configuration.yaml` is located).
2. Create a `custom_components` directory if it doesn't already exist.
3. Inside `custom_components`, create a new folder named `pagerduty`.
4. Download _all_ the files from the `custom_components/pagerduty/` directory in this repository.
5. Place the files you downloaded into the `pagerduty` directory you created.
6. Restart Home Assistant.
7. In the HA UI, go to "Configuration" -> "Integrations" click "+" and search for "PagerDuty".

## Configuration

Once installed, configure the integration with your PagerDuty API token through the Home Assistant UI.

## Use of notifications

The service ID you can get from the URL when checking the service.  
The integration will create a new integration_key in PD with Home Assistant name, no need to fiddle with integration_key

```yaml
service: notify.pagerduty
data:
    message: "Your message here"
    data:
        service_id: "specific_service_id"
```

## Contributions

Contributions to the project are welcome!

---

[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40jdrozdnovak-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jdrozdnovak/ha_pagerduty.svg?style=for-the-badge
[releases]: https://github.com/jdrozdnovak/ha_pagerduty/releases
[user_profile]: https://github.com/jdrozdnovak
[license-shield]: https://img.shields.io/github/license/jdrozdnovak/ha_pagerduty.svg?style=for-the-badge
