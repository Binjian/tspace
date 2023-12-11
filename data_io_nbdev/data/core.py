# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/01.data.core.ipynb.

# %% auto 0
__all__ = ['KvaserType', 'RCANType', 'RawType', 'veos_lifetime_start_date', 'veos_lifetime_end_date', 'MotionPower', 'say_hi']

# %% ../../nbs/01.data.core.ipynb 3
import re
from configparser import ConfigParser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple, TypeVar, Union, TypeAlias
from zoneinfo import ZoneInfo  # type: ignore


# %% ../../nbs/01.data.core.ipynb 4
import pandas as pd  # type: ignore
from pydantic import BaseModel, Field, GetPydanticSchema  # type: ignore
from pydantic.dataclasses import dataclass  # type: ignore
from typing_extensions import TypedDict
from .location import EosLocation


# %% ../../nbs/01.data.core.ipynb 5
KvaserType: TypeAlias = dict[str, str]
RCANType: TypeAlias = dict[str, dict[str, list[Union[str, list[list[str]]]]]]
RawType: TypeAlias = Union[KvaserType, RCANType]


# %% ../../nbs/01.data.core.ipynb 6
#  Define TypedDict for type hinting of typed collections: records and episodes
veos_lifetime_start_date: pd.Timestamp = pd.Timestamp(
    ts_input="2021-01-01T00:00:00+08:00", tz="Asia/Shanghai"
)
veos_lifetime_end_date: pd.Timestamp = pd.Timestamp(
    ts_input="2031-12-31T00:00:00+08:00", tz="Asia/Shanghai"
)


# %% ../../nbs/01.data.core.ipynb 7
class MotionPower(NamedTuple):
    timestep: pd.Timestamp
    velocity: float
    thrust: float
    brake: float
    current: float
    voltage: float


# %% ../../nbs/01.data.core.ipynb 10
def say_hi(to: str):
    """Say hello to somebody"""
    return f'Hi {to}!'