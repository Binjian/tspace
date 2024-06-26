# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../nbs/05.storage.pool.parquet.ipynb.

# %% ../../../nbs/05.storage.pool.parquet.ipynb 3
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Optional
import dask.dataframe as dd  # type: ignore
import pandas as pd  # type: ignore
import pyarrow as pa  # type: ignore
import pyarrow.parquet as pq  # type: ignore
from dacite import from_dict  # type: ignore
from dask.diagnostics import ProgressBar  # type: ignore

# %% auto 0
__all__ = ['ParquetPool']

# %% ../../../nbs/05.storage.pool.parquet.ipynb 5
from .dask import DaskPool
from tspace.data.core import (
    ObservationMeta,
    PoolQuery,
    veos_lifetime_end_date,
    veos_lifetime_start_date,
)
from ...data.location import locations_by_abbr
from ...data.external.pandas_utils import encode_dataframe_from_parquet

# %% ../../../nbs/05.storage.pool.parquet.ipynb 6
@dataclass(kw_only=True)
class ParquetPool(  # type: ignore
    DaskPool
):  # new feature of python 3.10, not an error. IDE fall behind
    """
    The pool class for storing and retrieving records in Apache Arrow parquet files.

    It uses Pandas backend for Parquet, PyArrow Parquet interface for meta data storage, and Dask DataFrame for data processing.
    meta information is stored in parquet metadata (in footer of parquet file).

    Sample random observation quadruples will need some care to reassure the randomness.
    Here we apply dask DataFrame sample method. We use Dask Delayed to parallelize the data processing like sampling

    Attributes:

        pl_path: `Path` to the parquet file folder
        meta: meta information of the pool
        query: `PoolQuery` object to the pool
        cnt: number of records in the pool
        ddf: dask DataFrame object
    """

    ddf: Optional[dd.DataFrame] = (
        None  # dd.from_pandas(pd.DataFrame(), npartitions=1)  # dask DataFrame
    )

    def __post_init__(self):
        """load parquet pool from parquet files in folder specified by the recipe and validate meta information"""
        self.logger = self.logger.getChild("parquet pool")
        self.dict_logger = self.dict_logger
        super().__post_init__()

        self.logger.info(
            f"{{'header': 'Parquet pool stored', "
            f"'path': '{self.pl_path}', "
            f"'coll_type' : '{self.recipe['DEFAULT']['coll_type']}'}}",
            extra=self.dict_logger,
        )
        self.load()

    def load(self):
        """load RECORD arrays from parquet files in folder specified by the recipe"""
        try:
            with ProgressBar():
                self.ddf = dd.read_parquet(
                    str(self.pl_path),  # Path to str conversion
                    engine="pyarrow",
                    compression="snappy",
                    ignore_metadata_file=False,
                    split_row_groups="infer",
                    # infer_division=True,
                )
                # parquet file which is partitioned by a timestamp was converted to category,
                # when loaded to dask dataframe

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
            # # find and select the target partition with vehicle id and driver id in the Query
            # self.ddf_list = []
            # for n in range(self.ddf.npartitions):
            #     self.ddf_list.append(self.ddf.get_partition(n))
            # for i, ddf in enumerate(self.ddf_list):
            #     # if dfs_episode_new['vehicle']
            #     print(f"{i}")
            #     # df = ddf.compute()
            #     # ddf.columns
            #     # ddf.dtypes
            #     vehicle = ddf['vehicle__'].compute()[0]
            #     driver = ddf['driver__'].compute()[0]
            #     # df_episode_new = df_episode_new.append(ddf)
            #     if self.query['vehicle'] == vehicle and self.query['driver'] == driver:
            #         bHit = True
            #         print(
            #             f' hit {i}{"st" if i == 1 else "nd" if i == 2 else "rd" if i == 3 else "th"} partition'
            #         )
            #         # k = i
            #         self.ddf_list.append(i)
            #
            #         # ddf_db_list[i] = dd.concat([ddf, df], axis=0)
            #         # append ddf to dfs_episode_new
        except Exception as e:
            self.logger.warning(f"Loading Parquet error: {e}", extra=self.dict_logger)
            raise e

        self.logger.info(
            f"{{'header': 'Loading dataframe from parquet files.',  "
            f"'path': '{self.pl_path}'}}"
        )

        try:
            # load meta information from parquet metadata and compare with input metadata
            table_meta = pq.read_metadata(self.pl_path / "_common_metadata")
        except FileNotFoundError as e:
            self.logger.warning(
                f"{{'header': 'eos meta data not found in parquet file', "
                f"'path': '{self.pl_path}'}}",
                extra=self.dict_logger,
            )
            raise e
        pq_meta_info = json.loads(
            (table_meta.metadata[b"eos"]).decode().replace("'", '"')
        )
        pq_meta_info["site"] = locations_by_abbr[pq_meta_info["site"]["abbr"]]
        meta_from_pq = ObservationMeta(**pq_meta_info)
        for key, val in pq_meta_info.items():
            self.logger.info(
                f"{{'header': 'eos meta data', " f"'{key}': '{val}'}}",
                extra=self.dict_logger,
            )
        assert self.meta.have_same_meta(
            meta_from_pq
        ), f"meta information in parquet file doesn't match with input meta information!"

        self.cnt = self._count(self.query)
        # TODO if different, raise warning and update meta information in parquet file

    def close(self):
        """close the pool"""
        self.logger.info(
            f"Nothing to be done for dask parquet pool!",  # neither arrow parquet nor avro need cleaning up.
            extra=self.dict_logger,
        )

    def store(self, episode: pd.DataFrame) -> None:
        """Deposit an episode with all records in every time step into arrow parquet."""

        # reset index level vehicle, driver, episodestart to columns, so that the only index is timestamp
        episode_flat = episode.reset_index(level=["vehicle", "driver", "episodestart"])
        # convert vehicle and driver to category
        # episode_flat["vehicle"] = episode_flat["vehicle"].astype("category")
        # episode_flat["driver"] = episode_flat["driver"].astype("category")
        # episode_flat["episodestart"] = episode_flat["episodestart"].astype(
        #     "datetime64[ns]")

        # Convert Input DataFrame to flat-indexed DataFrame both in rows and columns
        # encoding MultiIndex columns index to string
        episode_flat.columns = pd.Index(
            [
                (
                    f"{x[0]}_{x[1]}_{x[2]}"
                    if (x[1] != "" and x[2] != "")
                    else (
                        f"{x[0]}_{x[1]}_"
                        if (x[1] != "" and x[2] == "")
                        else (
                            f"{x[0]}__{x[2]}"  # !!! dunder!!!
                            if (x[2] != "")
                            else f"{x[0]}__"
                        )
                    )
                )
                for x in episode_flat.columns.to_flat_index()
            ]
        )

        # episode_flat.set_index('timestamp__', inplace=True)
        # self.logger.info(f"{{'header': 'episode_flat index', "
        #                 f"\'ddf.index\': {episode_flat.index}}}",
        #                 extra=self.dict_logger)
        # episode_flat["episodestart__"] = episode_flat["episodestart__"].astype("datetime64[ns]")

        self.logger.info(f"deposit one episode in Parquet", extra=self.dict_logger)
        try:
            episode_flat.to_parquet(
                self.pl_path,
                engine="pyarrow",
                compression="snappy",
                index=True,
                partition_cols=["vehicle__", "driver__"],
            )
            #         write_metadata_file=True,  # write metadata file, default is True
            #         custom_metadata=self.input_metadata,  # write input meta information to parquet metadata
            #         overwrite=False,  # if not empty, not overwrite and append
            #         allow_truncated_timestamps=True,  # allow Timestamp to be truncated from ns to ms

        except Exception as e:
            self.logger.error(f"Writing Parquet error: {e}", extra=self.dict_logger)
            raise e

        # if the first parquet file, generate from pyarrow Table and store _common_metadata
        if self.ddf is None:
            table = pa.Table.from_pandas(df=episode_flat)
            input_metadata = {"eos": str(self.meta.model_dump()).replace("'", '"')}
            schema = table.schema.with_metadata(input_metadata)
            pq.write_metadata(schema, str(self.pl_path / "_common_metadata"))

        try:
            with ProgressBar():
                self.ddf = dd.read_parquet(
                    str(self.pl_path),  # Path to str conversion
                    engine="pyarrow",
                    compression="snappy",
                    ignore_metadata_file=False,
                    split_row_groups="infer",
                    # infer_division=True,
                )
                # parquet file which is partitioned by a timestamp was converted to category,
                # when loaded to dask dataframe
        except Exception as e:
            self.logger.warning(f"Loading Parquet error: {e}", extra=self.dict_logger)
            raise e

        last_cnt = self.cnt
        # self.cnt = self._count(self.query)
        self.cnt = last_cnt + len(episode)
        self.logger.info(f"Pool size: {self.cnt} records.", extra=self.dict_logger)

    def delete(self, idx) -> None:
        """
        Delete a record by item id.

        not implemented for arrow pool
        """
        raise NotImplementedError

    def delete_episode(self, query: PoolQuery) -> None:
        """
        delete records specified by `PoolQuery`

        Caution:
        TODO wrong implementation, since Dask does not support drop rows for the moment
        TODO Integrate PYSpark and save to Apache Delta Lake
        So now Arrow pool does not support delete episode or rows in general
        but you can use filter and groupby!!


        Expected:
        Delete all records in an episode by PoolQuery with
            - vehicle
            - driver
            - episodestart_start
            - episodestart_end

        """
        res = self.get_query(query)
        old_cnt = self.cnt
        self.ddf.drop(res.index, inplace=True)
        self.cnt = self._count(self.query)

        try:
            input_metadata = {
                b"eos": str(self.meta.model_dump()).replace("'", '"').encode()
            }
            with ProgressBar():
                self.ddf.to_parquet(
                    self.pl_path,
                    engine="pyarrow",
                    compression="snappy",
                    partition_on=[
                        "vehicle__",
                        "driver__",
                    ],
                    write_index=True,  # write index to parquet, default is True
                    custom_metadata=input_metadata,  # write input meta information to parquet metadata
                    append=False,
                    overwrite=True,
                    # allow_truncated_timestamps=True,
                )
        except Exception as e:
            self.logger.warning(
                f"Writing Parquet error while deleting episodes: {e}",
                extra=self.dict_logger,
            )
        else:
            self.logger.info(
                f"deleted {old_cnt - self.cnt} records in Parquet",
                extra=self.dict_logger,
            )
        finally:
            self.logger.info(f"The parquet pool contains now {self.cnt} records.")

    def get_query(self, query: Optional[PoolQuery] = None) -> Optional[dd.DataFrame]:
        """
        get query from dask dataframe parquet storage

        Arg:
            query: `PoolQuery` object to the pool

        Return:

            A Dask DataFrame with all records in the query time range
        """
        assert query is not None, f"query is None!"

        if query.episodestart_start is None:
            query.episodestart_start = veos_lifetime_start_date.to_pydatetime()

        if query.episodestart_end is None:
            query.episodestart_end = veos_lifetime_end_date.to_pydatetime()

        res = self.ddf.loc[
            (
                self.ddf["vehicle__"] == query.vehicle
            )  # comparing category type and str seems to work!
            & (self.ddf["driver__"] == query.driver)
            & (
                self.ddf["episodestart__"] >= pd.Timestamp(query.episodestart_start)
            )  # .tz_convert('UTC'))  #.tz_convert(None))
            & (
                self.ddf["episodestart__"] <= pd.Timestamp(query.episodestart_end)
            )  # .tz_convert('UTC'))  #.tz_convert(None))
        ].loc[
            pd.Timestamp(query.timestamp_start) : pd.Timestamp(query.timestamp_end)  # type: ignore
        ]
        assert isinstance(res, dd.DataFrame), f"res is not a dask DataFrame!"
        return res

    def sample(self, size: int = 4, *, query: PoolQuery) -> pd.DataFrame:  # type: ignore
        """
        Sample a batch of records from arrow parquet pool with fractional sampling.

        Args:
            size: number of records in the batch
            query: `PoolQuery` object to the pool

        Return:
            A Pandas DataFrame with all records in the query range
        """
        if query == self.query:
            cnt = self.cnt
        else:
            cnt = self._count(query)
        assert (
            0.0 < (size / cnt) <= 1.0
        ), f"sampling a dask dataframe must be fractional!"

        res = self.get_query(query)
        if size < 0.1 * cnt:
            rough_pick = res.sample(frac=0.15).compute()
            flat_batch = rough_pick.sample(n=size, replace=False, axis=0)
        else:
            self.logger.warning(
                f"sample size {size} is not smaller than 10% of total records {cnt}!"
            )
            rough_pick = res.compute()
            flat_batch = rough_pick.sample(n=size, replace=False, axis=0)

        assert len(flat_batch) == size, f"batch size is not {size}!"
        assert isinstance(flat_batch, pd.DataFrame), f"batch is not a pandas DataFrame!"
        batch = encode_dataframe_from_parquet(flat_batch)
        return batch

    def __iter__(self):
        return (record for record in self.ddf.iterrows())
