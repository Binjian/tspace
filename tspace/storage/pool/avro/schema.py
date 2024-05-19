# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../../nbs/05.storage.pool.avro.schema.ipynb.

# %% auto 0
__all__ = ['state_unit_fields_schema', 'state_specs_fields_schema', 'action_specs_fields_schema', 'reward_specs_fields_schema',
           'site_fields_schema', 'episode_meta_fields_schema', 'observation_meta_fields_schema', 'state_fields_schema',
           'action_fields_schema', 'reward_fields_schema', 'gen_torque_table_schema', 'gen_episode_array_fields_schema',
           'gen_episode_schema']

# %% ../../../../nbs/05.storage.pool.avro.schema.ipynb 3
from ....data.core import ObservationMeta

# %% ../../../../nbs/05.storage.pool.avro.schema.ipynb 4
state_unit_fields_schema = [
    {"name": "velocity_unit_code", "type": "string"},
    {"name": "thrust_unit_code", "type": "string"},
    {"name": "brake_unit_code", "type": "string"},
]

# %% ../../../../nbs/05.storage.pool.avro.schema.ipynb 5
state_specs_fields_schema = [
    {
        "name": "state_unit_codes",
        "type": {
            "type": "record",
            "name": "state_unit_codes_",
            "fields": state_unit_fields_schema,
        },
    },
    {"name": "state_number", "type": "int"},
    {"name": "unit_number_per_state", "type": "int"},
    {"name": "unit_duration", "type": "float"},
    {"name": "frequency", "type": "float"},
]

# %% ../../../../nbs/05.storage.pool.avro.schema.ipynb 6
action_specs_fields_schema = [
    {"name": "action_unit_code", "type": "string"},
    {"name": "action_row_number", "type": "int"},
    {"name": "action_column_number", "type": "int"},
]

# %% ../../../../nbs/05.storage.pool.avro.schema.ipynb 7
reward_specs_fields_schema = [{"name": "reward_unit_code", "type": "string"}]

# %% ../../../../nbs/05.storage.pool.avro.schema.ipynb 8
site_fields_schema = [
    {"name": "abbr", "type": "string"},
    {"name": "name", "type": "string"},
    {"name": "cname", "type": "string"},
    {"name": "tz", "type": "string"},
]

# %% ../../../../nbs/05.storage.pool.avro.schema.ipynb 9
episode_meta_fields_schema = [
    {"name": "vehicle", "type": "string"},
    {"name": "driver", "type": "string"},
    {"name": "episodestart", "type": "long", "logicalType": "timestamp-micros"},
]

# %% ../../../../nbs/05.storage.pool.avro.schema.ipynb 10
observation_meta_fields_schema = [
    {
        "name": "state_specs",
        "type": {
            "type": "record",
            "name": "state_specs_",
            "fields": state_specs_fields_schema,
        },
    },
    {
        "name": "action_specs",
        "type": {
            "type": "record",
            "name": "action_specs_",
            "fields": action_specs_fields_schema,
        },
    },
    {
        "name": "reward_specs",
        "type": {
            "type": "record",
            "name": "reward_specs_",
            "fields": reward_specs_fields_schema,
        },
    },
    {
        "name": "site",
        "type": {
            "type": "record",
            "name": "site_",
            "fields": site_fields_schema,
        },
    },
]

# %% ../../../../nbs/05.storage.pool.avro.schema.ipynb 11
state_fields_schema = [
    {"name": "velocity", "type": {"type": "array", "items": "float"}},
    {"name": "thrust", "type": {"type": "array", "items": "float"}},
    {"name": "brake", "type": {"type": "array", "items": "float"}},
    {
        "name": "timestep",
        "type": {
            "type": "array",
            "items": {"type": "long", "logicalType": "timestamp-micros"},
        },
    },
]

# %% ../../../../nbs/05.storage.pool.avro.schema.ipynb 12
def gen_torque_table_schema(obs_meta: ObservationMeta):  # An `ObservationMeta` object
    """Generate torque table schema from observation meta data"""
    torque_table_row_names = obs_meta.get_torque_table_row_names()
    torque_table_schema = [
        {"name": r, "type": {"type": "array", "items": "float"}}
        for r in torque_table_row_names
    ]

    return torque_table_schema

# %% ../../../../nbs/05.storage.pool.avro.schema.ipynb 13
action_fields_schema = [
    {"name": "speed", "type": {"type": "array", "items": "float"}},
    {"name": "throttle", "type": {"type": "array", "items": "float"}},
    {
        "name": "timestep",
        "type": {
            "type": "array",
            "items": {"type": "long", "logicalType": "timestamp-micros"},
        },
    },
]

# %% ../../../../nbs/05.storage.pool.avro.schema.ipynb 14
reward_fields_schema = [
    {"name": "work", "type": {"type": "array", "items": "float"}},
    {
        "name": "timestep",
        "type": {
            "type": "array",
            "items": {"type": "long", "logicalType": "timestamp-micros"},
        },
    },
]

# %% ../../../../nbs/05.storage.pool.avro.schema.ipynb 15
def gen_episode_array_fields_schema(
    obs_meta: ObservationMeta,  # An `ObservationMeta` object
):
    """Generate episode array fields schema from observation meta data"""
    episode_array_fields_schema = [
        {
            "type": "long",
            "name": "timestamp",
            "logicalType": "timestamp-micros",
        },
        {
            "name": "state",
            "type": {
                "type": "record",
                "name": "state_",
                "fields": state_fields_schema,
            },
        },
        {
            "name": "action",
            "type": {
                "type": "record",
                "name": "action_",
                "fields": gen_torque_table_schema(obs_meta) + action_fields_schema,
            },
        },
        {
            "name": "reward",
            "type": {
                "type": "record",
                "name": "reward_",
                "fields": reward_fields_schema,
            },
        },
        {
            "name": "nstate",
            "type": {
                "type": "record",
                "name": "nstate_",
                "fields": state_fields_schema,
            },
        },
    ]

    return episode_array_fields_schema

# %% ../../../../nbs/05.storage.pool.avro.schema.ipynb 16
def gen_episode_schema(
    obs_meta: ObservationMeta,  # An `ObservationMeta` object
) -> dict:
    """Generate episode schema from observation meta data"""
    schema_episode = {
        "type": "record",
        "name": "episode",
        "doc": "episode data with a timestamp, meta description and an array of episode steps",
        "fields": [
            {
                "type": "long",
                "name": "episodestart",
                "logicalType": "timestamp-micros",
            },
            {
                "name": "meta",
                "type": {
                    "type": "record",
                    "name": "meta_",
                    "fields": [
                        {
                            "name": "episode_meta",
                            "type": {
                                "type": "record",
                                "name": "episode_meta_",
                                "fields": episode_meta_fields_schema,
                            },
                        },
                        {
                            "name": "observation_meta",
                            "type": {
                                "type": "record",
                                "name": "observation_meta_",
                                "fields": observation_meta_fields_schema,
                            },
                        },
                    ],
                },
            },
            {
                "name": "sequence",
                "type": {
                    "type": "array",
                    "items": {
                        "name": "step",  # not used in constructing the episode observation array data
                        "type": "record",
                        "fields": gen_episode_array_fields_schema(obs_meta),
                    },
                },
            },
        ],
    }
    return schema_episode