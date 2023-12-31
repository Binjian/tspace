# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/06.dataflow.consumer.ipynb.

# %% auto 0
__all__ = ['T', 'Consumer']

# %% ../../nbs/06.dataflow.consumer.ipynb 3
import abc
from threading import Event
from dataclasses import dataclass
from typing import Optional, TypeVar, Generic

# %% ../../nbs/06.dataflow.consumer.ipynb 4
from .pipeline.queue import Pipeline  # type: ignore

# %% ../../nbs/06.dataflow.consumer.ipynb 5
T = TypeVar("T")  # A Generic type

# %% ../../nbs/06.dataflow.consumer.ipynb 6
@dataclass
class Consumer(
    abc.ABC, Generic[T]
):  # Pycharm false positive warning for Generic type non-unique:w
    """Consumer consumes data into the pipeline. It provides the unified interface for data consumption consume()"""

    def __post_init__(self):
        super().__init__()

    @abc.abstractmethod
    def consume(
        self,
        pipeline: Pipeline[T],  # T: pd.DataFrame
        start_event: Optional[Event] = None,  # input event: start
        stop_event: Optional[Event] = None,  # input event: stop
        interrupt_event: Optional[Event] = None,  # input event: interrupt
        exit_event: Optional[Event] = None,  # input event: exit
        flash_event: Optional[Event] = None,  # output event: flash
    ):
        """
        consume data into the pipeline
        """
        pass
