"""Humidifier platform for Real Hygro."""
from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta

from homeassistant.components.humidifier import (
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AUTOMATIC_ENABLED,
    CONF_DRY_TOLERANCE,
    CONF_HUMIDITY_SENSOR,
    CONF_MAX_HUMIDITY,
    CONF_MIN_HUMIDITY,
    CONF_MIN_RUNTIME,
    CONF_RISE_PERCENT,
    CONF_RISE_TIME,
    CONF_SWITCH_ENTITY,
    CONF_TARGET_HUMIDITY,
    CONF_WET_TOLERANCE,
    DEFAULT_NAME,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([RealHygroHumidifier(hass, entry)])


class RealHygroHumidifier(RestoreEntity, HumidifierEntity):
    _attr_should_poll = False
    _attr_name = DEFAULT_NAME
    _attr_device_class = HumidifierDeviceClass.DEHUMIDIFIER
    _attr_supported_features = HumidifierEntityFeature.TARGET_HUMIDITY

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        cfg = entry.data
        self._sensor_entity = cfg[CONF_HUMIDITY_SENSOR]
        self._switch_entity = cfg[CONF_SWITCH_ENTITY]
        self._attr_target_humidity = cfg[CONF_TARGET_HUMIDITY]
        self._dry_tolerance = cfg[CONF_DRY_TOLERANCE]
        self._wet_tolerance = cfg[CONF_WET_TOLERANCE]
        self._attr_min_humidity = cfg[CONF_MIN_HUMIDITY]
        self._attr_max_humidity = cfg[CONF_MAX_HUMIDITY]
        self._min_runtime = timedelta(
            hours=cfg[CONF_MIN_RUNTIME].get("hours", 0),
            minutes=cfg[CONF_MIN_RUNTIME].get("minutes", 0),
            seconds=cfg[CONF_MIN_RUNTIME].get("seconds", 0),
        )
        self._automatic_enabled = cfg[CONF_AUTOMATIC_ENABLED]
        self._rise_time = timedelta(
            minutes=cfg[CONF_RISE_TIME].get("minutes", 0),
            seconds=cfg[CONF_RISE_TIME].get("seconds", 0),
        )
        self._rise_percent = float(cfg[CONF_RISE_PERCENT])

        self._attr_available = True
        self._attr_is_on = False
        self._attr_current_humidity = None
        self._manual_enabled = True
        self._history: deque[tuple[datetime, float]] = deque()
        self._runtime_until: datetime | None = None
        self._unsubs = []

    async def async_added_to_hass(self) -> None:
        if (old_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = old_state.state == "on"
            target = old_state.attributes.get("humidity")
            if target is not None:
                self._attr_target_humidity = int(target)

        self._unsubs.append(async_track_state_change_event(self.hass, [self._sensor_entity], self._sensor_changed))
        self._unsubs.append(async_track_time_interval(self.hass, self._periodic_check, timedelta(seconds=30)))
        await self._update_from_sensor()

    async def async_will_remove_from_hass(self) -> None:
        for unsub in self._unsubs:
            unsub()

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_luftentfeuchter"

    async def async_set_humidity(self, humidity: int) -> None:
        self._attr_target_humidity = max(self.min_humidity, min(self.max_humidity, humidity))
        await self._control_logic(force=True)

    async def async_turn_on(self, **kwargs) -> None:
        self._manual_enabled = True
        await self._turn_switch(True)

    async def async_turn_off(self, **kwargs) -> None:
        self._manual_enabled = False
        await self._turn_switch(False)

    async def _turn_switch(self, turn_on: bool) -> None:
        service = "turn_on" if turn_on else "turn_off"
        await self.hass.services.async_call("switch", service, {ATTR_ENTITY_ID: self._switch_entity}, blocking=True)
        self._attr_is_on = turn_on
        if turn_on:
            self._runtime_until = dt_util.utcnow() + self._min_runtime
        self.async_write_ha_state()

    @callback
    def _sensor_changed(self, event) -> None:
        self.hass.async_create_task(self._update_from_sensor())

    async def _periodic_check(self, _now) -> None:
        await self._update_from_sensor()

    async def _update_from_sensor(self) -> None:
        state = self.hass.states.get(self._sensor_entity)
        if state is None or state.state in ("unknown", "unavailable"):
            self._attr_available = False
            self.async_write_ha_state()
            return

        self._attr_available = True
        current = float(state.state)
        self._attr_current_humidity = current

        now = dt_util.utcnow()
        self._history.append((now, current))
        cutoff = now - self._rise_time
        while self._history and self._history[0][0] < cutoff:
            self._history.popleft()

        await self._control_logic()

    async def _control_logic(self, force: bool = False) -> None:
        if self.current_humidity is None:
            return

        now = dt_util.utcnow()
        min_until_active = self._runtime_until is not None and now < self._runtime_until

        should_on = self._manual_enabled and self.current_humidity >= (self.target_humidity + self._wet_tolerance)
        should_off = self.current_humidity <= (self.target_humidity - self._dry_tolerance)

        if self._automatic_enabled and len(self._history) > 1:
            rise = self._history[-1][1] - self._history[0][1]
            if rise >= self._rise_percent:
                should_on = True

        if should_on and not self.is_on:
            await self._turn_switch(True)
        elif (should_off or not self._manual_enabled) and self.is_on and (force or not min_until_active):
            await self._turn_switch(False)
        else:
            self.async_write_ha_state()
