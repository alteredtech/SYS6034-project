import json
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

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

def plot_histograms_by_sim(df, col_name, binwidth=5):
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
        plt.savefig(f"histogram_{col_name}_{sim}.png")

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
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    df = load_logs()
    print(f"Loaded {len(df)} logs from {len(df['source_file'].unique())} files.")
    df = unpack_extra(df)
    print(df.columns.tolist())
    plot_histograms_by_sim(df, 'return_delay', binwidth=30)
    plot_histograms_by_sim(df, 'charging_time', binwidth=30)
    rate_summary = calculate_poisson_rates(df)
    print(rate_summary)