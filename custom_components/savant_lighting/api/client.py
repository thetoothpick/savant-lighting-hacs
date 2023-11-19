import asyncio
import logging
import sys
from asyncio import Task
from collections import defaultdict
from typing import Callable, Coroutine, Any

import aiohttp
from aiohttp import ClientWebSocketResponse, ClientSession

from . import uris, messages, util
from .light import SavantLight
from .registry import SavantLightRegistry, SavantState
from .websocket_message import WebSocketMessage

headers = {'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits'}

_LOGGER = logging.getLogger(__name__)


class SavantLightingClient:
    session: ClientSession
    ws: ClientWebSocketResponse = None
    read_message_task: Task
    hostname: str = None
    pending: list = list()
    registry: SavantLightRegistry

    def __init__(self, hostname):
        self.hostname = hostname
        self.registry = SavantLightRegistry()
        self.handler = MessageHandler(self.registry)
        self.client_state = SavantClientState()

    def start(self):
        asyncio.create_task(self.run())

    async def run(self):
        _LOGGER.info('starting savant lighting client')
        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect('ws://%s:8480/' % self.hostname, protocols=['savant_protocol'],
                                                headers=headers)
        await self.send_message(uris.SESSION_DEVICE_PRESENT, [messages.DEVICE_PRESENT])
        await self.send_message(uris.STATE_REGISTER, [messages.STATE_MODULE])
        self.read_message_task = asyncio.create_task(self.read_messages())
        self.client_state.running = True
        _LOGGER.info('started savant lighting client')

    async def read_messages(self):
        while self.is_connected():
            await self.handler.handle_message(WebSocketMessage(**await self.ws.receive_json(loads=util.loads)))

    async def load_lights(self):
        self.handler.hooks[uris.LIGHTING_DEVICE_LIST].append(self.load_light_states())
        await self.send_message(uris.LIGHTING_DEVICE_GET, [{}])

    async def send_light_state(self, addr: str, brightness: int):
        light = self.registry.lights[addr]
        await self.ws.send_json(WebSocketMessage([{"state": light.load_state_name(), "value": f"{brightness:d}%"}],
                                                 uris.STATE_SET), dumps=util.dumps)
        await self.load_light_state(addr)

    async def load_light_states(self):
        for addr in self.registry.lights:
            await self.load_light_state(addr)

    async def load_light_state(self, addr):
        self.client_state.pending_lights.append(addr)
        state_uri = uris.STATE_MODULE_GET % addr
        self.handler.hooks[state_uri].append(self.light_state_loaded(addr))
        await self.send_message(state_uri, [{}])

    async def light_state_loaded(self, addr: str):
        self.client_state.pending_lights.remove(addr)
        if len(self.client_state.pending_lights) == 0:
            self.client_state.loaded_lights = True

    def is_light_state_loaded(self, addr):
        return addr in self.registry.lights and addr not in self.client_state.pending_lights

    def is_connected(self):
        return self.ws is not None and not self.ws.closed

    async def stop(self):
        _LOGGER.info('shutting down savant lighting client')
        await self.send_message(uris.STATE_UNREGISTER, [messages.STATE_MODULE])
        self.read_message_task.cancel('shutting down')
        await self.session.close()
        
    async def send_message(self, uri, msgs):
        _LOGGER.debug('sent: uri: %s, messages: %s', uri, msgs)
        await self.ws.send_json(WebSocketMessage(msgs, uri), dumps=util.dumps)


class MessageHandler:
    registry: SavantLightRegistry
    hooks: dict[str, list[Coroutine[Any, Any, None]]] = defaultdict(list)

    def __init__(self, registry):
        self.registry = registry

    async def handle_message(self, ws_message: WebSocketMessage):
        _LOGGER.debug('received: uri: %s, messages: %s', ws_message.URI, ws_message.messages)
        match ws_message.URI:
            case uris.LIGHTING_DEVICE_LIST:
                for light in [SavantLight(msg) for msg in ws_message.messages]:
                    self.registry.lights[light.address] = light
            case uris.STATE_SET:
                for state in [SavantState(**msg) for msg in ws_message.messages]:
                    self.registry.states[state.state] = state
            case uris.STATE_UPDATE:
                for state in [SavantState(**msg) for msg in ws_message.messages]:
                    if 'module.' in state.state:
                        self.registry.states[state.state] = state
                        addr = state.state.replace('module.', '')
                        state_uri = uris.STATE_MODULE_GET % addr
                        await self.call_hooks(state_uri)

        if uris.STATE_MODULE_GET_PATTERN.match(ws_message.URI):
            for state in [SavantState(**msg) for msg in ws_message.messages]:
                self.registry.states[state.state] = state

        await self.call_hooks(ws_message.URI)

    async def call_hooks(self, uri):
        if len(self.hooks[uri]) > 0:
            for hook in self.hooks[uri]:
                await hook
            self.hooks[uri].clear()


class SavantClientState:
    loaded_lights: bool = False
    running: bool = False
    pending_lights: list[str] = list()
