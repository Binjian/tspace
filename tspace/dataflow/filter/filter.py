# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../nbs/06.dataflow.filter.filter.ipynb.

# %% auto 0
__all__ = ['T_RAW', 'T', 'Filter']

# %% ../../../nbs/06.dataflow.filter.filter.ipynb 3
import abc
from threading import Event
from typing import Union
from dataclasses import dataclass
from typing import Optional, TypeVar, Generic

# %% ../../../nbs/06.dataflow.filter.filter.ipynb 4
from ..pipeline.queue import Pipeline  # type: ignore
from ..pipeline.deque import PipelineDQ  # type: ignore

# %% ../../../nbs/06.dataflow.filter.filter.ipynb 5
T_RAW = TypeVar("T_RAW")  # Generic type for raw data
T = TypeVar("T")  # Generic type for processed data

# %% ../../../nbs/06.dataflow.filter.filter.ipynb 6
@dataclass
class Filter(abc.ABC, Generic[T_RAW, T]):
    """Filter consume data into the pipeline. It provides a shared interface for signal processing units filter()."""

    def __post_init__(self):
        super().__init__()

    @abc.abstractmethod
    def filter(
        self,
        in_pipeline: Union[
            PipelineDQ[T_RAW], Pipeline[T]
        ],  # deque[dict[str,str]] for vehicle_interface, Queue[pd.DataFrame] for crunchers
        out_pipeline: Pipeline[T],  # output pipeline
        start_event: Optional[Event],  # input event start
        stop_event: Optional[Event],  # input event stop
        interrupt_event: Optional[Event],  # input event interrupt
        flash_event: Optional[Event],  # input event flash
        exit_event: Optional[Event],  # input event exit
    ) -> None:
        """filter data from in_pipeline to out_pipeline"""
        pass
