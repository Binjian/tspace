# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../nbs/07.agent.utils.hyperparams.ipynb.

# %% ../../../nbs/07.agent.utils.hyperparams.ipynb 3
from __future__ import annotations
from typing import TypeVar
from pydantic import BaseModel

# %% auto 0
__all__ = ['default_truck', 'HyperParam', 'HyperParamDPG', 'HyperParamDDPG', 'HyperParamIDQL', 'HyperParamRDPG']

# %% ../../../nbs/07.agent.utils.hyperparams.ipynb 4
from ...config.vehicles import trucks_by_id

# %% ../../../nbs/07.agent.utils.hyperparams.ipynb 5
# default_truck = trucks_by_id['default']
default_truck = trucks_by_id["VB7_FIELD"]

# %% ../../../nbs/07.agent.utils.hyperparams.ipynb 6
class HyperParamDPG(BaseModel):
    """
    Generic Hyperparameters for the RL agent

    Attributes:

        - BatchSize: int = 4  # batch size for training
        - NStates: int = (
            default_truck.observation_numel
        )  # number of states in the state space
        - NActions: int = (
            default_truck.torque_flash_numel
        )  # number of actions in the action space
        - ActionBias: float = 0.0  # bias for action output
        - NLayerActor: int = 2  # number of layers for the actor network
        - NLayerCritic: int = 2  # number of layers for the critic network
        - Gamma: float = 0.99  # Gamma value for RL discount
        - TauActor: float = 0.005  # Tau value for Polyak averaging for the actor network
        - TauCritic: float = 0.005  # Tau value for Polyak averaging for the actor network
        - ActorLR: float = 0.001  # learning rate for the actor network
        - CriticLR: float = 0.002  # learning rate for the critic network
        - CkptInterval: int = 5  # checkpoint interval
    """

    BatchSize: int = 4  # batch size for training
    NStates: int = (
        default_truck.observation_numel
    )  # number of states in the state space
    NActions: int = (
        default_truck.torque_flash_numel
    )  # number of actions in the action space
    ActionBias: float = 0.0  # bias for action output`
    NLayerActor: int = 2  # number of layers for the actor network
    NLayerCritic: int = 2  # number of layers for the critic network
    Gamma: float = 0.99  # Gamma value for RL discount
    TauActor: float = 0.005  # Tau value for Polyak averaging for the actor network
    TauCritic: float = 0.005  # Tau value for Polyak averaging for the actor network
    ActorLR: float = 0.001  # learning rate for the actor network
    CriticLR: float = 0.002  # learning rate for the critic network
    CkptInterval: int = 5  # checkpoint interval

# %% ../../../nbs/07.agent.utils.hyperparams.ipynb 7
class HyperParamDDPG(HyperParamDPG):
    """
    Hyperparameters for the DDPG agent


    Attributes:

        - CriticStateInputDenseDimension1: int = (
            16  # output dimension for the state input (first) Dense layer
        )
        - CriticStateInputDenseDimension2: int = (
            32  # output dimension for the state input second Dense layer
        )
        - CriticActionInputDenseDimension: int = (
            32  # output dimension for the action input Dense layer
        )
        - CriticOutputDenseDimension1: int = (
            256  # output dimension for the first critic output Dense layer
        )
        - CriticOutputDenseDimension2: int = (
            256  # output dimension for the second critic output Dense layer
        )
        - ActorInputDenseDimension1: int = (
            256  # output dimension for the first actor input Dense layer
        )
        - ActorInputDenseDimension2: int = (
            256  # output dimension for the second actor input Dense layer
        )
    """

    CriticStateInputDenseDimension1: int = (
        16  # output dimension for the state input (first) Dense layer
    )
    CriticStateInputDenseDimension2: int = (
        32  # output dimension for the state input second Dense layer
    )
    CriticActionInputDenseDimension: int = (
        32  # output dimension for the action input Dense layer
    )
    CriticOutputDenseDimension1: int = (
        256  # output dimension for the first critic output Dense layer
    )
    CriticOutputDenseDimension2: int = (
        256  # output dimension for the second critic output Dense layer
    )
    ActorInputDenseDimension1: int = (
        256  # output dimension for the first actor input Dense layer
    )
    ActorInputDenseDimension2: int = (
        256  # output dimension for the second actor input Dense layer
    )

# %% ../../../nbs/07.agent.utils.hyperparams.ipynb 8
class HyperParamIDQL(HyperParamDPG):
    """
    Hyperparameters for the DDPG agent


    Attributes:

        - CriticStateInputDenseDimension1: int = (
            16  # output dimension for the state input (first) Dense layer
        )
        - CriticStateInputDenseDimension2: int = (
            32  # output dimension for the state input second Dense layer
        )
        - CriticActionInputDenseDimension: int = (
            32  # output dimension for the action input Dense layer
        )
        - CriticOutputDenseDimension1: int = (
            256  # output dimension for the first critic output Dense layer
        )
        - CriticOutputDenseDimension2: int = (
            256  # output dimension for the second critic output Dense layer
        )
        - ActorInputDenseDimension1: int = (
            256  # output dimension for the first actor input Dense layer
        )
        - ActorInputDenseDimension2: int = (
            256  # output dimension for the second actor input Dense layer
        )
    """

    CriticStateInputDenseDimension1: int = (
        16  # output dimension for the state input (first) Dense layer
    )
    CriticStateInputDenseDimension2: int = (
        32  # output dimension for the state input second Dense layer
    )
    CriticActionInputDenseDimension: int = (
        32  # output dimension for the action input Dense layer
    )
    CriticOutputDenseDimension1: int = (
        256  # output dimension for the first critic output Dense layer
    )
    CriticOutputDenseDimension2: int = (
        256  # output dimension for the second critic output Dense layer
    )
    ActorInputDenseDimension1: int = (
        256  # output dimension for the first actor input Dense layer
    )
    ActorInputDenseDimension2: int = (
        256  # output dimension for the second actor input Dense layer
    )

# %% ../../../nbs/07.agent.utils.hyperparams.ipynb 9
class HyperParamRDPG(HyperParamDPG):
    """
    Hyperparameters for the RDPG agent

    Attributes:

        - HiddenDimension: int = 256  # hidden unit number for the action input layer
        - PaddingValue: float = (
            -10000
        )  # padding value for the input, impossible value for observation, action or reward
        - tbptt_k1: int = 200  # truncated backpropagation through time: forward steps,
        - tbptt_k2: int = 200  # truncated backpropagation through time: backward steps
    """

    HiddenDimension: int = 256  # hidden unit number for the action input layer
    PaddingValue: float = (
        -10000
    )  # padding value for the input, impossible value for observation, action or reward
    tbptt_k1: int = 200  # truncated backpropagation through time: forward steps,
    # example: 100*4s=400s (6min40s), 200*4s=800s (13min20s) 400*4s=1600s (26min40s)
    tbptt_k2: int = 200  # truncated backpropagation through time: backward steps,
    # Note: keras only support k1=k2, ignite support k1!=k2

# %% ../../../nbs/07.agent.utils.hyperparams.ipynb 10
class HyperParamIDQL(HyperParamDPG):
    """
    Hyperparameters for the IDQL agent

    Attributes:

        - HiddenDimension: int = 256  # hidden unit number for the action input layer
        - PaddingValue: float = (
            -10000
        )  # padding value for the input, impossible value for observation, action or reward
        - tbptt_k1: int = 200  # truncated backpropagation through time: forward steps,
        - tbptt_k2: int = 200  # truncated backpropagation through time: backward steps
    """

    HiddenDimension: int = 256  # hidden unit number for the action input layer
    PaddingValue: float = (
        -10000
    )  # padding value for the input, impossible value for observation, action or reward
    tbptt_k1: int = 200  # truncated backpropagation through time: forward steps,
    # example: 100*4s=400s (6min40s), 200*4s=800s (13min20s) 400*4s=1600s (26min40s)
    tbptt_k2: int = 200  # truncated backpropagation through time: backward steps,
    # Note: keras only support k1=k2, ignite support k1!=k2

# %% ../../../nbs/07.agent.utils.hyperparams.ipynb 11
HyperParam = TypeVar("HyperParam", HyperParamDDPG, HyperParamRDPG, HyperParamIDQL)
