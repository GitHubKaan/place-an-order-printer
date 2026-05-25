import os
import sys
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

@dataclass
class EnvReaderUtil:
    env: str = ""
    version: str = ""

    api_version: str = ""
    api_https: bool = False
    api_www: bool = False
    api_host: str = ""
    api_port: str = ""
    api_path: str = ""

    websocket_path: str = ""
    websocket_reconnect_time: int = 10

    printer_paper_pixel_width: int = 576
    printer_paper_character_width: int = 48

    printer_disable_init: bool = False

    device_token: str = ""

    websocket_client_debug: bool = False
    image_url_api_https: bool = False
    image_url_api_host: str = ""
    image_url_api_port: str = ""

    @classmethod
    def from_env(cls) -> "EnvReaderUtil":
        return cls(
            env=os.getenv("ENV", ""),
            version=os.getenv("VERSION", ""),

            api_version=os.getenv("API_VERSION", ""),
            api_https=os.getenv("API_HTTPS", "false").lower() == "true",
            api_www=os.getenv("API_WWW", "false").lower() == "true",
            api_host=os.getenv("API_HOST", "localhost"),
            api_port=os.getenv("API_PORT", ""),
            api_path=os.getenv("API_PATH", ""),

            websocket_path=os.getenv("WEBSOCKET_PATH", "ws"),
            websocket_reconnect_time=int(os.getenv("WEBSOCKET_RECONNECT_TIME", "10")),

            printer_paper_pixel_width=int(os.getenv("PRINTER_PAPER_PIXEL_WIDTH", "576")),
            printer_paper_character_width=int(os.getenv("PRINTER_PAPER_CHARACTER_WIDTH", "48")),

            printer_disable_init=os.getenv("PRINTER_DISABLE_INIT", "false").lower() == "true",

            device_token=os.getenv("DEVICE_TOKEN", ""),

            websocket_client_debug=os.getenv("WEBSOCKET_CLIENT_DEBUG", "false").lower() == "true",
            image_url_api_https=os.getenv("IMAGE_URL_API_HTTPS", "false").lower() == "true",
            image_url_api_host=os.getenv("IMAGE_URL_API_HOST", ""),
            image_url_api_port=os.getenv("IMAGE_URL_API_PORT", ""),
        )

    def _build_backend_path(self) -> str:
        api_path = self.api_path.strip("/")
        api_version = self.api_version.strip()
        parts: list[str] = []
        if api_path:
            parts.append(api_path)
        if api_version:
            version = api_version if api_version.startswith("v") else f"v{api_version}"
            parts.append(version)
        return ("/" + "/".join(parts)) if parts else ""

    def build_api_url(self) -> str:
        scheme = "https" if self.api_https else "http"
        www_prefix = "www." if self.api_www else ""
        host = self.api_host or "localhost"
        port = f":{self.api_port}" if self.api_port else ""
        backend = self._build_backend_path()
        return f"{scheme}://{www_prefix}{host}{port}{backend}"

    def build_ws_url(self) -> str:
        scheme = "wss" if self.api_https else "ws"
        www_prefix = "www." if self.api_www else ""
        host = self.api_host or "localhost"
        port = f":{self.api_port}" if self.api_port else ""
        backend = self._build_backend_path()
        ws_path = self.websocket_path.strip("/") if self.websocket_path else "ws"
        path = f"/{ws_path}" if ws_path else ""
        return f"{scheme}://{www_prefix}{host}{port}{backend}{path}"

    @staticmethod
    def load_environment(env: str) -> None:
        env_file = Path(f".env.{env}")

        if not env_file.exists():
            print(f"[ERROR] Environment file '{env_file}' not found.")
            print("         Please create it or copy from '.env.example'.")
            sys.exit(1)

        load_dotenv(dotenv_path=env_file, override=True)
        print(f"Environment loaded: {env_file} ({env}-mode)")