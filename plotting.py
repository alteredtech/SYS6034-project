import json
import os
import pandas as pd
import matplotlib.pyplot as plt

def load_all_simulations(log_dir):
    all_logs = []
    for file in os.listdir(log_dir):
        if file.endswith("logs.json"):
            with open(os.path.join(log_dir, file), "r") as f:
                data = json.load(f)
                df = pd.json_normalize(data)
                df["simulation"] = file.replace(".json", "")
                all_logs.append(df)
    return pd.concat(all_logs, ignore_index=True)

def preprocess_logs(df):
    df = df[df["event"].notna()]
    df = df[df["event"].isin(["requesting charger", "starts charging", "charging"])]
    df["time"] = pd.to_numeric(df["time"], errors="coerce")
    df = df.dropna(subset=["time"])
    return df

def compute_metrics(df):
    sims = []
    for sim_id, group in df.groupby("simulation"):
        starts = group[group["event"] == "starts charging"]
        requests = group[group["event"] == "requesting charger"]

        merged = pd.merge(
            requests[["ev_id", "time", "day"]],
            starts[["ev_id", "time"]],
            on="ev_id",
            suffixes=("_request", "_start")
        )
        merged["wait_time"] = merged["time_start"] - merged["time_request"]
        merged["hour_request"] = merged["time_request"] / 60

        charging_events = group[group["event"] == "charging"].copy()
        charging_events["charging_time"] = charging_events["extra"].apply(lambda x: x.get("charging_time") if isinstance(x, dict) else None)
        charging_events = charging_events.dropna(subset=["charging_time"])

        lambda_est = len(merged) / (merged["hour_request"].max() - merged["hour_request"].min())
        mu_est = 1 / charging_events["charging_time"].mean() * 60 if not charging_events.empty else 0
        utilization = lambda_est / mu_est if mu_est > 0 else float('nan')

        sims.append({
            "simulation": sim_id,
            "lambda_per_hour": lambda_est,
            "mu_per_hour": mu_est,
            "utilization": utilization,
            "wait_times": merged["wait_time"].tolist(),
            "charging_times": charging_events["charging_time"].tolist(),
            "queue_lengths": group[group["event"] == "requesting charger"]["extra"].apply(lambda x: x.get("queue_length") if isinstance(x, dict) else None).dropna().tolist()
        })
    return sims

def plot_metrics(sims):
    for metric in ["wait_times", "charging_times", "queue_lengths"]:
        plt.figure(figsize=(10, 6))
        for sim in sims:
            plt.hist(sim[metric], bins=30, alpha=0.6, label=sim["simulation"])
        plt.title(f"Histogram of {metric.replace('_', ' ').title()}")
        plt.xlabel("Minutes")
        plt.ylabel("Frequency")
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"histogram_{metric}.png")

    df_summary = pd.DataFrame(sims)
    df_summary.plot(x="simulation", y=["lambda_per_hour", "mu_per_hour", "utilization"], kind="bar", figsize=(10, 6))
    plt.title("Simulation-level Metrics")
    plt.ylabel("Events per Hour / Utilization")
    plt.tight_layout()
    plt.savefig("Utilization.png")

if __name__ == "__main__":
    log_dir = "logs"
    all_logs = load_all_simulations(log_dir)
    preprocessed_logs = preprocess_logs(all_logs)
    metrics = compute_metrics(preprocessed_logs)
    plot_metrics(metrics)