# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/03.config.vcu.ipynb.

# %% auto 0
__all__ = ['generate_torque_table', 'generate_vcu_calibration', 'generate_lookup_table', 'test_generate_lookup_table',
           'test_generate_vcu_calibration']

# %% ../../nbs/03.config.vcu.ipynb 3
import glob
import os
import os.path
from pathlib import Path
import numpy as np
import pandas as pd  # type: ignore
from scipy import interpolate  # type: ignore

# %% ../../nbs/03.config.vcu.ipynb 5
def generate_torque_table(
    pedal_scale: tuple, speed_scale: tuple  # pedal range (0,1)  # speed range (0,120)
):
    """
    Generate VCU calibration parameters for a given truck.
    simple piecewise linear surface, close to default calibration table
    Input is npd 17, nvl 21; output vcu_param_list as float32
    pedal is x(column), velocity is y(row) )

    Parameters:

        pedal_scale: tuple
            pedal range (0,1)
        speed_scale: tuple
            speed range (0,120)

    Return:
        pandas dataframe
    """

    pdv, vlv = np.meshgrid(list(pedal_scale), list(speed_scale), sparse=True)
    v = pdv / (1 + np.sqrt(np.abs(vlv)))
    pd_v = pd.DataFrame(v, columns=list(pedal_scale), index=list(speed_scale))

    return pd_v

# %% ../../nbs/03.config.vcu.ipynb 6
def generate_vcu_calibration(
    npd: int,  # number of pedal steps
    pedal_range: tuple,  # pedal range (0,1)
    nvl: int,  # number of velocity steps
    velocity_range: tuple,  # speed range (0,120)
    shortcut: int,  # 1: use default eco calibration table
    data_root: Path,  # path to data folder
):
    """
    Generate VCU calibration parameters for a given truck.

    pedal is x(column), velocity is y(row)
    input : npd 17, nvl 21; output vcu_param_list as float32

    Parameters:

        npd: int
            number of pedal steps
        pedal_range: tuple
            pedal range (0,1)
        nvl: int
            number of velocity steps
        velocity_range: tuple
            speed range (0,120)
        shortcut: int
            1: use segment-wise linear eco calibration table
            2: use init table
            3: use latest pedal map that was used
        data_root: str
            path to data folder

    Return:
        pandas dataframe
    """
    ped = np.linspace(pedal_range[0], pedal_range[1], num=npd)  # 0 - 100% pedal

    if shortcut == 1:
        vel_ = np.linspace(
            velocity_range[0], velocity_range[1], num=nvl - 1
        )  # 0 - 120 kmph velocity
        vel = np.insert(vel_, 1, 7)  # insert 7 kmph, and convert to m/s
        pdv, vlv = np.meshgrid(ped, vel / 3.6, sparse=True)
        v = pdv / (1 + np.sqrt(np.abs(vlv)))
        pd_v = pd.DataFrame(v, columns=ped, index=vel)

    elif shortcut == 2:  # import default eco calibration table
        table_path = data_root.joinpath(
            "vb7_init_table.csv"
        )  # init table is driver independent in the pardir.
        pd_v = pd.read_csv(table_path, header=0, index_col=0)
        # table_path = datafolder + "/54_vertices_approx-regen3.csv"  # init table is driver independent in the pardir.
        # pd_data = pd.read_csv(table_path, header=0, index_col=0)
    elif shortcut == 3:  # import latest pedal map that was used
        files = glob.glob(str(data_root) + "/last_table*.csv")
        if not files:  # files is empty list []
            print("no last table is available. Get init table instead.")
            latest_table = Path(__file__).parent.joinpath(
                "vb7_init_table.csv"
            )  # init table is driver independent in the pardir.
        else:
            latest_table = max(files, key=os.path.getmtime)
        # latest = datafolder + "last_table.csv"  # init table is driver relevant.
        pd_v = pd.read_csv(latest_table, header=0, index_col=0)

    else:
        vel = np.ones(nvl)
        pdv, vlv = np.meshgrid(ped, vel, sparse=False)
        pd_v = pd.DataFrame(pdv, columns=ped, index=vel)
    return pd_v

# %% ../../nbs/03.config.vcu.ipynb 8
def generate_lookup_table(
    pedal_range: tuple, velocity_range: tuple, calib_table: pd.DataFrame
):
    """
    Generate VCU calibration parameters for a given truck.

    pedal in x(col), velocity in y(row)
    input : npd 17, nvl 21; output vcu_param_list as float32

    Parameters:

        pedal_range: tuple
            pedal range (0,1)
        velocity_range: tuple
            speed range (0,120)
        calib_table: pandas dataframe
            calibration table

    Return:

        numpy array
    """
    nvl, npd = calib_table.shape
    p_step = complex(0, npd)
    v_step = complex(0, nvl)
    grid_v, grid_p = np.mgrid[
        velocity_range[0] : velocity_range[1] : v_step,
        pedal_range[0] : pedal_range[1] : p_step,
    ]
    calib_lookup = interpolate.RegularGridInterpolator(
        (grid_p, grid_v), calib_table.to_numpy()
    )
    return calib_lookup

# %% ../../nbs/03.config.vcu.ipynb 11
def test_generate_lookup_table():
    vcu_calib_table_row = 17  # number of pedal steps
    vcu_calib_table_col = 21  # numnber of velocity steps
    pedal_range = [0, 1.0]
    velocity_range = [0, 120.0]
    vcu_calib_table = generate_vcu_calibration(
        npd=vcu_calib_table_row,
        pedal_range=pedal_range,
        nvl=vcu_calib_table_col,
        velocity_range=velocity_range,
        shortcut=1,
        data_root=Path("."),
    )
    vcu_lookup_table = generate_lookup_table(
        pedal_range, velocity_range, vcu_calib_table
    )
    return vcu_lookup_table


def test_generate_vcu_calibration():
    vcu_calib_table_row = 17  # number of pedal steps
    vcu_calib_table_col = 21  # numnber of velocity steps
    pedal_range = [0, 1.0]
    velocity_range = [0, 20.0]
    vcu_calib_table = generate_vcu_calibration(
        npd=vcu_calib_table_row,
        pedal_range=pedal_range,
        nvl=vcu_calib_table_col,
        velocity_range=velocity_range,
        shortcut=1,
        data_root=Path("."),
    )
    return vcu_calib_table
