import asyncio
import json
import logging
import os
import websockets

from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from src.prints.initial_status import print_initial_status
from src.prints.receipt import print_receipt
from src.utils.env_reader import Env, build_ws_url

class WebSocketListener:
    _initial_start = True
    _boot_marker_path = "/run/printservice-booted"

    def __init__(self, env: Env) -> None:
        self._env = env
        self.url = build_ws_url(env)
        self.token = env.device_token

        self.reconnect_delay = env.websocket_reconnect_time
        self.init_timeout = 10

        self._running = False
        self._connection_opened = False
        self._debug = env.websocket_client_debug
        self._print_initial_on_first_boot = self._is_first_boot_start()

        if not self.token:
            print("[ WARNING ] DEVICE_TOKEN is not set – connecting without auth token.")

    def _is_first_boot_start(self) -> bool:
        if os.path.exists(self._boot_marker_path):
            return False

        try:
            with open(self._boot_marker_path, "w", encoding="utf-8") as marker:
                marker.write("booted\n")
        except Exception as exc:
            print(f"[ WARNING ] Could not create boot marker {self._boot_marker_path}: {exc}")
            return False

        return True

    def start(self) -> None:
        self._running = True
        try:
            asyncio.run(self._run())
        except KeyboardInterrupt:
            print("[ INFO ] WebSocket listener interrupted by user.")
            self._running = False

    def stop(self) -> None:
        print("[ INFO ] Stopping WebSocket listener …")
        self._running = False

    async def _run(self) -> None:
        first_attempt = True

        while self._running:
            success = await self._connect_once()

            if first_attempt:
                first_attempt = False
                status_message = "connected" if success else "not connected"
                print(f"[STATUS] Initial WebSocket-Status: {status_message}")

            if not self._running:
                break

            if not success:
                print(f"[ INFO ] Connection failed. Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
                continue

            if not self._running:
                break

            print(f"[ INFO ] Connection lost. Reconnecting in {self.reconnect_delay}s...")
            await asyncio.sleep(self.reconnect_delay)

        print("[ INFO ] WebSocket listener stopped.")

    async def _connect_once(self) -> bool:
        self._connection_opened = False

        headers: list[tuple[str, str]] = []
        if self.token:
            headers.append(("Authorization", self.token))

        if self._debug:
            logging.getLogger("websockets").setLevel(logging.DEBUG)
            print("[ INFO ] WebSocket client debug enabled.")

        print(f"[ INFO ] Connecting to {self.url}")

        try:
            async with websockets.connect(
                self.url,
                additional_headers=headers,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
                open_timeout=self.init_timeout,
            ) as ws:
                self._connection_opened = True
                await self._on_open(ws)
                await self._listen(ws)
                return True
        except asyncio.TimeoutError:
            print(f"[ WARNING ] Connection not established within {self.init_timeout}s (timeout).")
            return False
        except (ConnectionClosedOK, ConnectionClosedError) as exc:
            print(f"[ INFO ] WebSocket closed: {exc}")
            return True
        except Exception as exc:
            print(f"[ ERROR ] WebSocket error: {exc}")
            return False

    async def _on_open(self, ws: websockets.WebSocketClientProtocol) -> None:
        await asyncio.sleep(1)  # Little pause required because websocket client is not instantly ready

        print("[ INFO ] Connection established.")
        subscribe = json.dumps({"type": "RECEIPTS"})
        await ws.send(subscribe)
        print(f"[ INFO ] Sent subscription: {subscribe}")

    async def _listen(self, ws: websockets.WebSocketClientProtocol) -> None:
        async for raw in ws:
            print(f"[ INFO ] Message received: {raw}")
            self._process_message(raw)

    def _process_message(self, raw: str) -> None:
        try:
            payload: dict = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            print(f"[ WARNING ] Received non-JSON message: {raw} ({exc})")
            return

        msg_type = payload.get("type")
        status = payload.get("statusCode")
        operation = payload.get("operation")
        data = payload.get("data")

        print(f"type={msg_type} | operation={operation} | status={status} | data={data}")

        if msg_type != "RECEIPTS":
            print("[ DEBUG ] Ignoring non-RECEIPTS message.")
            return

        if operation == "INITIAL":
            print("[ INFO ] Initial receipt stream confirmed – no action.")

            if self._initial_start and self._print_initial_on_first_boot:
                print_initial_status()
                self._initial_start = False
                self._print_initial_on_first_boot = False

            return

        if data:
            print(f"[ INFO ] Receipt event received – operation={operation} data={data}")
            try:
                print_receipt(data)
            except Exception as exc:
                print(f"[ ERROR ] Printing failed: {exc}")
            return

        print(f"[ WARNING ] Unhandled RECEIPTS message without data: {payload}")
