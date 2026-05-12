"""Config flow for Real Hygro."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_AUTOMATIC_ENABLED,
    CONF_DRY_TOLERANCE,
    CONF_HUMIDITY_SENSOR,
    CONF_MAX_HUMIDITY,
    CONF_MIN_HUMIDITY,
    CONF_MIN_RUNTIME,
    CONF_NAME,
    CONF_RISE_PERCENT,
    CONF_RISE_TIME,
    CONF_SWITCH_ENTITY,
    CONF_TARGET_HUMIDITY,
    CONF_WET_TOLERANCE,
    DEFAULT_AUTOMATIC_ENABLED,
    DEFAULT_DRY_TOLERANCE,
    DEFAULT_MAX_HUMIDITY,
    DEFAULT_MIN_HUMIDITY,
    DEFAULT_MIN_RUNTIME,
    DEFAULT_NAME,
    DEFAULT_RISE_PERCENT,
    DEFAULT_RISE_TIME,
    DEFAULT_TARGET_HUMIDITY,
    DEFAULT_WET_TOLERANCE,
    DOMAIN,
)

_DURATION_HMS = re.compile(r"^\d{2}:\d{2}:\d{2}$")
_DURATION_MS = re.compile(r"^\d{2}:\d{2}$")


def _duration_dict_hms(value: str) -> dict[str, int]:
    hours, minutes, seconds = (int(part) for part in value.split(":"))
    return {"hours": hours, "minutes": minutes, "seconds": seconds}


def _duration_dict_ms(value: str) -> dict[str, int]:
    minutes, seconds = (int(part) for part in value.split(":"))
    return {"minutes": minutes, "seconds": seconds}


def _base_schema(defaults: dict[str, Any]) -> vol.Schema:
    schema: dict[Any, Any] = {
        vol.Required(CONF_NAME, default=defaults[CONF_NAME]): selector.TextSelector(),
        vol.Required(CONF_TARGET_HUMIDITY, default=defaults[CONF_TARGET_HUMIDITY]): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=100, step=1, mode="box")
        ),
        vol.Required(CONF_DRY_TOLERANCE, default=defaults[CONF_DRY_TOLERANCE]): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=20, step=0.1, mode="box")
        ),
        vol.Required(CONF_WET_TOLERANCE, default=defaults[CONF_WET_TOLERANCE]): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=20, step=0.1, mode="box")
        ),
        vol.Required(CONF_MIN_HUMIDITY, default=defaults[CONF_MIN_HUMIDITY]): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=100, step=1, mode="box")
        ),
        vol.Required(CONF_MAX_HUMIDITY, default=defaults[CONF_MAX_HUMIDITY]): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=100, step=1, mode="box")
        ),
        vol.Required(CONF_MIN_RUNTIME, default=_duration_dict_hms(defaults[CONF_MIN_RUNTIME])): selector.DurationSelector(),
        vol.Required(CONF_AUTOMATIC_ENABLED, default=defaults[CONF_AUTOMATIC_ENABLED]): selector.BooleanSelector(),
        vol.Required(CONF_RISE_TIME, default=_duration_dict_ms(defaults[CONF_RISE_TIME])): selector.DurationSelector(),
        vol.Required(CONF_RISE_PERCENT, default=defaults[CONF_RISE_PERCENT]): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0.1, max=30, step=0.1, mode="box")
        ),
    }

    if defaults.get(CONF_HUMIDITY_SENSOR):
        schema[vol.Required(CONF_HUMIDITY_SENSOR, default=defaults[CONF_HUMIDITY_SENSOR])] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor"], multiple=False)
        )
    else:
        schema[vol.Required(CONF_HUMIDITY_SENSOR)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor"], multiple=False)
        )

    if defaults.get(CONF_SWITCH_ENTITY):
        schema[vol.Required(CONF_SWITCH_ENTITY, default=defaults[CONF_SWITCH_ENTITY])] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["switch"], multiple=False)
        )
    else:
        schema[vol.Required(CONF_SWITCH_ENTITY)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["switch"], multiple=False)
        )

    return vol.Schema(schema)


def _normalize(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    errors: dict[str, str] = {}
    normalized = dict(data)

    normalized[CONF_NAME] = str(data[CONF_NAME]).strip()
    if not normalized[CONF_NAME]:
        errors[CONF_NAME] = "name_required"

    normalized[CONF_TARGET_HUMIDITY] = int(float(data[CONF_TARGET_HUMIDITY]))
    normalized[CONF_DRY_TOLERANCE] = float(data[CONF_DRY_TOLERANCE])
    normalized[CONF_WET_TOLERANCE] = float(data[CONF_WET_TOLERANCE])
    normalized[CONF_MIN_HUMIDITY] = int(float(data[CONF_MIN_HUMIDITY]))
    normalized[CONF_MAX_HUMIDITY] = int(float(data[CONF_MAX_HUMIDITY]))
    normalized[CONF_RISE_PERCENT] = float(data[CONF_RISE_PERCENT])

    min_rt = data[CONF_MIN_RUNTIME]
    normalized[CONF_MIN_RUNTIME] = f"{min_rt.get('hours', 0):02}:{min_rt.get('minutes', 0):02}:{min_rt.get('seconds', 0):02}"
    rise_rt = data[CONF_RISE_TIME]
    normalized[CONF_RISE_TIME] = f"{rise_rt.get('minutes', 0):02}:{rise_rt.get('seconds', 0):02}"

    if not _DURATION_HMS.match(normalized[CONF_MIN_RUNTIME]):
        errors[CONF_MIN_RUNTIME] = "invalid_hms"
    if not _DURATION_MS.match(normalized[CONF_RISE_TIME]):
        errors[CONF_RISE_TIME] = "invalid_ms"

    if normalized[CONF_MIN_HUMIDITY] >= normalized[CONF_MAX_HUMIDITY]:
        errors[CONF_MIN_HUMIDITY] = "min_max_invalid"
        errors[CONF_MAX_HUMIDITY] = "min_max_invalid"

    return normalized, errors


class RealHygroConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        defaults = {
            CONF_NAME: DEFAULT_NAME,
            CONF_HUMIDITY_SENSOR: "",
            CONF_SWITCH_ENTITY: "",
            CONF_TARGET_HUMIDITY: DEFAULT_TARGET_HUMIDITY,
            CONF_DRY_TOLERANCE: DEFAULT_DRY_TOLERANCE,
            CONF_WET_TOLERANCE: DEFAULT_WET_TOLERANCE,
            CONF_MIN_HUMIDITY: DEFAULT_MIN_HUMIDITY,
            CONF_MAX_HUMIDITY: DEFAULT_MAX_HUMIDITY,
            CONF_MIN_RUNTIME: DEFAULT_MIN_RUNTIME,
            CONF_AUTOMATIC_ENABLED: DEFAULT_AUTOMATIC_ENABLED,
            CONF_RISE_TIME: DEFAULT_RISE_TIME,
            CONF_RISE_PERCENT: DEFAULT_RISE_PERCENT,
        }
        errors = {}
        if user_input is not None:
            normalized, errors = _normalize(user_input)
            if not errors:
                return self.async_create_entry(title=normalized[CONF_NAME], data=normalized)
            defaults.update(normalized)

        return self.async_show_form(step_id="user", data_schema=_base_schema(defaults), errors=errors)

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return RealHygroOptionsFlow(config_entry)


class RealHygroOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        defaults = dict(self.config_entry.data)
        errors = {}
        if user_input is not None:
            normalized, errors = _normalize(user_input)
            if not errors:
                self.hass.config_entries.async_update_entry(self.config_entry, title=normalized[CONF_NAME], data=normalized)
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                return self.async_create_entry(title="", data={})
            defaults.update(normalized)

        return self.async_show_form(step_id="init", data_schema=_base_schema(defaults), errors=errors)
