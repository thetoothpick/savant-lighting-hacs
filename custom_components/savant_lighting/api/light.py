# {'id': '39', 'name': 'Living Room Primary Downlights', 'room': 'Living Room', 'type': 'ECHVAP2',
# 'boardname': 'Paddle', 'uid': '80C5F2B3130F0084', 'address': '027', 'bl': 'bA', 'mode': None,
# 'rgb': '001F3F', 'ambient': 'on', 'controltype': None, 'sleduid': None, 'echoaddress': None,
# 'dimmerIsSwitch': 'false', 'powerCurve': '0', 'localMode': '0',
# 'switch': [
# {'id': '1', 'led': '4', 'rgb': '00FFFF', 'function': 'onraise', 'scene': '40', 'zone': None, 'engraving': 'Up', 'ledintensity': '40'},
# {'id': '5', 'led': '3', 'rgb': '00FFFF', 'function': 'on', 'scene': '40', 'zone': None, 'engraving': 'AUX T', 'ledintensity': '40'},
# {'id': '6', 'led': '3', 'rgb': '00FFFF', 'function': 'off', 'scene': '40', 'zone': None, 'engraving': 'AUX B', 'ledintensity': '40'},
# {'id': '7', 'led': '3', 'rgb': '00FFFF', 'function': 'offlower', 'scene': '40', 'zone': None, 'engraving': 'Down', 'ledintensity': '40'}
# ],
# 'load': [{'id': '1', 'name': 'Living Room Primary Downlights', 'room': 'Living Room', 'loadNotWired': 'false', 'min': '0', 'max': '100', 'LoadType': '0'}],
# 'shade': []}

from dataclasses import dataclass


@dataclass
class SavantSwitch:
    id: int
    led: int
    function: str
    scene: int
    zone: str

    def __init__(self, dictionary):
        self.__dict__.update(dictionary)
        self.id = int(self.id)
        self.led = int(self.led)
        self.scene = int(self.scene)


@dataclass
class SavantLoad:
    id: int
    name: str
    room: str
    min: int
    max: int

    def __init__(self, dictionary):
        self.__dict__.update(dictionary)
        self.id = int(self.id)
        self.min = int(self.min)
        self.max = int(self.max)


@dataclass
class SavantLight:
    id: int
    name: str
    room: str
    type: str
    boardname: str
    uid: str
    address: str
    mode: str
    dimmerIsSwitch: bool
    switch: list[SavantSwitch]
    load: list[SavantLoad]

    def __init__(self, dictionary):
        self.__dict__.update(dictionary)

        self.id = int(self.id)
        self.dimmerIsSwitch = bool(self.dimmerIsSwitch)
        self.switch = [SavantSwitch(d) for d in self.switch]
        self.load = [SavantLoad(d) for d in self.load]

    def load_state_name(self):
        return 'load.' + self.address.lstrip('0') + '0000'

    def module_state_name(self):
        return 'module.' + self.address
