from functools import partial
import json

dumps = partial(json.dumps, default=lambda x: x.__dict__)


def loads(s: str):
    return json.loads(s.replace('"message"', '"messages"'))
