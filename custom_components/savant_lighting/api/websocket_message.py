from dataclasses import dataclass


@dataclass
class WebSocketMessage:
    messages: list[dict]
    URI: str
