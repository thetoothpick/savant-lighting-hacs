import re

SESSION_DEVICE_PRESENT: str = 'session/devicePresent'

LIGHTING_DEVICE_GET: str = 'lighting/config/device/get'
LIGHTING_DEVICE_LIST: str = 'lighting/config/device/list'

STATE_SET: str = 'state/set'
STATE_UPDATE: str = 'state/update'
STATE_MODULE_GET: str = 'state/module/%s/get'
STATE_LOAD_GET: str = 'state/load/%s/get'
STATE_MODULE_GET_PATTERN: re.Pattern = re.compile('state/module/\\w+/get')
