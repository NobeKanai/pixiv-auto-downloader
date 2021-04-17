from pathlib import Path
from typing import Tuple
import platform
import pickle

# tmp file
tmp_path = Path("/var/cache/pad") if platform.system() != "Windows" else Path(
    ".tmp")


def load_configs() -> Tuple:
    """
    load config load config from tmp file
    we assume config is a Tuple
    """
    with open(tmp_path, 'rb') as f:
        return pickle.load(f)


def flush_configs(configs: Tuple):
    """flush config to tmp file
    we assume config is a Tuple 
    """
    with open(tmp_path, 'wb') as f:
        pickle.dump(
            configs,
            f,
            pickle.HIGHEST_PROTOCOL,
        )
