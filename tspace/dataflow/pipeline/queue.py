# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../nbs/06.dataflow.pipeline.queue.ipynb.

# %% auto 0
__all__ = ['T', 'Pipeline']

# %% ../../../nbs/06.dataflow.pipeline.queue.ipynb 3
import queue
from typing import TypeVar

# %% ../../../nbs/06.dataflow.pipeline.queue.ipynb 4
T = TypeVar("T")  # Generic type

# %% ../../../nbs/06.dataflow.pipeline.queue.ipynb 5
class Pipeline(queue.Queue[T]):
    """Pipeline class from Queue for single-ended unit in dataflow"""

    def get_data(self) -> T:
        """
        Get data from the pipeline

        return:
            data: data from the pipeline
        """
        return self.get()

    def put_data(self, value: T):
        """
        Put data into the pipeline

        arg:

            value: data to be put into the pipeline

        return:

            None
        """

        self.put(value)

    def clear(self):
        """
        clear the pipeline (Queue) as the standard Queue

        since python `queue.Queue` does not have clear() method
        """
        while not self.empty():
            self.get()