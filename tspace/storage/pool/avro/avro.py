# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../../nbs/05.storage.pool.avro.avro.ipynb.

# %% ../../../../nbs/05.storage.pool.avro.avro.ipynb 3
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import dask.bag as db  # type: ignore
import fastavro
import pandas as pd  # type: ignore
from dask.bag import Bag, random
from dask.diagnostics import ProgressBar  # type: ignore

# %% auto 0
__all__ = ['AvroPool']

# %% ../../../../nbs/05.storage.pool.avro.avro.ipynb 5
from tspace.data.core import (
    ObservationMeta,
    PoolQuery,
    veos_lifetime_end_date,
    veos_lifetime_start_date,
)
from ....data.location import locations_by_abbr
from ....data.external.pandas_utils import avro_ep_decoding, avro_ep_encoding

# %% ../../../../nbs/05.storage.pool.avro.avro.ipynb 6
from ..dask import DaskPool  # type: ignore
from .schema import gen_episode_schema  # type: ignore

# %% ../../../../nbs/05.storage.pool.avro.avro.ipynb 7
@dataclass(kw_only=True)
class AvroPool(DaskPool):  # type: ignore   # pycharm bug
    """
    AvroPool is the avro storage for pooling the real-time data from the cloud.

    Features:
        - It's supposed to support large local data pool with buffer capacity
    only bounded by local system storage.

        - It uses Dask Bag to store the data in memory and Dask DataFrame to process the data.

        - Meta information is stored in avro metadata in each of avro file. Sampling

        - Random episodes needs some care to reassure the randomness. It uses Dask Delayed to parallelize the data processing like sampling

    Attributes:
        - dbg: Dask Bag of episodes
        - dbg_schema: schema for avro file decoding

    """

    dbg: Optional[db.Bag] = None  # db.from_sequence([])  # dask DataFrame
    dbg_schema: Optional[dict] = (
        None  # field(default_factory=dict)  # schema for avro file decoding
    )

    def __post_init__(self):
        """Set up logger, post init of DaskPool and load the pool."""
        self.logger = self.logger.getChild("avro pool")
        self.dict_logger = self.dict_logger
        super().__post_init__()

        self.logger.info(
            f"{{'header': 'Arrow pool stored', "
            f"'path': '{self.pl_path}', "
            f"'coll_type' : '{self.recipe['DEFAULT']['coll_type']}'}}",
            extra=self.dict_logger,
        )
        self.load()

    def load(self):
        """load EPISODE arrays from avro files in folder specified by the recipe"""

        schema = gen_episode_schema(
            self.meta
        )  # schema for avro file decoding into episode bag

        self.dbg_schema = fastavro.parse_schema(schema)
        self.logger.info(
            f"{{'header': 'Arrow pool loaded', ",
            f"'path': '{self.pl_path}'}}",
            extra=self.dict_logger,
        )
        try:
            with ProgressBar():
                self.dbg = db.read_avro(
                    str(self.pl_path / "bag_episodes.*.avro"),  # Path to str conversion
                )
                # # parquet file which is partitioned by a timestamp was converted to category,
                # # when loaded to dask dataframe
                # self.dbg["episodestart__"] = self.dbg["episodestart__"].astype(
                #     "datetime64[ns]"
                # )  # very important for indexing and slicing!!!
            self.logger.info(
                f"{{'header': 'Loading bag from avro files.',  "
                f"'path': '{self.pl_path}'}}",
                extra=self.dict_logger,
            )
        except (FileNotFoundError, ValueError) as e:
            self.logger.info(
                f'Data folder ({self.recipe["DEFAULT"]["data_folder"]}) is empty! parquet files not found: {e} ...'
            )
            self.logger.info(
                f'Create data folder ({self.recipe["DEFAULT"]["data_folder"]}) for Apache Arrow parquet files!'
            )
            self.pl_path.mkdir(parents=True, exist_ok=True)
            self.cnt = 0
            return
        except Exception as e:
            self.logger.warning(f"Loading avro error: {e}", extra=self.dict_logger)
            raise e

        # Deduplicate the bag, avro file take duplicated records.
        # Otherwise, a separate task to clean up duplications periodically is required.
        self.dbg = self.dbg.distinct(
            lambda x: (
                x["meta"]["episode_meta"]["driver"],
                x["meta"]["episode_meta"]["vehicle"],
                x["meta"]["episode_meta"]["episodestart"],
            )
        )

        # extract metadata stored in an avro record and compare with input metadata
        meta_in_an_episode = self.dbg.take(1)[0][
            "meta"
        ]  # take the first episode, take return a tuple of dicts
        episode_meta = meta_in_an_episode["episode_meta"]
        observation_meta = meta_in_an_episode["observation_meta"]
        observation_meta["site"] = locations_by_abbr[observation_meta["site"]["abbr"]]
        pool_meta = ObservationMeta(**observation_meta)
        self.logger.info(
            f"meta in avro file: {observation_meta}", extra=self.dict_logger
        )
        assert self.meta.have_same_meta(
            pool_meta
        ), f"meta information in avro file doesn't match with input meta information!"
        # TODO if different, raise warning and update meta information in parquet file

        self.cnt = self._count(self.query)

    def close(self):
        """close the pool"""
        self.logger.info(
            f"Nothing to be done for dask avro pool!",  # neither arrow parquet nor avro need cleaning up.
            extra=self.dict_logger,
        )

    def store(self, episode: pd.DataFrame) -> None:
        """Deposit an episode as a single item into avro."""

        episode_dict_nested = avro_ep_encoding(episode)
        indices_dict = [
            {episode.index.names[i]: level for i, level in enumerate(levels)}
            for levels in episode.index
        ]
        episode_meta = indices_dict[0]  # only one row in the dataframe
        try:
            episode_meta.pop("timestamp")
        except KeyError:
            raise KeyError(f"timestamp is not in index of episode dataframe!")

        episode_meta["episodestart"] = (
            episode_meta["episodestart"].timestamp() * 1e6
        )  # convert to microsecond
        # convert the dict to a dask bag file
        # observation_meta = ObservationMeta(
        #     state_specs=self.meta.state_specs,
        #     action_specs=self.meta.action_specs,
        #     reward_specs=self.meta.reward_specs,
        #     site=self.meta.site,
        # )
        records_episode_to_add = {
            "episodestart": episode_meta["episodestart"],
            "meta": {
                "episode_meta": episode_meta,
                "observation_meta": self.meta.model_dump(),
            },
            "sequence": episode_dict_nested,
        }

        dask_bag_ep = db.from_sequence([records_episode_to_add], npartitions=1)
        if self.dbg is not None:
            self.dbg = db.concat([self.dbg, dask_bag_ep])
        else:
            self.dbg = dask_bag_ep

        try:
            with ProgressBar():
                self.dbg.to_avro(
                    self.pl_path / "bag_episodes.*.avro",
                    schema=self.dbg_schema,
                )
        except Exception as e:
            self.logger.warning(f"Writing avro error: {e}", extra=self.dict_logger)
        else:
            self.cnt = self.cnt + 1
            self.logger.info(f"deposit one episode in avro", extra=self.dict_logger)
        finally:
            self.logger.info(f"Done avro pool.")

    def get_query(self, query: Optional[PoolQuery] = None) -> Optional[Bag]:
        """
        get query from dask dataframe

        Arg:
            query: `PoolQuery` object

        return:
            a Dask Bag with all episodes in the query range
        """
        assert query is not None, f"query is None!"

        if query.episodestart_start is None:
            query.episodestart_start = veos_lifetime_start_date.to_pydatetime()

        if query.episodestart_end is None:
            query.episodestart_end = veos_lifetime_end_date.to_pydatetime()

        if query.seq_len_from is None:
            query.seq_len_from = 0

        if not query.seq_len_to is None:
            query.seq_len_to = int(
                1e09
            )  # 1 bio steps is enough as upper bound >74k Years
        if self.dbg is None:
            return None
        queried = self.dbg.filter(
            lambda x: x["meta"]["episode_meta"]["vehicle"] == query.vehicle
            and x["meta"]["episode_meta"]["driver"] == query.driver
            and (
                pd.Timestamp(query.episodestart_start)
                .tz_convert(tz="UTC")
                .tz_localize(None)
                < pd.to_datetime(
                    x["meta"]["episode_meta"]["episodestart"], unit="us"
                )  # timestamp in avro is UTC in microsecond
                < pd.Timestamp(query.episodestart_end)
                .tz_convert(tz="UTC")
                .tz_localize(None)
            )  # do timestamps from avro get need conversion? x["meta"]["episode_meta"]["episodestart"]? x:
            and (query.seq_len_from < len(x["sequence"]) < query.seq_len_to)
        )
        assert isinstance(queried, Bag), f"queried is not a bag!"
        return queried

    def find(self, query: PoolQuery) -> Optional[pd.DataFrame]:
        """
        Find records by the `PoolQuery` object.
        The down-stream task can use pandas dataframe unique() for index to get unique episodes.

        Arg:
            query: `PoolQuery` object

        Return:
            A multi-indexed DataFrame with all episodes in the query range.
        """

        queried_dict = self.get_query(query).compute()
        df_episodes = avro_ep_decoding(queried_dict, tz_info=query.episodestart_start.tzinfo)  # type: ignore

        return df_episodes

    def delete(self, idx) -> None:
        """
        Delete a record by item id.

        Not yet implemented for arrow pool!
        """

        raise NotImplementedError

    def remove_episode(self, query: PoolQuery) -> None:
        """
        remove episodes in the query from bag, but not from avro file!

        Delete all episodes in the query range. Modify the bag in place.

        Arg:
            query: `PoolQuery` object

        Return:
                None
        """

        self.dbg = self.dbg.remove(
            lambda x: x["meta"]["episode_meta"]["vehicle"] == query.vehicle
            and x["meta"]["episode_meta"]["driver"] == query.driver
            and (
                pd.Timestamp(query.episodestart_start)
                .tz_convert(tz="UTC")
                .tz_localize(None)
                < pd.to_datetime(x["meta"]["episode_meta"]["episodestart"], unit="us")
                < pd.Timestamp(query.episodestart_end)
                .tz_convert(tz="UTC")
                .tz_localize(None)
            )
        )  # do timestamps from avro need conversion? x["meta"]["episode_meta"]["episodestart"]
        old_cnt = self.cnt
        self.cnt = self._count(self.query)
        self.logger.info(
            f"Avro pool decreases in {old_cnt-self.cnt} episosdes.",
            extra=self.dict_logger,
        )

    def sample(
        self,
        size: int = 4,  # desired size of the samples
        *,
        query: Optional[PoolQuery] = None,  # query for sampling
    ) -> pd.DataFrame:
        """
        Sample a batch of episodes from Apache avro pool.

        downstream can use pandas DataFrame unique() for index to extract single episodes.
        since return is a dataframe, downstream can use pandas dataframe unique() for index to get unique episodes.
        Therefore, decoding to DataFrame have to be done in avro pool

        Args:
            size: number of episodes to sample
            query: `PoolQuery` object

        Return:
            A DataFrame with all episodes
        """

        if query == self.query:
            cnt = self.cnt
        else:
            cnt = self._count(query)

        queried = self.get_query(query)

        if cnt >= size:
            sampled = db.random.sample(
                population=queried, k=size, split_every=8
            )  # todo: split_every=8 is the default number, to be investigated
        else:
            sampled = db.random.choices(population=queried, k=size, split_every=8)

        # query.timestamp_start.tzinfo is Optional[tzinfo], avro_ep_decoding() requires tzinfo as optional
        df_episodes = avro_ep_decoding(
            sampled.compute(),  # bag to nested lists
            tz_info=query.episodestart_start.tzinfo,  # type: ignore
        )

        return df_episodes

    def __iter__(self):
        return (record for record in self.dbg.__iter__())
