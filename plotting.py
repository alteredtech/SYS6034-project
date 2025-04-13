import json
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import numpy as np
import random

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

def plot_histograms_by_sim(df, col_name, binwidth=5, save_dir="output"):
    os.makedirs(save_dir, exist_ok=True)
    sims = df['source_file'].unique()

    for sim in sims:
        sim_df = df[df['source_file'] == sim]
        plt.figure(figsize=(8, 5))
        sns.histplot(sim_df[col_name].dropna(), binwidth=binwidth, kde=True)
        plt.title(f"{col_name} distribution - {sim}")
        plt.xlabel(f"{col_name} (minutes)")
        plt.ylabel("Count")
        plt.grid(True)
        plt.tight_layout()
        
        clean_sim_name = sim.replace(".json", "").replace(" ", "_")
        out_path = os.path.join(save_dir, f"histogram_{col_name}_{clean_sim_name}.png")
        plt.savefig(out_path)
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

def fit_and_plot_distributions(df, col_name, save_dir="output", binwidth=5):
    os.makedirs(save_dir, exist_ok=True)
    sims = df['source_file'].unique()

    candidate_distributions = {
        "exponential": stats.expon,
        "weibull": stats.weibull_min,
        "lognorm": stats.lognorm
    }

    for sim in sims:
        sim_df = df[df['source_file'] == sim]
        data = sim_df[col_name].dropna()
        if data.empty:
            continue

        # Histogram base
        plt.figure(figsize=(8, 5))
        sns.histplot(data, binwidth=binwidth, stat="density", label="Empirical", color="lightgray", edgecolor="black")

        x = np.linspace(data.min(), data.max(), 200)
        best_fit = None
        best_sse = float("inf")

        for name, dist in candidate_distributions.items():
            try:
                params = dist.fit(data)
                pdf = dist.pdf(x, *params)
                sse = np.sum((stats.gaussian_kde(data)(x) - pdf) ** 2)

                plt.plot(x, pdf, label=f"{name} (SSE={sse:.2e})")

                if sse < best_sse:
                    best_fit = (name, params)
                    best_sse = sse
            except Exception as e:
                print(f"Could not fit {name} for {sim}: {e}")

        # Annotate best fit
        if best_fit:
            plt.title(f"{col_name} Fit - {sim}\nBest fit: {best_fit[0]} (SSE={best_sse:.2e})")
        else:
            plt.title(f"{col_name} Fit - {sim} (No valid fit)")

        plt.xlabel(f"{col_name} (minutes)")
        plt.ylabel("Density")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        out_path = os.path.join(save_dir, f"fit_{col_name}_{sim.replace('.json','').replace(' ','_')}.png")
        plt.savefig(out_path)
        plt.close()

def compare_to_truncated_exponential(df, col_name, lam, save_dir="output", binwidth=30):
    os.makedirs(save_dir, exist_ok=True)

    for sim in df['source_file'].unique():
        sim_df = df[df['source_file'] == sim]
        real_data = sim_df[col_name].dropna()

        if real_data.empty:
            continue

        # Simulate truncated exponential
        sim_data = truncated_exponential_sample(len(real_data), lam)

        # Plot both
        plt.figure(figsize=(8, 5))
        sns.histplot(real_data, stat="density", binwidth=binwidth, label="Empirical", color="skyblue", edgecolor="black")
        sns.histplot(sim_data, stat="density", binwidth=binwidth, label="Simulated Trunc Exp", color="tomato", alpha=0.4)

        plt.title(f"{col_name} vs Truncated Exp - {sim}")
        plt.xlabel(f"{col_name} (minutes)")
        plt.ylabel("Density")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        out_path = os.path.join(save_dir, f"compare_trunc_exp_{col_name}_{sim.replace('.json','')}.png")
        plt.savefig(out_path)
        plt.close()

def hourly_arrival_count(df, event_filter="arrival", save_dir="output"):
    os.makedirs(save_dir, exist_ok=True)

    for sim in df['source_file'].unique():
        sim_df = df[df['source_file'] == sim]

        # Optional: filter for only relevant events
        if event_filter:
            sim_df = sim_df[sim_df['event'] == event_filter]

        # Count events by (day, hour)
        grouped = sim_df.groupby(["day", "sim_hour"]).size().reset_index(name="count")

        # Pivot for heatmap
        pivot = grouped.pivot(index="day", columns="sim_hour", values="count").fillna(0)

        # Plot heatmap
        plt.figure(figsize=(12, 6))
        sns.heatmap(pivot, cmap="Blues", annot=True, fmt=".0f", cbar_kws={"label": "Arrival Count"})
        if event_filter:
            plt.title(f"Hourly {event_filter.capitalize()} Counts - {sim}")
        else:
            plt.title(f"Hourly Arrivals by Day - {sim}")
        plt.xlabel("Hour of Day")
        plt.ylabel("Simulation Day")
        plt.tight_layout()

        clean_name = sim.replace(".json", "")
        plt.savefig(os.path.join(save_dir, f"arrivals_by_day_hour_{clean_name}.png"))
        plt.close()

def plot_density_histograms_by_sim(df, col_name, binwidth=5, save_dir="output"):
    os.makedirs(save_dir, exist_ok=True)
    sims = df['source_file'].unique()

    for sim in sims:
        sim_df = df[df['source_file'] == sim]
        data = sim_df[col_name].dropna()

        if data.empty:
            continue

        plt.figure(figsize=(8, 5))
        sns.histplot(data, binwidth=binwidth, stat="density", kde=True)
        plt.title(f"Density of {col_name} - {sim}")
        plt.xlabel(f"{col_name} (minutes)")
        plt.ylabel("Density")
        plt.grid(True)
        plt.tight_layout()

        clean_sim_name = sim.replace(".json", "").replace(" ", "_")
        out_path = os.path.join(save_dir, f"density_{col_name}_{clean_sim_name}.png")
        plt.savefig(out_path)
        plt.close()

def calculate_poisson_rates(df):
    results = []
    for sim in df['source_file'].unique():
        sim_df = df[df['source_file'] == sim]

        mean_arrival_time = sim_df['return_delay'].dropna().mean() / 60 # Convert to hours
        mean_service_time = sim_df['charging_time'].dropna().mean() / 60 # Convert to hours

        lambda_rate = 1 / mean_arrival_time if mean_arrival_time else None
        mu_rate = 1 / mean_service_time if mean_service_time else None

        results.append({
            'simulation': sim,
            'mean_return_delay (hr)': mean_arrival_time,
            'mean_charging_time (hr)': mean_service_time,
            'lambda (arrivals/hr)': lambda_rate,
            'mu (services/hr)': mu_rate,
            "rho (utilization)": lambda_rate / mu_rate if lambda_rate and mu_rate else None,
        })
    
    results_df = pd.DataFrame(results)
    results_df.to_csv(os.path.join("logs", "poisson_rates_summary.csv"), index=False)
    return results_df

if __name__ == "__main__":
    df = load_logs()
    print(f"Loaded {len(df)} logs from {len(df['source_file'].unique())} files.")
    df = unpack_extra(df)
    print(df.columns.tolist())
    print(df.head())
    # Plot histograms
    plot_histograms_by_sim(df, 'return_delay', binwidth=5)
    plot_histograms_by_sim(df, 'charging_time', binwidth=30)
    # Fit and plot distributions
    fit_and_plot_distributions(df, 'return_delay', binwidth=5)
    fit_and_plot_distributions(df, 'charging_time', binwidth=30)
    # Compare to truncated exponential
    compare_to_truncated_exponential(df, col_name="return_delay", lam=10.375, binwidth=30)
    # Hourly arrival counts
    hourly_arrival_count(df, event_filter="requesting charger")
    rate_summary = calculate_poisson_rates(df)
    
    print(rate_summary)