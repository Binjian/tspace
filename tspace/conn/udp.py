# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/04.conn.udp.ipynb.

# %% auto 0
__all__ = ['udp_context']

# %% ../../nbs/04.conn.udp.ipynb 2
import glob
import os
import os.path
from pathlib import Path
import numpy as np
import pandas as pd  # type: ignore
from scipy import interpolate  # type: ignore

# %% ../../nbs/04.conn.udp.ipynb 3
import contextlib
import socket
from typing import Generator, Optional

# %% ../../nbs/04.conn.udp.ipynb 5
@contextlib.contextmanager
def udp_context(
    host: str,  # host for udp socket
    port: str,  # port for udp socket
    timeout: Optional[float] = 5.0,  # timeout for udp socket
) -> Generator[socket.socket, None, None]:  # Generator for udp socket
    """UDP context manager"""

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error:
        raise Exception("Failed to create socket")
    socket.socket.settimeout(s, timeout)
    s.bind((host, int(port)))

    try:
        yield s
    except TimeoutError:
        raise TimeoutError(f"UDP Timeout error: {timeout} seconds")
    except Exception as e:
        raise e
    finally:
        s.close()
