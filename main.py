import sys
from datetime import datetime

from src.websocket_listener import WebSocketListener
from src.utils.env_reader import EnvReaderUtil

def print_banner(runtime_env: str, env: EnvReaderUtil) -> None:
    print("")
    print(f"place-an-order-printer ({env.version}v)")
    print("By Turanics")
    print(f"Copyright © {datetime.now().year}")
    print("")
    print(f"Endpoints:                  {EnvReaderUtil.build_api_url(env)}")
    print(f"WebSockets:                 {EnvReaderUtil.build_ws_url(env)}")
    print("")

    if runtime_env == "dev":
        print("[ WARNING ] Development build is currently running. ")

    print("[ LOG ] Compiled successfully! Server is running...")


def main() -> None:
    runtime_env = sys.argv[1].strip().lower()

    EnvReaderUtil.load_environment(runtime_env)
    env = EnvReaderUtil.from_env()

    print_banner(runtime_env, env)

    listener = WebSocketListener(env)
    listener.start()

if __name__ == "__main__":
    main()
