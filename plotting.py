import json
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import numpy as np
import random
import math
from scipy.stats import kstest
from collections import defaultdict

def load_logs(log_directory="logs"):
    log_files = [f for f in os.listdir(log_directory) if f.endswith("_logs.json")]
    all_logs = []

    for file in log_files:
        with open(os.path.join(log_directory, file), 'r') as f:
            logs = json.load(f)
            for log in logs:
                log["source_file"] = file
            all_logs.extend(logs)

    return pd.DataFrame(all_logs)

def unpack_extra(df):
    extra_df = df['extra'].dropna().apply(pd.Series)
    df = pd.concat([df.drop(columns=['extra']), extra_df], axis=1)
    return df

def plot_histograms_by_sim_combined_avg_by_scenario(df, col_name, binwidth=5, save_dir="output"):
    os.makedirs(save_dir, exist_ok=True)

    scenario_groups = defaultdict(list)
    for sim in df['source_file'].unique():
        base = sim.split("_run")[0]  # customize as needed
        scenario_groups[base].append(sim)
    
    num_sims = len(scenario_groups)

    cols = 2
    rows = math.ceil(num_sims / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 4), squeeze=False)

    for idx, (scenario, files) in enumerate(scenario_groups.items()):
        combined_df = df[df['source_file'].isin(files)]
        data = combined_df[col_name].dropna()
        ax = axes[idx // cols][idx % cols]

        if data.empty:
            ax.set_visible(False)
            continue

        sns.histplot(data, binwidth=binwidth, kde=True, ax=ax)
        ax.set_title(f"{col_name} - {scenario} (Avg of {len(files)} runs)")
        ax.set_xlabel(f"{col_name} (minutes)")
        ax.set_ylabel("Count")
        ax.grid(True)

    # Hide unused axes
    for i in range(num_sims, rows * cols):
        fig.delaxes(axes[i // cols][i % cols])

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, f"combined_{col_name}_histograms.png"))
    plt.close()

def truncated_exponential_sample(size, lam, low=0, high=2880):
    """
    Generate `size` samples from a truncated exponential distribution,
    bounded between `low` and `high` (in minutes).
    """
    samples = []
    while len(samples) < size:
        sample = random.expovariate(1 / lam) 
        sample = sample * 60
        if low <= sample <= high:  # Truncate to 48 hours
            samples.append(sample)
    return np.array(samples)

def fit_and_plot_distributions_combined_avg_by_scenario(df, col_name, save_dir="output", binwidth=5):
    os.makedirs(save_dir, exist_ok=True)

    scenario_groups = defaultdict(list)
    for sim in df['source_file'].unique():
        base = sim.split("_run")[0]  # Customize if your filenames differ
        scenario_groups[base].append(sim)

    scenarios = list(scenario_groups.keys())
    cols = 2
    rows = math.ceil(len(scenarios) / cols)

    candidate_distributions = {
        "exponential": stats.expon,
        "weibull": stats.weibull_min,
        "lognorm": stats.lognorm
    }

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 4), squeeze=False)

    for idx, scenario in enumerate(scenarios):
        group_df = df[df['source_file'].isin(scenario_groups[scenario])]
        data = group_df[col_name].dropna()
        ax = axes[idx // cols][idx % cols]

        if data.empty:
            ax.set_visible(False)
            continue

        sns.histplot(data, binwidth=binwidth, stat="density", label="Empirical", color="lightgray", edgecolor="black", ax=ax)
        x = np.linspace(data.min(), data.max(), 200)

        best_fit = None
        best_pval = -1  # For selecting the best distribution
        best_d = float("inf")

        for name, dist in candidate_distributions.items():
            try:
                params = dist.fit(data)
                D, p_val = kstest(data, dist.cdf, args=params)
                pdf = dist.pdf(x, *params)
                ax.plot(x, pdf, label=f"{name} (D={D:.3f}, p={p_val:.3f})")

                if p_val > best_pval or (p_val == best_pval and D < best_d):
                    best_fit = (name, params)
                    best_pval = p_val
                    best_d = D

            except Exception as e:
                print(f"Could not fit {name} for {scenario}: {e}")

        if best_fit:
            ax.set_title(f"{scenario}\nBest Fit (K-S): {best_fit[0]} (p={best_pval:.3f})")
        else:
            ax.set_title(f"{scenario} (No valid fit)")

        ax.set_xlabel(f"{col_name} (minutes)")
        ax.set_ylabel("Density")
        ax.grid(True)
        ax.legend(fontsize="small")

    for i in range(len(scenarios), rows * cols):
        fig.delaxes(axes[i // cols][i % cols])

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, f"avg_combined_{col_name}_fit_distributions.png"))
    plt.close()

def compare_to_truncated_exponential_avg_by_scenario(df, col_name, lam, binwidth=30, save_dir="output"):
    os.makedirs(save_dir, exist_ok=True)

    # Group files by scenario (e.g., simulation_1 from simulation_1_run_1.json, etc.)
    scenario_groups = defaultdict(list)
    for sim in df['source_file'].unique():
        base = sim.split("_run")[0]  # adjust if you use _trial or _seed
        scenario_groups[base].append(sim)

    scenarios = list(scenario_groups.keys())
    cols = 2
    rows = math.ceil(len(scenarios) / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 4), squeeze=False)

    for idx, scenario in enumerate(scenarios):
        group_df = df[df['source_file'].isin(scenario_groups[scenario])]
        real_data = group_df[col_name].dropna()
        ax = axes[idx // cols][idx % cols]

        if real_data.empty:
            ax.set_visible(False)
            continue

        # Simulate truncated exponential with same sample size
        sim_data = truncated_exponential_sample(len(real_data), lam)

        # Plot both
        sns.histplot(real_data, stat="density", binwidth=binwidth, label="Empirical", color="skyblue", edgecolor="black", ax=ax)
        sns.histplot(sim_data, stat="density", binwidth=binwidth, label="Truncated Exp", color="tomato", alpha=0.4, ax=ax)

        ax.set_title(f"{scenario}\nEmpirical vs. Truncated Exp")
        ax.set_xlabel(f"{col_name} (minutes)")
        ax.set_ylabel("Density")
        ax.grid(True)
        ax.legend(fontsize="small")

    for i in range(len(scenarios), rows * cols):
        fig.delaxes(axes[i // cols][i % cols])

    plt.tight_layout()
    out_path = os.path.join(save_dir, f"avg_combined_{col_name}_compare_trunc_exp.png")
    plt.savefig(out_path)
    plt.close()

def hourly_arrival_count_avg_by_scenario(df, event_filter="arrival", save_dir="output"):
    os.makedirs(save_dir, exist_ok=True)

    scenario_groups = defaultdict(list)
    for sim in df['source_file'].unique():
        base = sim.split("_run")[0]  # Customize if your filenames vary
        scenario_groups[base].append(sim)

    scenarios = list(scenario_groups.keys())
    cols = 2
    rows = math.ceil(len(scenarios) / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 4), squeeze=False)

    for idx, scenario in enumerate(scenarios):
        sim_df = df[df['source_file'].isin(scenario_groups[scenario])]
        if event_filter:
            sim_df = sim_df[sim_df['event'] == event_filter]

        # Count arrivals per (day, hour)
        grouped = sim_df.groupby(["day", "sim_hour"]).size().reset_index(name="count")

        # Pivot to heatmap-friendly format
        pivot = grouped.pivot(index="day", columns="sim_hour", values="count").fillna(0)

        ax = axes[idx // cols][idx % cols]
        sns.heatmap(pivot, cmap="Blues", ax=ax, cbar=False, annot=True, fmt=".0f")

        ax.set_title(f"{scenario}\nHourly {event_filter.capitalize()} Counts")
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Simulation Day")

    # Hide empty subplots
    for i in range(len(scenarios), rows * cols):
        fig.delaxes(axes[i // cols][i % cols])

    plt.tight_layout()
    out_path = os.path.join(save_dir, f"avg_hourly_arrivals_{event_filter}.png")
    plt.savefig(out_path)
    plt.close()

def erlang_c(scenario, lambda_rate, mu_rate, chargers = 4):
    output_data = {}
    for c in range(1, chargers + 1):
        a = lambda_rate / mu_rate  # Offered load
        rho = a / c

        # Denominator of Erlang C
        sum_terms = sum([(a ** k) / math.factorial(k) for k in range(c)])
        last_term = (a ** c) / (math.factorial(c) * (1 - rho))
        denom = sum_terms + last_term

        # Erlang C probability of waiting
        pw = last_term / denom

        # Expected waiting time in queue
        ewq = pw / (c * mu_rate - lambda_rate)
        ew = ewq + 1 / mu_rate

        results = {
            "lambda_rate": lambda_rate,
            "mu_rate": mu_rate,
            "c": c,
            "ErlangC_Prob_Wait": pw,
            "E[Wq] (hrs)": ewq,
            "E[W_total] (hrs)": ew,
            "Utilization": rho
        }
        output_data[f"c_{c}"] = results

    # Save to output folder
    os.makedirs("output", exist_ok=True)
    output_file = os.path.join("output", f"{scenario}_erlang_c_results.json")
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=4)

def calculate_poisson_rates_avg_by_scenario(df, save_dir="logs"):
    os.makedirs(save_dir, exist_ok=True)
    scenario_groups = defaultdict(list)
    for sim in df['source_file'].unique():
        base = sim.split("_run")[0]  # Customize as needed
        scenario_groups[base].append(sim)

    results = []
    for scenario, runs in scenario_groups.items():

        # Per-run rates (for optional CI/stats later)
        run_stats = []

        for sim in runs:
            sub_df = df[df['source_file'] == sim]
            mean_arrival_time = sub_df['return_delay'].dropna().mean() / 60  # hours
            mean_service_time = sub_df['charging_time'].dropna().mean() / 60  # hours

            lambda_rate = 1 / mean_arrival_time if mean_arrival_time else None
            mu_rate = 1 / mean_service_time if mean_service_time else None
            rho = lambda_rate / mu_rate if lambda_rate and mu_rate else None

            run_stats.append((lambda_rate, mu_rate, rho))

        # Aggregate: remove Nones before computing mean
        lambda_values = [x[0] for x in run_stats if x[0] is not None]
        mu_values = [x[1] for x in run_stats if x[1] is not None]
        rho_values = [x[2] for x in run_stats if x[2] is not None]

        # Calculate mean rates
        lambda_mean = sum(lambda_values) / len(lambda_values) if lambda_values else None
        lambda_rate_mean = 1 / (sum(lambda_values) / len(lambda_values)) if lambda_values else None
        mu_mean = sum(mu_values) / len(mu_values) if mu_values else None
        mu_rate_mean = 1 / (sum(mu_values) / len(mu_values)) if mu_values else None
        rho_mean = sum(rho_values) / len(rho_values) if rho_values else None
        # Calculate Erlang C
        erlang_c(scenario=scenario, lambda_rate=lambda_rate_mean, mu_rate=mu_rate_mean, chargers=4)

        results.append({
            "scenario": scenario,
            "mean_lambda (1/lambda) (arrivals/hr)": lambda_mean,
            "mean_lambda_rate (arrivals/hrs)": lambda_rate_mean,
            "mean_mu (services/hr)": mu_mean,
            "mean_mu_rate (services/hrs)": mu_rate_mean,
            "mean_rho (utilization)": rho_mean,
            "n_runs": len(runs)
        })

    results_df = pd.DataFrame(results)
    out_path = os.path.join(save_dir, "poisson_rates_summary_avg.csv")
    results_df.to_csv(out_path, index=False)
    return results_df

if __name__ == "__main__":
    df = load_logs()
    print(f"Loaded {len(df)} logs from {len(df['source_file'].unique())} files.")
    df = unpack_extra(df)
    
    # Plot histograms
    plot_histograms_by_sim_combined_avg_by_scenario(df, 'return_delay', binwidth=5)
    plot_histograms_by_sim_combined_avg_by_scenario(df, 'charging_time', binwidth=30)
    # Fit and plot distributions
    fit_and_plot_distributions_combined_avg_by_scenario(df, 'return_delay', binwidth=5)
    fit_and_plot_distributions_combined_avg_by_scenario(df, 'charging_time', binwidth=30)
    # Compare to truncated exponential
    compare_to_truncated_exponential_avg_by_scenario(df, col_name="return_delay", lam=10.375, binwidth=30)
    # Hourly arrival counts
    hourly_arrival_count_avg_by_scenario(df, event_filter="requesting charger")
    rate_summary = calculate_poisson_rates_avg_by_scenario(df)
    
    print(rate_summary)