# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/01.data.core.ipynb.

# %% auto 0
__all__ = ['KvaserType', 'RCANType', 'RawType', 'ItemT', 'RE_RECIPEKEY', 'MotionPower', 'ECUMixin', 'CloudMixin',
           'StateUnitCodes', 'StateSpecs', 'StateSpecsCloud', 'StateSpecsECU', 'ActionSpecs', 'RewardSpecs',
           'ObservationMeta', 'ObservationMetaCloud', 'ObservationMetaECU', 'DataFrameDoc', 'PoolQuery',
           'get_filemeta_config', 'configparser_as_dict']

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
from tspace.data.time import (
    veos_lifetime_end_date,
    veos_lifetime_start_date,
)

# %% ../../nbs/01.data.core.ipynb 7
KvaserType: TypeAlias = dict[str, str]
RCANType: TypeAlias = dict[str, dict[str, list[Union[str, list[list[str]]]]]]
RawType: TypeAlias = Union[KvaserType, RCANType]

# %% ../../nbs/01.data.core.ipynb 8
class MotionPower(NamedTuple):
    """
    Motion power tuple for raw data captured by Kvaser

    Attributes:

        timestep: timestamp of the tuple
        velocity: velocity in m/s,
        thrust: thrust in percentage of full acc pedal,
        brake: brake in percentage of full brake pedal,
        current: current in A,
        voltage: voltage in V,

    return:

            MotionPower tuple
    """

    timestep: pd.Timestamp
    """timestamp of the tuple"""

    velocity: float
    """velocity in m/s"""

    thrust: float
    """thrust in percentage of full acc pedal"""

    brake: float
    """brake in percentage of full brake pedal"""

    current: float
    """current in A"""

    voltage: float
    """voltage in V"""

# %% ../../nbs/01.data.core.ipynb 11
class ECUMixin(BaseModel):
    """
    ECU mixin class, for inheriting by Kvaser generated observation data

    Attributes:

        ecu_observation_number: number of observations per ECU
        ecu_observation_frequency: frequency of observations per ECU
        ecu_countdown: countdown time for ECU

    return:

            ECUMixin
    """

    # optional: can be adjusted by developer
    ecu_observation_number: int = 30
    #     (KvaserMixin.kvaser_observation_number
    # )  # 30  # Kvaser number of one observation unit: 30 as count number
    ecu_observation_frequency: int = 20
    #     (KvaserMixin.kvaser_observation_frequency
    #     # 20  # Kvaser observation frequency: 20 Hz, fixed by hardware setting
    # )
    ecu_countdown: int = 3
    #     (KvaserMixin.kvaser_countdown
    #     # 3  # Kvaser countdown time: 3 seconds, optional: can be adjusted by developer
    # )

# %% ../../nbs/01.data.core.ipynb 13
class CloudMixin(BaseModel):
    """
    Cloud mixin class, for inheriting by tbox generated observation data

    Attributes:

        cloud_signal_frequency: frequency of observations of Tbox
        cloud_gear_frequency: frequency of gear signal of Tbox
        cloud_unit_duration: unit duration of Tbox in seconds
        cloud_unit_number: number of observation units of Tbox

    return:

            CloudMixin
    """

    cloud_signal_frequency: int = 50  # TboxMixin.tbox_signal_frequency  # 50  # Hz
    cloud_gear_frequency: int = 2  # TboxMixin.tbox_gear_frequency  # 2  # Hz
    cloud_unit_duration: int = 1
    #     (TboxMixin.tbox_unit_duration
    # )  # 1  # cloud unit duration in seconds
    cloud_unit_number: int = 4
    #     (TboxMixin.tbox_unit_number
    # )  # int = 4  # cloud number of units of cloud observation

# %% ../../nbs/01.data.core.ipynb 15
class StateUnitCodes(BaseModel):
    """
    Observation of the episode

    attribute:

        velocity_unit_code: unit of velocity, default "kph"
        thrust_unit_code: unit of thrust, default "pct"
        brake_unit_code: unit of brake, default "pct"
    """

    velocity_unit_code: str = "kph"  # unit of velocity, default "kph"
    thrust_unit_code: str = "pct"  # unit of thrust, default "pct"
    brake_unit_code: str = "pct"  # unit of brake, default "pct"

# %% ../../nbs/01.data.core.ipynb 16
@dataclass(kw_only=True)
class StateSpecs:
    """
    Observation of the episode

    attributes:

            state_unit_codes: StateUnitCodes
            state_number: number of states, default 3, velocity, thrust, brake
            unit_number_per_state: number of units, default 4
            unit_duration: duration of each unit, default 1 second
            frequency: frequency of each unit, default 50 Hz
    """

    state_unit_codes: StateUnitCodes = Field(default_factory=StateUnitCodes)
    state_number: int = 3  # number of states, default 3, velocity, thrust, brake
    unit_number_per_state: int = 200  # number of units, default 4
    unit_duration: float = 1.0  # duration of each unit, default 1 second
    frequency: int = 50  # frequency of each unit, default 50 Hz

# %% ../../nbs/01.data.core.ipynb 17
@dataclass
class StateSpecsCloud(StateSpecs):
    """
    StateSpecs for cloud interface

    attributes:

        cloud_interface: CloudMixin
    """

    cloud_interface: CloudMixin = Field(default_factory=CloudMixin)

    def __post_init__(self):
        self.state_number = 3
        self.unit_number_per_state = int(
            self.cloud_interface.cloud_unit_number
            * self.cloud_interface.cloud_unit_duration
            * self.cloud_interface.cloud_signal_frequency
        )  # 4*1*50 = 200
        self.unit_duration = (
            self.cloud_interface.cloud_unit_duration
            * self.cloud_interface.cloud_unit_number
        )  # 1.0 * 4 = 4.0s
        self.frequency = self.cloud_interface.cloud_signal_frequency  # 50

# %% ../../nbs/01.data.core.ipynb 18
@dataclass
class StateSpecsECU(StateSpecs):
    """
    StateSpecs for Kvaser interface


    attributes:

        ecu_interface: ECUMixin
    """

    ecu_interface: ECUMixin = Field(default_factory=ECUMixin)

    def __post_init__(self):
        self.state_number = 3
        self.unit_number_per_state = self.ecu_interface.ecu_observation_number  # 30
        self.unit_duration = (
            self.ecu_interface.ecu_observation_number
            / self.ecu_interface.ecu_observation_frequency  # 1.5s
        )
        self.frequency = self.ecu_interface.ecu_observation_frequency  # 20

# %% ../../nbs/01.data.core.ipynb 19
class ActionSpecs(BaseModel):
    """
    Action of the episode

    attributes:

        action_unit_code: unit of action, default "nm"
        action_row_number: number of rows, default 4
        action_column_number: number of columns, default 17
    """

    action_unit_code: str = "nm"  # unit of action, default "nm"
    action_row_number: int = (
        4  # trucks_by_id["default"].torque_table_row_num_flash  # 4  # number of rows, default 4
    )
    action_column_number: int = (
        17  # trucks_by_id["default"].torque_table_col_num  # 17  # number of columns, default 17 len(PEDAL_SCALE)
    )

# %% ../../nbs/01.data.core.ipynb 20
class RewardSpecs(BaseModel):
    """
    Reward of the episode

    Attributes:

        reward_unit_code: unit of reward, default "wh"
        reward_number: number of rewards, default 1, current reward, can be extended to multiple past rewards
    """

    reward_unit_code: str = "wh"  # unit of reward, default "wh"
    reward_number: int = (
        1  # number of rewards, default 1, current reward, can be extended to multiple past rewards
    )

# %% ../../nbs/01.data.core.ipynb 21
class ObservationMeta(BaseModel):
    """
    selected metadata for db document matching pandas DataFrame

    Attributes:

        state_specs: StateSpecs
        action_specs: ActionSpecs
        reward_specs: RewardSpecs
        site: EosLocation  # "at"  # observation (testing) site
    """

    state_specs: StateSpecs  # StateSpecs
    # ActionSpecs(action_unit_code="nm",
    #             action_row_number=trucks_by_id["default"].torque_table_row_num_flash,  # 4
    #             action_column_number=trucks_by_id["default"].torque_table_col_num,  # 17)
    action_specs: ActionSpecs
    reward_specs: RewardSpecs  # RewardSpecs(reward_unit_code="wh")
    site: EosLocation  # "at"  # observation (testing) site

    def get_number_of_states(self) -> int:
        """
        get number of states from StateSpecs
        """

        return self.state_specs.state_number * self.state_specs.unit_number_per_state

    def get_number_of_actions(self) -> int:
        """
        get number of actions from ActionSpecs
        """
        return (
            self.action_specs.action_row_number * self.action_specs.action_column_number
        )

    def get_number_of_states_actions(self) -> Tuple[int, int]:
        """
        get number of states and actions from Plot
        """
        return self.get_number_of_states(), self.get_number_of_actions()

    def have_same_meta(
        self, meta_to_compare: "ObservationMeta"
    ):  # another ObservationMeta object (forward declaratin)
        """
        Compare two plots, return True if they are the same, while ignoring the 'when' field
        """
        return all(
            [
                all(
                    [
                        self.state_specs.state_unit_codes
                        == meta_to_compare.state_specs.state_unit_codes,
                        self.state_specs.state_number
                        == meta_to_compare.state_specs.state_number,
                        self.state_specs.unit_number_per_state
                        == meta_to_compare.state_specs.unit_number_per_state,
                        self.state_specs.unit_duration
                        == meta_to_compare.state_specs.unit_duration,
                        self.state_specs.frequency
                        == meta_to_compare.state_specs.frequency,
                    ]
                ),
                all(
                    [
                        self.action_specs.action_row_number
                        == meta_to_compare.action_specs.action_row_number,
                        self.action_specs.action_column_number
                        == meta_to_compare.action_specs.action_column_number,
                        self.action_specs.action_unit_code
                        == meta_to_compare.action_specs.action_unit_code,
                    ]
                ),
                self.reward_specs == meta_to_compare.reward_specs,
                self.site == meta_to_compare.site,
            ]
        )
        # return all(
        #     [
        #         getattr(self, attr) == getattr(meta_to_compare, attr)
        #         for attr in list(self.__slots__)
        #     ]
        # )

    def get_torque_table_row_names(self) -> List[str]:
        """
        get torque table row names from reward_specs
        defined as [r0, r1, r2, ...]
        """
        torque_table_row_names = [
            f"r{i}" for i in range(self.action_specs.action_row_number)
        ]
        return torque_table_row_names

# %% ../../nbs/01.data.core.ipynb 27
# @dataclass(slots=True)  # use slot to save memory and fix the attributes
class ObservationMetaCloud(ObservationMeta):
    """
    selected metadata for db document matching pandas DataFrame
    """

    state_specs: StateSpecsCloud  # Field(default_factory=StateSpecs)

# %% ../../nbs/01.data.core.ipynb 28
# @dataclass(slots=True)  # use slot to save memory and fix the attributes
class ObservationMetaECU(ObservationMeta):
    """
    selected metadata for db document matching pandas DataFrame
    """

    state_specs: StateSpecsECU  # Field(default_factory=StateSpecsECU)

# %% ../../nbs/01.data.core.ipynb 29
class DataFrameDoc(TypedDict):
    """
    Record doc type of mongo pool for record

    attributes:

        timestamp: timestamp of the record
        meta: metadata of the record
        observation: observation of the record
    """

    timestamp: datetime  # only usage of Datetime type, as interface to MongoDB timestamp (BSON Date)
    meta: dict
    observation: dict
    # for RECORD seq_len = 1

# %% ../../nbs/01.data.core.ipynb 30
ItemT = TypeVar("ItemT", Dict, pd.DataFrame)

# %% ../../nbs/01.data.core.ipynb 31
class PoolQuery(BaseModel):
    """Query for Record"""

    vehicle: str  # ""
    driver: str  # ""
    episodestart_start: datetime = (
        veos_lifetime_start_date.to_pydatetime()
    )  # timezone aware
    episodestart_end: datetime = (
        veos_lifetime_end_date.to_pydatetime()
    )  # timezone aware
    timestamp_start: Optional[datetime] = None  # for episode query should be None
    timestamp_end: Optional[datetime] = None  # for episode query should be None
    seq_len_from: Optional[int] = (
        None  # default for record query, for episode query should be sequence length, default to around 200, like 160
    )
    seq_len_to: Optional[int] = (
        None  # default for record query, for episode query should be > 200, like 240
    )

# %% ../../nbs/01.data.core.ipynb 32
RE_RECIPEKEY = re.compile(r"^[A-Za-z]\w*\.ini$")

# %% ../../nbs/01.data.core.ipynb 33
def get_filemeta_config(
    data_folder: str,
    config_file: Optional[str],
    meta: Union[ObservationMetaCloud, ObservationMetaECU],
    coll_type: str,
) -> ConfigParser:
    """Get the filepool config from the specified path data_folder + '\' + config_file
        and compare the meat data with the plot info
    Returns:
        ConfigParser: filepool config
    """

    recipe_default: ConfigParser = ConfigParser()
    number_states, number_actions = meta.get_number_of_states_actions()
    recipe_default.read_dict(
        {
            "DEFAULT": {  # should go into parquet tabel meta info
                "data_folder": data_folder,  # '.',
                "recipe_file_name": "",  # 'recipe.ini',
                "coll_type": coll_type,
            },
            "array_specs": {  # should go into parquet columns meta info
                "states": str(number_states),  # 50*4*3
                "actions": str(number_actions),  # 17*4
                "rewards": "1",
                "next_states": str(number_states),  # 50*4*3
            },
        }
    )

    recipe: ConfigParser = ConfigParser()
    if config_file is None:
        recipe_default["DEFAULT"]["recipe_file_name"] = "recipe.ini"
    else:
        recipe_p = re.compile(RE_RECIPEKEY)
        assert recipe_p.match(
            config_file
        ), f"recipe file name {config_file} is not valid"
        recipe_default["DEFAULT"]["recipe_file_name"] = config_file
        data_folder_path = Path(data_folder)
        config_file_path = data_folder_path / config_file
        try:
            recipe.read_file(open(config_file_path))
            # check if the recipe is matching with the truck specs
            # assert (
            #     recipe['array_specs'] == recipe_default['array_specs']
            # ), f"ini file array_specs is not matching the realtime truck signal specs"
        except FileNotFoundError:
            recipe = recipe_default
            data_folder_path.mkdir(parents=True, exist_ok=True)
            with open(config_file_path, "w") as configfile:
                recipe.write(configfile)
        except Exception as e:
            raise Exception(f"Error reading recipe file {config_file_path}, {e}")
        recipe["DEFAULT"]["coll_type"] = coll_type

    return recipe

# %% ../../nbs/01.data.core.ipynb 34
def configparser_as_dict(config: ConfigParser):
    """
    Converts a ConfigParser object into a dictionary.

    The resulting dictionary has sections as keys which point to a dict of the
    sections options as key => value pairs.
    """
    the_dict = {}
    sections = config.sections()
    sections.append("DEFAULT")
    for section in sections:
        the_dict[section] = {}
        for key, val in config.items(section):
            the_dict[section][key] = val
    return the_dict
