from dataclasses import dataclass

from .light import SavantLight


@dataclass
class SavantState:
    state: str
    value: str

    def light_brightness(self) -> int:
        return int(self.value.split(',')[0])


class SavantLightRegistry:
    lights: dict[str, SavantLight] = dict()
    states: dict[str, SavantState] = dict()

    def light_brightness(self, addr):
        return self.states[self.lights[addr].module_state_name()].light_brightness()

    def light_on(self, addr):
        return self.states[self.lights[addr].module_state_name()].light_brightness() != 0
