from pathlib import Path

from lod.client import LocustClient
from lod.manager import LocustBaseManager, LocustSingleNodeManager, LocustDistributedManager
from lod.proxy import get_proxy_settings_for_port


class LocustRunner:

    def __init__(self, locustfile_path: str | Path, port: int = 8089):
        self._web_port = port
        self._locustfile_path = locustfile_path
        self._distributed = False
        self._locust_manager: LocustBaseManager = LocustSingleNodeManager(
            file_name=locustfile_path, web_port=port
        )
        self._is_locust_running = False
        self._locust_client = LocustClient(
            server_port=port,
        )
        self._proxy_settings = get_proxy_settings_for_port(self._web_port)
        self._preloaded_locust_swarm = None

    def start_locust(self) -> int:
        pid = self._locust_manager.start()
        self._is_locust_running = True
        try:
            import IPython
            display_html = IPython.get_ipython().user_ns["displayHTML"]
            display_text = f'<a href="{self._proxy_settings.get_proxy_url(ensure_ends_with_slash=True)}">Click to go to Access Locust Web UI!</a>'
            display_html(display_text)
        except Exception:
            print(f"Access Locust Web UI at {self._proxy_settings.get_proxy_url(ensure_ends_with_slash=True)}")
        if self._preloaded_locust_swarm:
            print("Preloaded swarm parameters:", self._preloaded_locust_swarm)
            self.run_swarm(**self._preloaded_locust_swarm)
            self._preloaded_locust_swarm = None
        return pid

    def distributed(self, process_to_core_count_ratio: float = 2.0):
        self._distributed = True
        self._locust_manager = LocustDistributedManager(
            file_name=self._locustfile_path,
            web_port=self._web_port,
            process_to_core_count_ratio=process_to_core_count_ratio
        )
        return self

    def stop_locust(self):
        self._locust_manager.kill()
        self._is_locust_running = False

    def set_initial_swarm(self,
              host: str,
              user_count: int,
              spawn_rate: int,
              run_time: str = "5m"):
        if self._is_locust_running:
            raise Exception("Locust is already running. Please stop it before setting initial swarm parameters.")
        else:
            self._preloaded_locust_swarm = {
                'host': host,
                'user_count': user_count,
                'spawn_rate': spawn_rate,
                'run_time': run_time
            }

        return self

    def run_swarm(self,
                  host: str,
                  user_count: int,
                  spawn_rate: int,
                  run_time: str = "5m"):
        if self._is_locust_running:
            self._locust_client.swarm(
                host=host,
                user_count=user_count,
                spawn_rate=spawn_rate,
                run_time=run_time
            )
        else:
            raise Exception("Locust is not running. Please start Locust first.")

    def stop_swarm(self):
        if self._is_locust_running:
            self._locust_client.stop_swarm()
        else:
            raise Exception("Locust is not running. Please start Locust first.")