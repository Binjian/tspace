# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/04.conn.clearable_pull_consumer.ipynb.

# %% auto 0
__all__ = ['ClearablePullConsumer']

# %% ../../nbs/04.conn.clearable_pull_consumer.ipynb 3
import ctypes
from ctypes import c_int
from _ctypes import POINTER
from rocketmq.client import PullConsumer, RecvMessage, _to_bytes  # type: ignore
from rocketmq.exceptions import ffi_check  # type: ignore
from rocketmq.ffi import _CMessageQueue, _CPullStatus, dll  # type: ignore

# %% ../../nbs/04.conn.clearable_pull_consumer.ipynb 4
class ClearablePullConsumer(PullConsumer):
    """
    PullConsumer with clear_history method

    Attributes:
        offset_table (dict): {mq_key: offset}
    """

    def _get_mq_key(self, mq):
        key = "%s@%s%s" % (mq.topic, mq.queueId, mq.brokerName)
        return key

    def get_message_queue_offset(self, mq):
        offset = self.offset_table.get(self._get_mq_key(mq), 0)
        return offset

    def set_message_queue_offset(self, mq, offset):
        self.offset_table[self._get_mq_key(mq)] = offset

    def clear_history(self, topic, expression="*"):
        max_num = 32  # pow(2,32)
        message_queue = POINTER(_CMessageQueue)()
        queue_size = c_int()
        ffi_check(
            dll.FetchSubscriptionMessageQueues(
                self._handle,
                _to_bytes(topic),
                ctypes.pointer(message_queue),
                ctypes.pointer(queue_size),
            )
        )

        for i in range(int(queue_size.value)):
            mq = message_queue[i]
            tmp_offset = ctypes.c_longlong(self.get_message_queue_offset(mq))
            # print('\n', self._get_mq_key(mq), 'clear', i, '/', queue_size.value,  tmp_offset)
            has_new_msg = True
            while has_new_msg:
                pull_res = dll.Pull(
                    self._handle,
                    ctypes.pointer(mq),
                    _to_bytes(expression),
                    tmp_offset,
                    max_num,
                )

                if pull_res.pullStatus != _CPullStatus.BROKER_TIMEOUT:
                    tmp_offset = pull_res.nextBeginOffset
                    self.set_message_queue_offset(mq, tmp_offset)
                    # print(self._get_mq_key(mq), 'cleared timeout', i, tmp_offset)
                    pass

                if pull_res.pullStatus == _CPullStatus.FOUND:
                    tmp_offset = pull_res.nextBeginOffset
                    self.set_message_queue_offset(mq, tmp_offset)
                    # print(self._get_mq_key(mq), 'cleared', i, tmp_offset)
                    pass

                elif pull_res.pullStatus == _CPullStatus.NO_MATCHED_MSG:
                    pass
                elif pull_res.pullStatus == _CPullStatus.NO_NEW_MSG:
                    has_new_msg = False
                elif pull_res.pullStatus == _CPullStatus.OFFSET_ILLEGAL:
                    pass
                else:
                    print(pull_res.pullStatus)
                    pass
                dll.ReleasePullResult(
                    pull_res
                )  # NOTE: No need to check ffi return code here
        # print('pull to rocketmq history cleared')
        ffi_check(dll.ReleaseSubscriptionMessageQueue(message_queue))

    def pull(self, topic, expression="*", max_num=32):
        message_queue = POINTER(_CMessageQueue)()
        queue_size = c_int()
        ffi_check(
            dll.FetchSubscriptionMessageQueues(
                self._handle,
                _to_bytes(topic),
                ctypes.pointer(message_queue),
                ctypes.pointer(queue_size),
            )
        )

        for i in range(int(queue_size.value)):
            mq = message_queue[i]
            tmp_offset = ctypes.c_longlong(self.get_message_queue_offset(mq))
            # print(i, '/', queue_size.value , tmp_offset,  self._get_mq_key(mq))

            has_new_msg = True
            while has_new_msg:
                pull_res = dll.Pull(
                    self._handle,
                    ctypes.pointer(mq),
                    _to_bytes(expression),
                    tmp_offset,
                    max_num,
                )

                if pull_res.pullStatus != _CPullStatus.BROKER_TIMEOUT:
                    tmp_offset = pull_res.nextBeginOffset
                    self.set_message_queue_offset(mq, tmp_offset)
                    pass

                if pull_res.pullStatus == _CPullStatus.FOUND:
                    tmp_offset = pull_res.nextBeginOffset
                    self.set_message_queue_offset(mq, tmp_offset)

                    for ii in range(int(pull_res.size)):
                        yield RecvMessage(pull_res.msgFoundList[ii])
                elif pull_res.pullStatus == _CPullStatus.NO_MATCHED_MSG:
                    pass
                elif pull_res.pullStatus == _CPullStatus.NO_NEW_MSG:
                    has_new_msg = False
                elif pull_res.pullStatus == _CPullStatus.OFFSET_ILLEGAL:
                    pass
                else:
                    pass
                dll.ReleasePullResult(
                    pull_res
                )  # NOTE: No need to check ffi return code here
        ffi_check(dll.ReleaseSubscriptionMessageQueue(message_queue))
