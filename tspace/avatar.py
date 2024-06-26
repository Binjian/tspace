# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00.avatar.ipynb.

# %% auto 0
__all__ = ['repo', 'proj_root', 'parser', 'Avatar', 'main']

# %% ../nbs/00.avatar.ipynb 3
import abc
import argparse
import concurrent.futures

import logging

import os
import sys

from dataclasses import dataclass
from logging.handlers import SocketHandler
from pathlib import Path, PurePosixPath
from threading import Event
from typing import Optional, Union, cast
import matplotlib.pyplot as plt  # type: ignore
import numpy as np
import pandas as pd  # type: ignore
import tensorflow as tf
from git import Repo
from pythonjsonlogger import jsonlogger  # type: ignore
from tensorflow.summary import SummaryWriter, create_file_writer, scalar  # type: ignore
from typeguard import check_type  # type: ignore

# %% ../nbs/00.avatar.ipynb 4
from .agent.dpg import DPG
from .agent.ddpg import DDPG
from .agent.rdpg.rdpg import RDPG
from .agent.idql import IDQL
from tspace.agent.utils.hyperparams import (
    HyperParamDDPG,
    HyperParamRDPG,
    HyperParamIDQL,
)

from .config.vehicles import TruckInField, TruckInCloud
from .config.drivers import Driver
from .config.messengers import CANMessenger, TripMessenger
from tspace.config.utils import (
    str_to_can_server,
    str_to_driver,
    str_to_trip_server,
    str_to_truck,
)

from .dataflow.cloud import Cloud
from .dataflow.cruncher import Cruncher
from .dataflow.kvaser import Kvaser
from .dataflow.pipeline.queue import Pipeline
from .system.log import set_root_logger
from .system.graceful_killer import GracefulKiller

# %% ../nbs/00.avatar.ipynb 5
from .agent.dpg import DPG
from .agent.ddpg import DDPG
from .agent.rdpg.rdpg import RDPG
from .agent.idql import IDQL
from tspace.agent.utils.hyperparams import (
    HyperParamDDPG,
    HyperParamRDPG,
    HyperParamIDQL,
)

from .config.vehicles import TruckInField, TruckInCloud
from .config.drivers import Driver
from .config.messengers import CANMessenger, TripMessenger
from tspace.config.utils import (
    str_to_can_server,
    str_to_driver,
    str_to_trip_server,
    str_to_truck,
)

from .dataflow.cloud import Cloud
from .dataflow.cruncher import Cruncher
from .dataflow.kvaser import Kvaser
from .dataflow.pipeline.queue import Pipeline
from .system.log import set_root_logger
from .system.graceful_killer import GracefulKiller

# %% ../nbs/00.avatar.ipynb 6
repo = Repo(".", search_parent_directories=True)
proj_root = Path(repo.working_tree_dir)
proj_root

# %% ../nbs/00.avatar.ipynb 11
@dataclass(kw_only=True)
class Avatar(abc.ABC):
    """
    Description: Implement realtime reinforcement learning algorithm for training and inference convergence of ddpg and rdpg agent

    Args:

        _truck: TruckInField or TruckInCloud
        _driver: Driver
        _agent: DDPG or RDPG
        _can_server: CANMessenger
        _trip_server: TripMessenger
        _resume: bool
        _infer_mode: bool
        logger: logging.Logger
        dict_logger: dict
        data_root: Path
        log_root: Optional[Path]
    """

    _truck: Union[TruckInField, TruckInCloud]
    _driver: Driver
    _can_server: CANMessenger
    _trip_server: Optional[TripMessenger]
    _agent: DPG  # set by derived Avatar like AvatarDDPG
    logger: logging.Logger
    dict_logger: dict
    vehicle_interface: Union[Kvaser, Cloud] = None
    _resume: bool = True
    _infer_mode: bool = False
    cruncher: Optional[Cruncher] = None
    data_root: Path = Path(".") / "data"
    log_root: Optional[Path] = None

    def __post_init__(
        self,
    ) -> None:
        """
        Initialize logging, vehicle interface (Kvaser or Cloud), cruncher.

        Agent should have been initialized and passed in as argument.
        """
        self.repo = repo
        # assert self.repo.is_dirty() == False, "Repo is dirty, please commit first"
        short_sha = self.repo.git.rev_parse(self.repo.head.commit.hexsha, short=7)
        self.logger.info(
            f"Project root: {proj_root}, "  # type: ignore
            f"git head: {short_sha}, "
            f"author: {self.repo.head.commit.author.name}, "
            f"git message: {self.repo.head.commit.message}",
            extra=self.dict_logger,
        )

        self.logger.info(f"{{'vehicle': '{self.truck.vid}'}}", extra=self.dict_logger)
        self.logger.info(f"{{'driver': '{self.driver.pid}'}}", extra=self.dict_logger)

        self.eps = np.finfo(
            np.float32
        ).eps.item()  # smallest number such that 1.0 + eps != 1.0

        self.logger.info(
            f"{{'header': 'Num GPUs Available: {len(tf.config.list_physical_devices('GPU'))}'}}"
        )
        # gpus = tf.config.list_physical_devices(device_type="GPU")
        # tf.config.experimental.set_memory_growth(gpus[0], True)
        self.logger.info(f"Tensorflow version: {tf.__version__}")
        tf_sys_details = tf.sysconfig.get_build_info()
        self.logger.info(f"{{'header': 'Tensorflow build info: {tf_sys_details}'}}")

        tf.keras.backend.set_floatx("float32")
        self.logger.info(
            f"{{'header': 'tensorflow device lib:\n{tf.config.list_physical_devices()}'}}",
            extra=self.dict_logger,
        )
        self.logger.info(
            f"{{'header': 'Tensorflow Imported!'}}", extra=self.dict_logger
        )

        if self.can_server.protocol == "udp":
            self.vehicle_interface: Kvaser = Kvaser(  # Producer~Consumer~Filter
                truck=cast(TruckInField, self.truck),
                driver=self.driver,
                can_server=self.can_server,
                resume=self.resume,
                data_dir=self.data_root,
                logger=self.logger,
                dict_logger=self.dict_logger,
            )
        else:  # self.can_server.protocol == 'tcp'
            self.vehicle_interface: Cloud = Cloud(  # Producer~Consumer
                truck=cast(TruckInCloud, self.truck),
                driver=self.driver,
                can_server=self.can_server,
                trip_server=self.trip_server,
                resume=self.resume,
                data_dir=self.data_root,
                logger=self.logger,
                dict_logger=self.dict_logger,
            )

        self.cruncher = Cruncher(  # Consumer
            agent=self.agent,
            truck=self.truck,
            driver=self.driver,
            resume=self.resume,
            infer_mode=self.infer_mode,
            data_dir=self.data_root,
            logger=self.logger,
            dict_logger=self.dict_logger,
        )

    @property
    def agent(self) -> Optional[DPG]:
        return self._agent

    @agent.setter
    def agent(self, value: DPG) -> None:
        self._agent = value

    @property
    def truck(self) -> Union[TruckInField, TruckInCloud]:
        return self._truck

    @truck.setter
    def truck(self, value: Union[TruckInField, TruckInCloud]) -> None:
        self._truck = value

    @property
    def driver(self) -> Driver:
        return self._driver

    @driver.setter
    def driver(self, value: Driver) -> None:
        self._driver = value

    @property
    def can_server(self) -> CANMessenger:
        return self._can_server

    @can_server.setter
    def can_server(self, value: CANMessenger) -> None:
        self._can_server = value

    @property
    def trip_server(self) -> TripMessenger:
        return self._trip_server

    @trip_server.setter
    def trip_server(self, value: TripMessenger) -> None:
        self._trip_server = value

    @property
    def resume(self) -> bool:
        return self._resume

    @resume.setter
    def resume(self, value: bool) -> None:
        self._resume = value

    @property
    def infer_mode(self) -> bool:
        return self._infer_mode

    @infer_mode.setter
    def infer_mode(self, value: bool) -> None:
        self._infer_mode = value

# %% ../nbs/00.avatar.ipynb 13
parser = argparse.ArgumentParser(
    "Use RL agent (DDPG, RDPG or IDQL) with tensorflow/JAX backend for EOS with coast-down activated "
    "and expected velocity in 3 seconds"
)

# %% ../nbs/00.avatar.ipynb 14
parser.add_argument(
    "-v",
    "--vehicle",
    type=str,
    default="VB7_FIELD",
    help="vehicle ID like 'VB7' or 'MP3' or VIN 'HMZABAAH1MF011055'",
)

# %% ../nbs/00.avatar.ipynb 15
parser.add_argument(
    "-d",
    "--driver",
    type=str,
    default="wang-kai",
    help="driver ID like 'longfei.zheng' or 'jiangbo.wei'",
)

# %% ../nbs/00.avatar.ipynb 16
parser.add_argument(
    "-i",
    "--interface",
    type=str,
    default="can_udp_svc",
    help="url for remote can server, e.g. ",
)

# %% ../nbs/00.avatar.ipynb 17
parser.add_argument(
    "-t",
    "--trip",
    type=str,
    default="local_udp",
    help="trip messenger, url or name, e.g. rocket_cloud, local_udp",
)

# %% ../nbs/00.avatar.ipynb 19
parser.add_argument(
    "-c",
    "--control",
    type=str,
    default="UDP",
    help="HMI Control Interface: "
    "'RMQ' for mobile phone (using rocketmq for training/assessment); "
    "'UDP' for local hmi (using loopback tcp for training/assessment); "
    "'DUMMY' for non-interaction for inference only and testing purpose",
)

# %% ../nbs/00.avatar.ipynb 20
parser.add_argument(
    "-a",
    "--agent",
    type=str,
    default="ddpg",
    help="RL agent choice: 'ddpg' for DDPG; 'rdpg' for Recurrent DPG; 'idql' for IDQL",
)

# %% ../nbs/00.avatar.ipynb 21
parser.add_argument(
    "-r",
    "--resume",
    default=False,
    help="resume the last training with restored model, checkpoint and pedal map",
    action="store_true",
)

# %% ../nbs/00.avatar.ipynb 22
parser.add_argument(
    "-l",
    "--learning",
    default=True,
    help="True for learning , with model update and training. False for inference only",
    action="store_true",
)

# %% ../nbs/00.avatar.ipynb 23
parser.add_argument(
    "-p",
    "--path",
    type=str,
    default=".",
    help="relative path to be saved, for create sub-folder for different drivers",
)

# %% ../nbs/00.avatar.ipynb 24
parser.add_argument(
    "-o",
    "--output",
    type=str,
    default="mongo_local",
    help="pool selection for data storage, "
    "url for mongodb server in format usr:password@host:port, e.g. admint:y02ydhVqDj3QFjT@10.10.0.4:23000, "
    "or simply name with synced default config, e.g. mongo_cluster, mongo_local; "
    "if specified as path name, use dask local under proj_root/data folder or cluster",
)

# %% ../nbs/00.avatar.ipynb 25
parser.add_argument(
    "--watchdog_nap_time",
    type=str,
    default="600",  # Default is  10 minutes
    help="nap time for watchdog, "
    "An internal watch dog will count the failures of input frame capturing,"
    "if capture OR flash fails for the given times within the given nap time,"
    "default is 10 minutes or 600 seconds,"
    "system will exit",
)

# %% ../nbs/00.avatar.ipynb 26
parser.add_argument(
    "--watchdog_capture_error_upper_bound",
    type=str,
    default="30",
    help="Upper bound times for capture error, "
    "An internal watch dog will count the failures of input frame capturing,"
    "if capture fails for the given times,"
    "system will exit",
)

# %% ../nbs/00.avatar.ipynb 27
parser.add_argument(
    "--watchdog_flash_error_upper_bound",
    type=str,
    default="30",
    help="Upper bound times for flashing error, "
    "An internal watch dog will count the failures of flashing,"
    "if flash fails for the given times,"
    "system will exit",
)

# %% ../nbs/00.avatar.ipynb 29
def main(args: argparse.Namespace) -> None:
    """
    Description: main function to start the Avatar.

    Initialize the Avatar with truck, driver, can server, trip server, and agent for input arguments.
    Create the first tier of the cascaded threading pools for vehicle interface and crucher.

    """
    # set up logging
    # set up data folder (logging, checkpoint, table)

    # set up data folder (logging, checkpoint, table)
    try:
        truck: Union[TruckInField, TruckInCloud] = str_to_truck(args.vehicle)
    except KeyError:
        raise KeyError(f"vehicle {args.vehicle} not found in config file")
    else:
        print(f"Vehicle found. vid:{truck.vid}, vin: {truck.vin}.")

    try:
        driver: Driver = str_to_driver(args.driver)
    except KeyError:
        raise KeyError(f"driver {args.driver} not found in config file")
    else:
        print(f"Driver found. pid:{driver.pid}, name: {driver.name}.")

    # remotecan_srv: str = 'can_intra'
    try:
        can_server = str_to_can_server(args.interface)
    except KeyError:
        raise KeyError(f"can server {args.interface} not found in config file")
    else:
        print(f"CAN Server found: {can_server.server_name}")

    try:
        trip_server = str_to_trip_server(args.trip)
    except KeyError:
        raise KeyError(f"trip server {args.web} not found in config file")
    else:
        print(f"Trip Server found: {trip_server.server_name}")

    assert args.agent in [
        "ddpg",
        "rdpg",
        "idql",
    ], "agent must be either ddpg, rdpg or idql"

    if args.resume:
        data_root = proj_root.joinpath("data/" + truck.vin + "-" + driver.pid).joinpath(
            args.path
        )
    else:  # from scratch
        data_root = proj_root.joinpath(
            "data/scratch/" + truck.vin + "-" + driver.pid
        ).joinpath(args.path)

    logger, dict_logger = set_root_logger(
        name="eos",
        data_root=data_root,
        agent=args.agent,
        tz=truck.site.tz,
        truck=truck.vid,
        driver=driver.pid,
    )
    logger.info(f"{{'header': 'Start Logging'}}", extra=dict_logger)

    if args.agent == "ddpg":
        agent: DDPG = DDPG(
            _coll_type="RECORD",
            _hyper_param=HyperParamDDPG(),
            _truck=truck,
            _driver=driver,
            _pool_key=args.output,
            _data_folder=str(data_root),
            _infer_mode=(not args.learning),
            _resume=args.resume,
            logger=logger,
            dict_logger=dict_logger,
        )
    elif args.agent == "rdpg":
        agent: RDPG = RDPG(  # type: ignore
            _coll_type="EPISODE",
            _hyper_param=HyperParamRDPG(),
            _truck=truck,
            _driver=driver,
            _pool_key=args.output,
            _data_folder=str(data_root),
            _infer_mode=(not args.learning),
            _resume=args.resume,
            logger=logger,
            dict_logger=dict_logger,
        )
    else:  # args.agent == 'idql'
        agent: IDQL = IDQL(  # type: ignore
            _coll_type="EPISODE",
            _hyper_param=HyperParamIDQL(),
            _truck=truck,
            _driver=driver,
            _pool_key=args.output,
            _data_folder=str(data_root),
            _infer_mode=(not args.learning),
            _resume=args.resume,
            logger=logger,
            dict_logger=dict_logger,
        )

    try:
        avatar = Avatar(
            _truck=truck,
            _driver=driver,
            _agent=agent,
            _can_server=can_server,
            _trip_server=trip_server,
            logger=logger,
            dict_logger=dict_logger,
            _resume=args.resume,
            _infer_mode=(not args.learning),
            data_root=data_root,
        )
    except TypeError as e:
        logger.error(
            f"{{'header': 'Project Exception TypeError', " f"'exception': '{e}'}}",
            extra=dict_logger,
        )
        sys.exit(1)
    except Exception as e:
        logger.error(
            f"{{'header': 'main Exception', " f"'exception': '{e}'}}",
            extra=dict_logger,
        )
        sys.exit(1)

    # initialize dataflow: pipelines, sync events among the threads
    observe_pipeline = Pipeline[pd.DataFrame](
        maxsize=3
    )  # pipeline for observations (type dataframe)
    flash_pipeline = Pipeline[pd.DataFrame](
        maxsize=3
    )  # pipeline for flashing torque tables (type dataframe)
    start_event = Event()
    stop_event = Event()
    interrupt_event = Event()
    exit_event = Event()
    flash_event = Event()

    logger.info(f"{{'header': 'main Thread Pool starts!'}}", extra=dict_logger)

    # Gracefulkiller instance can be created only in the main thread!
    killer = GracefulKiller(exit_event)
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=2, thread_name_prefix="Avatar"
    ) as executor:
        executor.submit(
            avatar.vehicle_interface.ignite,  # observe thread (spawns 4 threads for input, HMI and output)
            observe_pipeline,  # input port; output
            flash_pipeline,  # out port; input
            start_event,
            stop_event,
            interrupt_event,
            flash_event,
            exit_event,
            float(args.watchdog_nap_time),
            int(args.watchdog_capture_error_upper_bound),
            int(args.watchdog_flash_error_upper_bound),
        )

        executor.submit(
            avatar.cruncher.filter,  # data crunch thread
            observe_pipeline,  # output port; input
            flash_pipeline,  # input port; output
            start_event,
            stop_event,
            interrupt_event,
            flash_event,
            exit_event,
        )

    logger.info(f"{{'header': 'Start main Thread Pool dies!'}}", extra=dict_logger)
    # default behavior is "observe" will start and send out all the events to orchestrate other three threads.
    logger.info("Program exit!")

# %% ../nbs/00.avatar.ipynb 34
if (
    __name__ == "__main__" and "__file__" in globals()
):  # in order to be compatible for both script and notebnook
    """
    ## Setup
    """

    args = parser.parse_args()
    main(args)
