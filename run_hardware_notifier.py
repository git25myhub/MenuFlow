#!/usr/bin/env python3
import os
import time
import logging

from hardware_notifier import get_hardware_notifier, cleanup_hardware_notifier


def main() -> None:
    # Ensure we do not run in simulation on Raspberry Pi
    # Respect SIMULATION_MODE env if explicitly set
    sim_env = str(os.environ.get("SIMULATION_MODE", "")).strip().lower()
    simulation_mode = sim_env in ("1", "true", "yes", "on")

    notifier = get_hardware_notifier(simulation_mode=simulation_mode)

    # Apply SERVER_URL and RESTAURANT_ID overrides from environment, if provided
    try:
        server_url_env = os.environ.get("SERVER_URL")
        if server_url_env:
            notifier.server_url = str(server_url_env).rstrip("/")
    except Exception:
        pass
    try:
        restaurant_id_env = os.environ.get("RESTAURANT_ID")
        if restaurant_id_env is not None and str(restaurant_id_env).strip() != "":
            notifier.restaurant_id = int(restaurant_id_env)
    except Exception:
        pass

    try:
        # Keep the process alive while background threads do the work
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.getLogger(__name__).error(f"run_hardware_notifier crashed: {e}")
    finally:
        cleanup_hardware_notifier()


if __name__ == "__main__":
    main()
