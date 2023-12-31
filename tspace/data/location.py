# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/01.data.location.ipynb.

# %% auto 0
__all__ = ['LocationCat', 'locations', 'locations_by_abbr', 'locations_from_tz', 'EosLocation']

# %% ../../nbs/01.data.location.ipynb 2
from pydantic import BaseModel, ConfigDict, field_serializer
from ordered_set import OrderedSet
from zoneinfo import ZoneInfo
from .time import timezones

# %% ../../nbs/01.data.location.ipynb 5
from fastcore.utils import *

# %% ../../nbs/01.data.location.ipynb 6
LocationCat = OrderedSet(
    [
        "jiangyin",  # Location cat for Jiangyin
        "shanghai",  # Location cat for Shanghai
        "anting",  # Location cat for Anting
        "unknown",  # Location cat for unknown
    ]
)

# %% ../../nbs/01.data.location.ipynb 9
class EosLocation(BaseModel):
    """
    location class for eos, `abbr`, `name`, `cname`, `tz` are required

    args:

        abbr: abbreviation
        name: name
        cname: chinese name
        tz: timezone

    return:
            EosLocation
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    abbr: str  # abbreviation
    name: str  # name
    cname: str  # chinese name
    tz: ZoneInfo  # timezone

    @field_serializer("tz")
    def serialize_tz(self, tz: ZoneInfo, _info):  #  # timezone  # other info
        """
        serialize timezone to string

        args:

            tz: timezone
            _info:  other info

        return:

                str

        """
        return tz.key

# %% ../../nbs/01.data.location.ipynb 13
locations = [
    EosLocation(
        abbr="jy",
        name="Jiangyin",
        cname="江阴",
        tz=timezones["sh"],
    ),
    EosLocation(
        abbr="hq",
        name="Hongqiao",
        cname="虹桥",
        tz=timezones["sh"],
    ),
    EosLocation(
        abbr="sh",
        name="Shanghai",
        cname="上海",
        tz=timezones["sh"],
    ),
    EosLocation(
        abbr="at",
        name="Anting",
        cname="安亭",
        tz=timezones["sh"],
    ),
    EosLocation(
        abbr="sp",
        name="Sao_Paulo",
        cname="圣保罗",
        tz=timezones["sp"],
    ),
    EosLocation(
        abbr="la",
        name="Los_Angeles",
        cname="洛杉矶",
        tz=timezones["la"],
    ),
    EosLocation(
        abbr="ny",
        name="New_York",
        cname="纽约",
        tz=timezones["ny"],
    ),
    EosLocation(
        abbr="xj",
        name="Urumqi",
        cname="乌鲁木齐",
        tz=timezones["xj"],
    ),
    EosLocation(
        abbr="bl",
        name="Berlin",
        cname="柏林",
        tz=timezones["bl"],
    ),
    EosLocation(
        abbr="ld",
        name="London",
        cname="伦敦",
        tz=timezones["ld"],
    ),
    EosLocation(
        abbr="sy",
        name="Sydney",
        cname="悉尼",
        tz=timezones["sy"],
    ),
    EosLocation(
        abbr="jp",
        name="Tokyo",
        cname="东京",
        tz=timezones["jp"],
    ),
    EosLocation(
        abbr="hk",
        name="Hong_Kong",
        cname="香港",
        tz=timezones["hk"],
    ),
    EosLocation(
        abbr="rj",
        name="Rio_de_Janeiro",
        cname="里约热内卢",
        tz=timezones["rj"],
    ),
    EosLocation(
        abbr="unknown",
        name="unknown",
        cname="未知",
        tz=timezones["utc"],
    ),
]

# %% ../../nbs/01.data.location.ipynb 15
locations_by_abbr = dict(zip([location.abbr for location in locations], locations))

# %% ../../nbs/01.data.location.ipynb 17
# since ZoneInfo is hashable, we can use it as key! one to many mapping! among all the tz, the last is the output
locations_from_tz = dict(zip([location.tz for location in locations], locations))
