from typing import List
import argparse
import numpy as np
import time

from Simulator import Simulator, StrategyOrder
from ModelClasses import PVInstallation, EVInstallation, Heatpump, Battery
import time
from Vizualizer import Vizualizer
import constants

TIME_STEP_SECONDS = constants.TIME_STEP_SECONDS

# Renewable share threshold set based on ____________
HIGH_REN_THRESHOLD = 0.6
LOW_REN_THRESHOLD = 0.4

def pv_strategy(time_step : int, temperature_data : np.ndarray, renewable_share : np.ndarray, pv : PVInstallation):
    """
    Implement a nice pv strategy here

    Do this by setting a value for pv.consumption[time_step]
    This value should be <= 0
    """

    # Example 1: fully curtail the PV
    # pv.consumption[time_step] = 0.0

    # Example 2: no curtailment, generate the max power
    pv.consumption[time_step] = pv.max_power[time_step]

def ev_strategy(time_step : int, temperature_data : np.ndarray, renewable_share : np.ndarray, ev : EVInstallation):
    """
    Implement a nice ev strategy here!

    Do this by setting a value for ev.consumption[time_step]
    This value should be >= 0
    """

    # Example 1: charge as fast as technically possible
    ev.consumption[time_step] = ev.max

    # Example 2: try to reach max state of charge during the session. Divide the load over the available time
    """
    session_nr = int(ev.session[time_step])
    required_energy = ev.size  # always charge to 100% SoC
    energy_to_charge = max(0, required_energy - ev.energy)  # in kWh
    time_to_charge = (ev.session_leave[session_nr] - time_step) * TIME_STEP_SECONDS / 3600  # in hours
    ev.consumption[time_step] = min(ev.power_max, energy_to_charge / time_to_charge)
    """

def hp_strategy(time_step : int, temperature_data : np.ndarray, renewable_share : np.ndarray, hp : Heatpump):
    """
    Implement a nice hp strategy here!

    Do this by setting a value for hp.consumption[time_step]
    This value should be >= 0
    """
    # Example 1: Consume power such that the house temperature is kept at the set point and such that the tank
    # is heated as much as possible
    """
    hp.consumption[time_step] = hp.max  # convert to kW
    """

    # Example 2 : Consume power such that the house temperature is kept at the set point and such that the tank
    # temperature does not reach below its set point
    # All these calculations are in SI units, that is: Kelvin, Joule, and seconds
    T_ambient = temperature_data[time_step]

    # Calculate the amount of heat needed to keep the house temperature constant at the set point
    heat_demand_house = hp.calculate_heat_demand_house(time_step, hp.T_set)

    # Calculate whether the tank temperature will reach below its set point if the house is heated
    tank_T_difference_no_hp = heat_demand_house / (hp.tank_mass * hp.heat_capacity_water)
    tank_T_no_hp = hp.tank_T - tank_T_difference_no_hp

    if tank_T_no_hp > hp.tank_T_set:
        heat_power_to_tank = 0.0  # No heat needed for the tank
    else:
        # supply up to set point if possible
        heat_to_tank = hp.tank_mass * hp.heat_capacity_water * (hp.tank_T_set - tank_T_no_hp) + heat_demand_house
        heat_power_to_tank = min(hp.nominal_power, heat_to_tank / TIME_STEP_SECONDS)

    # Convert the heating power to electrical power using the Coefficient of Performance
    power = heat_power_to_tank / hp.cop(hp.tank_T_set, T_ambient)
    hp.consumption[time_step] = power / 1000.0  # convert to kW

def batt_strategy(time_step : int, temperature_data : np.ndarray, renewable_share : np.ndarray, batt : Battery):
    """
    Implement a nice battery strategy here

    Do this by setting a value for batt.consumption[time_step]
    This value cam be smaller (discharging) or greater (charging) than 0
    """

    # Example: do nothing, determine the consumption of the battery in the house strategy
    # pass

    # Default to 0; neighborhood_strategy will override in centralized,
    # house_strategy will override in decentralized.
    batt.consumption[time_step] = 0.0

def house_strategy(time_step : int, temperature_data : np.ndarray, renewable_share : np.ndarray, base_data : np.ndarray,
                   pv : PVInstallation, ev : EVInstallation, batt : Battery, hp : Heatpump):
    """
    Implement a nice house strategy here

    Do this by setting one or more of the following values:
    - pv.consumption[time_step]
    - ev.consumption[time_step]
    - hp.consumption[time_step]
    - batt.consumption[time_step]
    """

    ## YKA
    ## Decentralized Strategy logic: Each house manages its own battery based on its own net load
    house_load = base_data[time_step] + pv.consumption[time_step] + ev.consumption[time_step] + hp.consumption[time_step]
    if house_load <= 0: # if the combined load is negative, charge the battery
        batt.consumption[time_step] = min(-house_load, batt.max)
    else: # discharge the battery otherwise
        batt.consumption[time_step] = max(-house_load, batt.min)

def neighborhood_strategy(time_step, temperature_data : np.ndarray, renewable_share : np.ndarray, baseloads : np.ndarray,
                          pvs : List[PVInstallation], evs : List[EVInstallation], hps : List[Heatpump], batteries : List[Battery]):
    """
    Implement a nice neighborhood strategy here

    Do this by setting on or more of the following values for the assets in pvs, evs, hps, and batteries
    - pv.consumption[time_step] for pv in pvs
    - ev.consumption[time_step] for ev in evs
    - hp.consumption[time_step] for hp in hps
    - batt.consumption[time_step] for batt in batteries
    """

    ## YKA
    ## Centralized Strategy logic: Batteries are chared based on neighborhood totals and 
    ## are charged from the grid when the national renewable share is is high

    n = len(batteries)
    
    # Total neighborhood net load excluding batteries 
    total_net_load = sum(
        baseloads[i][time_step] + pvs[i].consumption[time_step] + evs[i].consumption[time_step] + hps[i].consumption[time_step]
        for i in range(n)
    )

    ren = renewable_share[time_step]


    # When there is no local generation, charge batteries if there is
    # a high renewable share on the national grid 
    if total_net_load < 0:
        # Local PV surplus: charge batteries
        target = -total_net_load
        for batt in batteries:
            charge = min(target, batt.max)
            batt.consumption[time_step] = charge
            target -= charge
            if target <= 0:
                break
    elif ren >= HIGH_REN_THRESHOLD:
        # High renewable share on grid: charge batteries from grid
        for batt in batteries:
            batt.consumption[time_step] = batt.max
    elif ren <= LOW_REN_THRESHOLD:
        # Low renewable share: discharge batteries to reduce import
        target = total_net_load
        for batt in batteries:
            discharge = min(target, -batt.min)  # batt.min is negative
            batt.consumption[time_step] = -discharge
            target -= discharge
            if target <= 0:
                break
    # else: do nothing (batteries stay at 0 from batt_strategy)

def main():
    """
    Run this function to start a simulation
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("control_strategy", choices=["centralized", "decentralized"])
    args = parser.parse_args()
    control_strategy = args.control_strategy

    # Set up simulation
    number_of_houses = 100  # <= 100
    amount_of_days_to_simulate = 364  # <= 364
    sim_length = amount_of_days_to_simulate * constants.AMOUNT_OF_TIME_STEPS_IN_DAY

    if control_strategy == "centralized":
        strategy_order = [StrategyOrder.INDIVIDUAL, StrategyOrder.NEIGHBORHOOD]
    else:
        strategy_order = [StrategyOrder.INDIVIDUAL, StrategyOrder.HOUSEHOLD]

    simulator = Simulator(control_order=strategy_order,
                          battery_strategy=batt_strategy, 
                          hp_strategy=hp_strategy, 
                          pv_strategy=pv_strategy, 
                          ev_strategy=ev_strategy, 
                          neighborhood_strategy=neighborhood_strategy, 
                          house_strategy=house_strategy)
    simulator.initialize(sim_length, number_of_houses, "data/data.pkl", "data/reference_load.npy")

    # Run Simulation
    start_time = time.time()
    print("Start simulation")
    simulator.start_simulation()
    print("finished simulation")
    print(f'Duration: {time.time() - start_time} seconds')
    
    # Show Results
    vizualizer = Vizualizer(sim_length, control_strategy)
    vizualizer.plot_results_reference_and_total_load(simulator.reference_load, simulator.total_load)
    vizualizer.print_metrics_renewable_share_total_load(simulator.ren_share, simulator.total_load)

    # Additional metrics
    total_pv = np.sum(np.array([pv.consumption.astype(float) for pv in simulator.pvs]), axis=0)
    pv_generated = -total_pv  # positive kW
    ren_s = simulator.ren_share[:sim_length]
    total_load = simulator.total_load
    grid_import = np.maximum(total_load, 0.0)
    grid_export = np.maximum(-total_load, 0.0)
    local_pv_used = np.maximum(0.0, pv_generated - grid_export)
    total_cons = local_pv_used + grid_import
    ren_consumed = local_pv_used + ren_s * grid_import
    print(f"\nMETRICS ({control_strategy.upper()} CONTROL):")
    print(f"  Renewable share of consumption: {np.sum(ren_consumed) / np.sum(total_cons) * 100:.2f}%")
    print(f"  Local PV absorption:            {np.sum(local_pv_used) / np.sum(pv_generated) * 100:.2f}%")
    print(f"  Grid import share:              {np.sum(grid_import) / np.sum(total_cons) * 100:.2f}%")

if __name__ == '__main__':
    exit(main())
