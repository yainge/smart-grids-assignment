import matplotlib.pyplot as plt
import numpy as np

import constants

class Vizualizer:

    def __init__(self, sim_length, mode) -> None:
        self.sim_length = sim_length
        self.mode = mode

    def plot_results_reference_and_total_load(self, reference_load : np.ndarray, total_load : np.ndarray):
        """
        Creates two plots:
        - The total load of the neighborhood over time, compared with a reference
        - The normalized daily profile of the neighborhood, compared with a reference

        Feel free to include more plots if you want
        """

        # Plot total calculated load and the reference load
        reference_load = reference_load[0:self.sim_length]
        plt.figure(figsize=(12, 5))
        #plt.plot(reference_load, label="Reference", linewidth=1)
        plt.plot(total_load, label=f"({self.mode} control)", linewidth=1)
        plt.title(f"Total Load Neighborhood ({self.mode} control)")
        plt.xlabel("PTU [-]")
        plt.ylabel("Power [kW]")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"figures/{self.mode}_total_load.png", dpi=150, bbox_inches="tight")
        plt.close()
     
        # Plot Average daily profile
        amount_of_time_steps_in_day = constants.AMOUNT_OF_TIME_STEPS_IN_DAY
        time_step_seconds = constants.TIME_STEP_SECONDS
        step_hours = time_step_seconds / 3600

        n_days = self.sim_length // amount_of_time_steps_in_day

        total_daily = total_load[:n_days * amount_of_time_steps_in_day].reshape(n_days, amount_of_time_steps_in_day)
        ref_daily = reference_load[:n_days * amount_of_time_steps_in_day].reshape(n_days, amount_of_time_steps_in_day)

        avg_total_daily = np.mean(total_daily, axis=0)
        avg_ref_daily = np.mean(ref_daily, axis=0)

        # normalize both by same max value for comparison
        max_val = max(np.max(avg_total_daily), np.max(avg_ref_daily))
        avg_total_daily_norm = avg_total_daily / max_val
        avg_ref_daily_norm = avg_ref_daily / max_val

        hours = np.arange(amount_of_time_steps_in_day) * step_hours

        plt.figure(figsize=(10, 5))
        #plt.plot(hours, avg_ref_daily_norm, label="Reference", linewidth=2)
        plt.plot(hours, avg_total_daily_norm, label=f"({self.mode} control)", linewidth=2)
        plt.title(f"Normalized Average Daily Power Profile ({self.mode} control)")
        plt.xlabel("Hour of day [-]")
        plt.ylabel("Relative Power [-]")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"figures/{self.mode}_daily_profile.png", dpi=150, bbox_inches="tight")
        plt.close()
        
    @staticmethod
    def plot_comparison(reference_load, centralized_load, decentralized_load, sim_length):
        ref = reference_load[:sim_length]
        cent = centralized_load[:sim_length]
        decent = decentralized_load[:sim_length]

        # Total load comparison
        plt.figure(figsize=(12, 5))
        #plt.plot(ref, label="Reference", linewidth=1)
        plt.plot(cent, label="Centralized", linewidth=1)
        plt.plot(decent, label="Decentralized", linewidth=1)
        plt.title("Total Load Neighborhood - Strategy Comparison")
        plt.xlabel("Time [PTU]")
        plt.ylabel("Power [kW]")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("figures/comparison_total_load.png", dpi=150, bbox_inches="tight")
        plt.close()

        # Daily profile comparison
        amount_of_time_steps_in_day = constants.AMOUNT_OF_TIME_STEPS_IN_DAY
        step_hours = constants.TIME_STEP_SECONDS / 3600
        n_days = sim_length // amount_of_time_steps_in_day

        def avg_daily(load):
            return np.mean(load[:n_days * amount_of_time_steps_in_day].reshape(n_days, amount_of_time_steps_in_day), axis=0)

        avg_ref = avg_daily(ref)
        avg_cent = avg_daily(cent)
        avg_decent = avg_daily(decent)
        max_val = max(np.max(avg_ref), np.max(avg_cent), np.max(avg_decent))

        hours = np.arange(amount_of_time_steps_in_day) * step_hours
        plt.figure(figsize=(10, 5))
        #plt.plot(hours, avg_ref / max_val, label="Reference", linewidth=2)
        plt.plot(hours, avg_cent / max_val, label="Centralized", linewidth=2)
        plt.plot(hours, avg_decent / max_val, label="Decentralized", linewidth=2)
        plt.title("Normalized Average Daily Power Profile - Strategy Comparison")
        plt.xlabel("Hour of day [-]")
        plt.ylabel("Relative Power [-]")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("figures/comparison_daily_profile.png", dpi=150, bbox_inches="tight")
        plt.close()

    @staticmethod
    def plot_metrics_comparison(centralized_metrics, decentralized_metrics):
        labels = ["Renewable Share\nof Supplied Electricity", "Local PV\nAbsorption", "Grid Import Share\nof Supplied Electricity"]
        cent_vals = [
            centralized_metrics["renewable_share"],
            centralized_metrics["local_pv_absorption"],
            centralized_metrics["grid_import_share"],
        ]
        decent_vals = [
            decentralized_metrics["renewable_share"],
            decentralized_metrics["local_pv_absorption"],
            decentralized_metrics["grid_import_share"],
        ]

        x = np.arange(len(labels))
        width = 0.35

        _, ax = plt.subplots(figsize=(9, 5))
        bars_cent = ax.bar(x - width / 2, cent_vals, width, label="Centralized")
        bars_decent = ax.bar(x + width / 2, decent_vals, width, label="Decentralized")

        ax.set_ylabel("Percentage [%]")
        ax.set_title("Strategy Comparison - Key Metrics")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        ax.grid(True, axis="y")

        for bar in bars_cent:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=9)
        for bar in bars_decent:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=9)

        plt.tight_layout()
        plt.savefig("figures/comparison_metrics.png", dpi=150, bbox_inches="tight")
        plt.close()

    def print_metrics_renewable_share_total_load(self, renewable_share : np.ndarray, total_load : np.ndarray):
        """
        Calculates 3 metrics:
        - Total energy exported to the grid
        - Total energy imported from the grid
        - Percentage of imported energy to be from renewables

        Feel free to include more metrics if you want
        """

        time_step_seconds = constants.TIME_STEP_SECONDS
        ren_share = renewable_share[0: self.sim_length]

        # Calculate metrics
        energy_export = abs(sum(total_load[total_load < 0] * time_step_seconds/ 3600))
        energy_import = sum(total_load[total_load>0] * time_step_seconds/ 3600)
        renewable_import = sum(total_load[total_load > 0] * ren_share[total_load > 0]) * time_step_seconds/ 3600
        renewable_percentage = renewable_import/energy_import * 100

        print("METRICS:")
        print("---------------------------------------")
        print(f"Energy Exported: {energy_export} kWh")
        print(f"Energy Imported: {energy_import} kWh")
        print(f"Share Renewable Energy Imported: {renewable_percentage} %")