from functools import partial
import json

dumps = partial(json.dumps, default=lambda x: x.__dict__)
