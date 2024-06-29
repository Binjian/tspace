# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/07.agent.idql.ipynb.

# %% auto 0
__all__ = ['DatasetDict', 'IDQL']

# %% ../../nbs/07.agent.idql.ipynb 3
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import pandas as pd
import tensorflow as tf
from typeguard import check_type
import jax
import jax.numpy as jnp

# %% ../../nbs/07.agent.idql.ipynb 4
from tspace.agent.utils.hyperparams import (
    HyperParamDDPG,
    HyperParamRDPG,
    HyperParamIDQL,
)
from ..storage.buffer.dask import DaskBuffer
from ..storage.buffer.mongo import MongoBuffer  # type: ignore
from ..data.core import PoolQuery  # type: ignore
from ..data.time import veos_lifetime_end_date, veos_lifetime_start_date
from ..data.core import PoolQuery  # type: ignore
from ..data.time import veos_lifetime_end_date, veos_lifetime_start_date

# %% ../../nbs/07.agent.idql.ipynb 5
from .dpg import DPG  # type: ignore

# %% ../../nbs/07.agent.idql.ipynb 6
from ..config.vehicles import Truck, TruckInCloud, trucks_by_id
from ..config.drivers import Driver
import logging
from typing import Union
from tspace.data.core import (
    RE_RECIPEKEY,
    ActionSpecs,
    ObservationMetaCloud,
    ObservationMetaECU,
    RewardSpecs,
    StateSpecsCloud,
    StateSpecsECU,
    get_filemeta_config,
)

# %% ../../nbs/07.agent.idql.ipynb 7
from jaxrl5.agents import DDPMIQLLearner
from jaxrl5.types import DataType
from flax.core import FrozenDict
import gymnasium as gym

# %% ../../nbs/07.agent.idql.ipynb 8
DatasetDict = dict[str, DataType]

# %% ../../nbs/07.agent.idql.ipynb 9
@dataclass
class IDQL(DPG):
    """IDQL agent for VEOS.

    Abstracts:

        data interface:
            - pool in mongodb
            - buffer in memory (numpy array)
        model interface:
            - actor networkVj
            - critic network


    Attributes:

        idql_net: actor network
        _ckpt_idql_dir: checkpoint directory for critic

    """

    # Following are derived
    idql_net: Optional[DDPMIQLLearner] = None  # actor_net_default
    action_space: Optional[gym.spaces.Space] = None  # action_space_default
    observation_space: Optional[gym.spaces.Space] = None  # action_space_default
    _ckpt_idql_dir: Optional[Path] = None  # Path("")

    def __post_init__(
        self,
    ):
        """initialize the rdpg agent.

        args:
            truck.ObservationNumber (int): dimension of the state space.
            padding_value (float): value to pad the state with, impossible value for observation, action or re
        """

        self.logger = self.logger.getChild("eos").getChild(self.__str__())
        self.logger.propagate = True

        super().__post_init__()  # call DPG post_init for pool init and plot init
        self.coll_type = "EPISODE"
        self.hyper_param = HyperParamIDQL(
            HiddenDimension=256,
            PaddingValue=-10000,
            tbptt_k1=200,
            tbptt_k2=200,
            BatchSize=4,
            NStates=self.truck.observation_numel,
            NActions=self.truck.torque_flash_numel,
            ActionBias=self.truck.torque_bias,
            NLayerActor=2,
            NLayerCritic=2,
            Gamma=0.99,
            TauActor=0.005,
            TauCritic=0.005,
            ActorLR=0.001,
            CriticLR=0.001,
            CkptInterval=5,
        )

        self.buffer.query = PoolQuery(
            vehicle=self.truck.vid,
            driver=self.driver.pid,
            episodestart_start=veos_lifetime_start_date,
            episodestart_end=veos_lifetime_end_date,
            seq_len_from=1,  # from 10  # sample sequence with a length from 1 to 200
            seq_len_to=self.hyper_param.tbptt_k1 + 100,  # to 300
        )
        self.buffer.pool.query = self.buffer.query

        # actor network (w/ target network)
        self.init_checkpoint()

        self.action_space = gym.spaces.Box(
            low=0.0, high=1.0, shape=(self.truck.torque_flash_numel,), dtype=np.float32
        )  # action space is 4*17 matrix
        self.observation_space = gym.spaces.Box(
            low=0.0, high=50.0, shape=(self.truck.observation_numel,), dtype=np.float32
        )  # observation space is 30*3 matrix

        self.idql_net = DDPMIQLLearner.create(
            seed=42,
            observation_space=self.observation_space,
            action_space=self.action_space,
        )

        self.touch_gpu()

    def __repr__(self):
        return f"IDQL({self.truck.vid}, {self.driver.pid})"

    def __str__(self):
        return "IDQL"

    def __hash__(self):
        return hash(self.__repr__())

    def touch_gpu(self):
        """touch the gpu to avoid the first time delay"""

        # tf.summary.trace_on(graph=true, profiler=true)
        # ignites manual loading of tensorflow library, \
        # to guarantee the real-time processing of first data in main thread
        init_states = pd.Series(
            np.random.rand(self.truck.observation_numel)
        )  # state must have 30 (speed, throttle, current, voltage) 5 tuple

        # init_states = tf.expand_dims(input_array, 0)  # motion states is 30*2 matrix

        _ = self.actor_predict(init_states)
        self.logger.info(
            f"manual load tf library by calling convert_to_tensor",
            extra=self.dict_logger,
        )

        self.actor_net.ou_noise.reset()

        # warm up the gpu training graph execution pipeline
        if self.buffer.pool.cnt != 0:
            if not self.infer_mode:
                self.logger.info(
                    f"rdpg warm up training!",
                    extra=self.dict_logger,
                )
                (_, _) = self.train()

                self.logger.info(
                    f"rdpg warm up training done!",
                    extra=self.dict_logger,
                )

    def init_checkpoint(self):
        """create or restore from checkpoint"""

        # actor create or restore from checkpoint
        # add checkpoints manager
        self._ckpt_idql_dir = Path(self.data_folder).joinpath(
            "tf_ckpts-"
            + self.__str__()
            + "-"
            + self.truck.vid
            + "-"
            + self.driver.pid
            + "_"
            + "/actor"
        )

        try:
            os.makedirs(self._ckpt_actor_dir)
            self.logger.info(
                "created checkpoint directory for actor: %s",
                self._ckpt_actor_dir,
                extra=self.dict_logger,
            )
        except FileExistsError:
            self.logger.info(
                "actor checkpoint directory already exists: %s",
                self._ckpt_actor_dir,
                extra=self.dict_logger,
            )

    # TODO for infer only mode, implement a method without noisy exploration.
    def actor_predict(
        self, state: pd.Series  # state sequence of the current episode
    ) -> np.ndarray:  # action sequence of the current episode
        """
        sample actions with additive ou noise

        input: state is a pd.Series of length 3*10*3/4*50*3 (r*c), output numpy array

        Action outputs and noise object are all row vectors of length 21*17 (r*c), output numpy array
        """

        # We make sure action is within bounds
        # legal_action = np.clip(sampled_actions, action_lower, action_upper)
        # get flat interleaved (not column-wise stacked) tensor from dataframe

        state_flat = None
        try:
            state_flat = jnp.array(state.to_numpy())
        except Exception as e:
            print(f"Exception: {e}")

        states = jnp.expand_dims(
            check_type(state_flat, jnp.ndarray), 0
        )  # motion states is 30*3 matrix

        # sample implicit policy (not the behavior poicly), batch dimension in result is squeezed
        sampled_actions = self.idql_net.sample_implicit_policy(states)

        self.logger.info(f"Inference IDQL done!", extra=self.dict_logger)
        # return np.squeeze(sampled_actions)  # ? might be unnecessary
        return sampled_actions

    def sample_minibatch(self):
        """Convert batch type from DataFrames to flattened tensors."""
        if (
            self.buffer.pool.cnt == 0
        ):  # bootstrap for Episode 0 from the current self.observations list
            self.logger.info(
                f"no data in pool, bootstrap from observation_list, "
                f"truck: {self.truck.vid}, driver: {self.driver.pid}.",
                extra=self.dict_logger,
            )
            assert (
                len(self.observations) > 0
            ), "no data in temporary buffer self.observations!"

            # sample from self.observations

            batch_idx = np.random.choice(
                len(self.observations), self.hyper_param.BatchSize  # 4
            )
            observation_samples = [
                self.observations[i] for i in batch_idx
            ]  # a sampled list of Series

            idx = pd.IndexSlice
            state = []
            action = []
            reward = []
            nstate = []
            for (
                observation
            ) in (
                observation_samples
            ):  # each observation is a Series, contiguous storage in rows (already flattened!)
                state.append(
                    observation.loc[
                        idx["state", ["velocity", "thrust", "brake"]]
                    ].values
                )
                action.append(
                    observation.loc[idx["action", self.torque_table_row_names]].values
                )
                reward.append(observation.loc[idx["reward", ["work"]]].values)
                nstate.append(
                    observation.loc[
                        idx["nstate", ["velocity", "thrust", "brake"]]
                    ].values
                )

            # convert to tensors by stacking so that the first dimension is batch_size
            states = tf.convert_to_tensor(np.stack(state), dtype=tf.float32)
            actions = tf.convert_to_tensor(np.stack(action), dtype=tf.float32)
            rewards = tf.convert_to_tensor(np.stack(reward), dtype=tf.float32)
            next_states = tf.convert_to_tensor(np.stack(nstate), dtype=tf.float32)

        else:  # otherwise sample from pool, ignoring the current ongoing episode to reduce complexity
            # TODO combine current episode with pool, need evenly sampling pool and list of observations, then combine
            # get sampling range, if not enough data, batch is small
            self.logger.info(
                f"start sample from pool with size: {self.hyper_param.BatchSize}, "
                f"truck: {self.truck.vid}, driver: {self.driver.pid}.",
                extra=self.dict_logger,
            )

            (
                states,
                actions,
                rewards,
                nstates,
            ) = self.buffer.sample()  # for both mongo and arrow pool

            states = tf.convert_to_tensor(states, dtype=tf.float32)
            actions = tf.convert_to_tensor(actions, dtype=tf.float32)
            rewards = tf.convert_to_tensor(rewards, dtype=tf.float32)
            next_states = tf.convert_to_tensor(nstates, dtype=tf.float32)

        return states, actions, rewards, next_states

    def train(self):
        """Train the networks on the batch sampled from the pool."""
        (
            states,
            actions,
            rewards,
            next_states,
        ) = self.sample_minibatch()

        batch = FrozenDict(
            {
                "actions": actions,
                "rewards": rewards,
                "observations": states,
                "next_observations": next_states,
            }
        )

        agent, info = self.agent.update(batch)
        self.agent = agent
        critic_loss = info["critic_loss"]
        actor_loss = info["actor_loss"]
        _ = info["value_loss"]
        return critic_loss, actor_loss

    def soft_update_target(self):
        """update the target networks with Polyak averaging"""
        # it's already done in jaxrl5 agent update
        pass

    # we only calculate the loss

    def save_ckpt(self):
        """TODO Save the checkpoint of the actor, critic and value network in Flax."""
        pass

    # We only compute the loss and don't update parameters
    def get_losses(self):
        """Get the losses of the networks on the batch sampled from the pool."""
        (
            states,
            actions,
            rewards,
            next_states,
        ) = self.sample_minibatch()

        batch = FrozenDict(
            {
                "actions": actions,
                "rewards": rewards,
                "observations": states,
                "next_observations": next_states,
            }
        )

        agent, info = self.agent.eval_loss(batch)

        critic_loss = 0.0
        actor_loss = info["actor_loss"]
        return critic_loss, actor_loss
