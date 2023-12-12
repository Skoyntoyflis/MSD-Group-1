"""
Python model 'SFD_Group.py'
Translated using PySD
"""

from pathlib import Path
import numpy as np

from pysd.py_backend.statefuls import Delay, Integ
from pysd import Component

__pysd_version__ = "3.7.1"

__data = {"scope": None, "time": lambda: 0}

_root = Path(__file__).parent


component = Component()

#######################################################################
#                          CONTROL VARIABLES                          #
#######################################################################

_control_vars = {
    "initial_time": lambda: 0,
    "final_time": lambda: 30,
    "time_step": lambda: 0.015625,
    "saveper": lambda: time_step(),
}


def _init_outer_references(data):
    for key in data:
        __data[key] = data[key]


@component.add(name="Time")
def time():
    """
    Current time of the model.
    """
    return __data["time"]()


@component.add(
    name="FINAL TIME", units="Year", comp_type="Constant", comp_subtype="Normal"
)
def final_time():
    """
    The final time for the simulation.
    """
    return __data["time"].final_time()


@component.add(
    name="INITIAL TIME", units="Year", comp_type="Constant", comp_subtype="Normal"
)
def initial_time():
    """
    The initial time for the simulation.
    """
    return __data["time"].initial_time()


@component.add(
    name="SAVEPER",
    units="Year",
    limits=(0.0, np.nan),
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"time_step": 1},
)
def saveper():
    """
    The frequency with which output is stored.
    """
    return __data["time"].saveper()


@component.add(
    name="TIME STEP",
    units="Year",
    limits=(0.0, np.nan),
    comp_type="Constant",
    comp_subtype="Normal",
)
def time_step():
    """
    The time step for the simulation.
    """
    return __data["time"].time_step()


#######################################################################
#                           MODEL VARIABLES                           #
#######################################################################


@component.add(
    name="Marriage rate",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"societal_factor": 1},
)
def marriage_rate():
    return 0.3 * (1 - societal_factor())


@component.add(
    name="Delay for societal",
    limits=(0.0, 10.0),
    comp_type="Constant",
    comp_subtype="Normal",
)
def delay_for_societal():
    return 0.5


@component.add(
    name="Divorce",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"divorce_rate": 1, "married": 1, "population": 1},
)
def divorce():
    return divorce_rate() * married() / population() * 1000


@component.add(
    name="Societal factor",
    comp_type="Stateful",
    comp_subtype="Delay",
    depends_on={"_delay_societal_factor": 1},
    other_deps={
        "_delay_societal_factor": {
            "initial": {
                "k": 1,
                "population": 1,
                "divorced": 1,
                "delay_for_societal": 1,
            },
            "step": {"k": 1, "population": 1, "divorced": 1, "delay_for_societal": 1},
        }
    },
)
def societal_factor():
    """
    1/(1 + EXP(-K*(Divorced/Population))) Divorced^N/(K^N+Divorced^N) IF THEN ELSE( Divorced/330>0.4, 0.58, 0.48)
    """
    return _delay_societal_factor()


_delay_societal_factor = Delay(
    lambda: 1 / (1 + np.exp(-k() * (divorced() / population()))),
    lambda: delay_for_societal(),
    lambda: 1 / (1 + np.exp(-k() * (divorced() / population()))),
    lambda: 1,
    time_step,
    "_delay_societal_factor",
)


@component.add(
    name="Population",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"unmarried": 1, "married": 1, "divorced": 1},
)
def population():
    return unmarried() + married() + divorced()


@component.add(name="Delay for recovery", comp_type="Constant", comp_subtype="Normal")
def delay_for_recovery():
    return 3


@component.add(
    name="Recovery",
    comp_type="Stateful",
    comp_subtype="Delay",
    depends_on={"_delay_recovery": 1},
    other_deps={
        "_delay_recovery": {
            "initial": {"divorced": 1, "recovery_rate": 1, "delay_for_recovery": 1},
            "step": {"divorced": 1, "recovery_rate": 1, "delay_for_recovery": 1},
        }
    },
)
def recovery():
    return _delay_recovery()


_delay_recovery = Delay(
    lambda: divorced() * recovery_rate(),
    lambda: delay_for_recovery(),
    lambda: divorced() * recovery_rate(),
    lambda: 1,
    time_step,
    "_delay_recovery",
)


@component.add(
    name="Divorced",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_divorced": 1},
    other_deps={
        "_integ_divorced": {"initial": {}, "step": {"divorce": 1, "recovery": 1}}
    },
)
def divorced():
    return _integ_divorced()


_integ_divorced = Integ(
    lambda: divorce() - recovery(), lambda: 30170000.0, "_integ_divorced"
)


@component.add(name="Economic factor", comp_type="Constant", comp_subtype="Normal")
def economic_factor():
    return 0.53333


@component.add(
    name="Unmarried",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_unmarried": 1},
    other_deps={
        "_integ_unmarried": {"initial": {}, "step": {"recovery": 1, "marriage": 1}}
    },
)
def unmarried():
    return _integ_unmarried()


_integ_unmarried = Integ(
    lambda: recovery() - marriage(), lambda: 113761000.0, "_integ_unmarried"
)


@component.add(
    name="K", limits=(-4.0, 4.0, 0.1), comp_type="Constant", comp_subtype="Normal"
)
def k():
    return 1


@component.add(
    name="Marriage",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"marriage_rate": 1, "unmarried": 1},
)
def marriage():
    return marriage_rate() * unmarried()


@component.add(
    name="Married",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_married": 1},
    other_deps={
        "_integ_married": {"initial": {}, "step": {"marriage": 1, "divorce": 1}}
    },
)
def married():
    return _integ_married()


_integ_married = Integ(
    lambda: marriage() - divorce(), lambda: 113295000.0, "_integ_married"
)


@component.add(
    name="Recovery rate", limits=(0.0, 1.0), comp_type="Constant", comp_subtype="Normal"
)
def recovery_rate():
    return 0.3


@component.add(
    name="Divorce rate",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "w_eco": 2,
        "w_soc": 2,
        "education": 1,
        "economic_factor": 1,
        "societal_factor": 1,
    },
)
def divorce_rate():
    return (
        (1 - w_eco() - w_soc()) * education()
        + w_eco() * economic_factor()
        + w_soc() * societal_factor()
    ) / 3


@component.add(name="Education", comp_type="Constant", comp_subtype="Normal")
def education():
    return 0.9


@component.add(
    name="W eco", limits=(0.0, 1.0), comp_type="Constant", comp_subtype="Normal"
)
def w_eco():
    return 0.33


@component.add(
    name="W soc", limits=(0.0, 1.0), comp_type="Constant", comp_subtype="Normal"
)
def w_soc():
    return 0.33
