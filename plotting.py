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
    # Get a list of all files in the specified directory that end with "_logs.json"
    log_files = [f for f in os.listdir(log_directory) if f.endswith("_logs.json")]
    all_logs = []  # Initialize an empty list to store all log entries

    # Iterate over each log file
    for file in log_files:
        # Open the log file and load its contents as JSON
        with open(os.path.join(log_directory, file), 'r') as f:
            logs = json.load(f)
            # Add the source file name to each log entry for traceability
            for log in logs:
                log["source_file"] = file
            # Append all log entries from the current file to the main list
            all_logs.extend(logs)

    # Convert the list of logs into a Pandas DataFrame and return it
    return pd.DataFrame(all_logs)

def unpack_extra(df):
    # Extract the 'extra' column, dropping any rows with missing values, and expand it into separate columns
    extra_df = df['extra'].dropna().apply(pd.Series)
    # Concatenate the original DataFrame (excluding the 'extra' column) with the expanded 'extra' DataFrame
    df = pd.concat([df.drop(columns=['extra']), extra_df], axis=1)
    # Return the modified DataFrame with the additional columns from 'extra'
    return df

def plot_histograms_by_sim_combined_avg_by_scenario(df, col_name, binwidth=5, save_dir="output"):
    # Ensure the output directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Group simulation files by scenario
    scenario_groups = defaultdict(list)
    for sim in df['source_file'].unique():
        base = sim.split("_run")[0]  # Extract the base scenario name from the file name
        scenario_groups[base].append(sim)
    
    # Determine the number of scenarios
    num_sims = len(scenario_groups)

    # Set the number of columns and calculate the required rows for subplots
    cols = 2
    rows = math.ceil(num_sims / cols)

    # Create a figure with subplots
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 4), squeeze=False)

    # Iterate over each scenario and its associated files
    for idx, (scenario, files) in enumerate(scenario_groups.items()):
        # Combine data from all files in the current scenario
        combined_df = df[df['source_file'].isin(files)]
        data = combined_df[col_name].dropna()  # Drop missing values for the column of interest
        ax = axes[idx // cols][idx % cols]  # Select the appropriate subplot axis

        # Skip if there is no data for the current scenario
        if data.empty:
            ax.set_visible(False)  # Hide the subplot if no data is available
            continue

        # Plot the histogram with a kernel density estimate (KDE)
        sns.histplot(data, binwidth=binwidth, kde=True, ax=ax)
        # Set the title and labels for the subplot
        ax.set_title(f"{col_name} - {scenario} (Avg of {len(files)} runs)")
        ax.set_xlabel(f"{col_name} (minutes)")
        ax.set_ylabel("Count")
        ax.grid(True)  # Add a grid for better readability

    # Hide unused subplots if the grid is larger than the number of scenarios
    for i in range(num_sims, rows * cols):
        fig.delaxes(axes[i // cols][i % cols])

    # Adjust layout and save the figure to the specified directory
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, f"combined_{col_name}_histograms.png"))
    plt.close()

def truncated_exponential_sample(size, lam, low=0, high=2880):
    """
    Generate `size` samples from a truncated exponential distribution,
    bounded between `low` and `high` (in minutes).
    """
    samples = []  # Initialize an empty list to store the samples
    while len(samples) < size:  # Continue until the desired number of samples is generated
        sample = random.expovariate(1 / lam)  # Generate a sample from an exponential distribution
        sample = sample * 60  # Convert the sample from hours to minutes
        if low <= sample <= high:  # Check if the sample falls within the specified bounds
            samples.append(sample)  # Add the valid sample to the list
    return np.array(samples)  # Convert the list of samples to a NumPy array and return it

def fit_and_plot_distributions_combined_avg_by_scenario(df, col_name, save_dir="output", binwidth=5):
    # Ensure the output directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Group simulation files by scenario
    scenario_groups = defaultdict(list)
    for sim in df['source_file'].unique():
        base = sim.split("_run")[0]  # Customize if your filenames differ
        scenario_groups[base].append(sim)

    # Determine the number of scenarios and layout for subplots
    scenarios = list(scenario_groups.keys())
    cols = 2  # Number of columns in the subplot grid
    rows = math.ceil(len(scenarios) / cols)  # Number of rows in the subplot grid

    # Define candidate distributions to fit
    candidate_distributions = {
        "exponential": stats.expon,
        "weibull": stats.weibull_min,
        "lognorm": stats.lognorm
    }

    # Create a figure with subplots
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 4), squeeze=False)

    # Iterate over each scenario to fit distributions
    for idx, scenario in enumerate(scenarios):
        # Filter the DataFrame for the current scenario
        group_df = df[df['source_file'].isin(scenario_groups[scenario])]
        data = group_df[col_name].dropna()  # Extract the column of interest
        ax = axes[idx // cols][idx % cols]  # Select the appropriate subplot axis

        # Skip if there is no data for the current scenario
        if data.empty:
            ax.set_visible(False)
            continue

        # Plot the empirical data as a histogram
        sns.histplot(data, binwidth=binwidth, stat="density", label="Empirical", color="lightgray", edgecolor="black", ax=ax)
        x = np.linspace(data.min(), data.max(), 200)  # Generate x values for PDF plotting

        # Variables to track the best-fitting distribution
        best_fit = None
        best_pval = -1  # Highest p-value indicates the best fit
        best_d = float("inf")  # Lowest D-statistic for ties in p-value

        # Fit each candidate distribution to the data
        for name, dist in candidate_distributions.items():
            try:
                # Fit the distribution to the data
                params = dist.fit(data)
                # Perform the Kolmogorov-Smirnov test
                D, p_val = kstest(data, dist.cdf, args=params)
                # Compute the PDF for the fitted distribution
                pdf = dist.pdf(x, *params)
                # Plot the fitted PDF
                ax.plot(x, pdf, label=f"{name} (D={D:.3f}, p={p_val:.3f})")

                # Update the best fit if this distribution is better
                if p_val > best_pval or (p_val == best_pval and D < best_d):
                    best_fit = (name, params)
                    best_pval = p_val
                    best_d = D

            except Exception as e:
                # Handle any errors during fitting
                print(f"Could not fit {name} for {scenario}: {e}")

        # Set the title to indicate the best-fitting distribution
        if best_fit:
            ax.set_title(f"{scenario}\nBest Fit (K-S): {best_fit[0]} (p={best_pval:.3f})")
        else:
            ax.set_title(f"{scenario} (No valid fit)")

        # Set axis labels and grid
        ax.set_xlabel(f"{col_name} (minutes)")
        ax.set_ylabel("Density")
        ax.grid(True)
        ax.legend(fontsize="small")  # Add a legend to distinguish distributions

    # Hide unused subplots if the grid is larger than the number of scenarios
    for i in range(len(scenarios), rows * cols):
        fig.delaxes(axes[i // cols][i % cols])

    # Adjust layout and save the figure to the specified directory
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, f"avg_combined_{col_name}_fit_distributions.png"))
    plt.close()

def compare_to_truncated_exponential_avg_by_scenario(df, col_name, lam, binwidth=30, save_dir="output"):
    # Ensure the output directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Group files by scenario (e.g., simulation_1 from simulation_1_run_1.json, etc.)
    scenario_groups = defaultdict(list)
    for sim in df['source_file'].unique():
        base = sim.split("_run")[0]  # Adjust if your filenames differ
        scenario_groups[base].append(sim)

    # Determine the number of scenarios and layout for subplots
    scenarios = list(scenario_groups.keys())
    cols = 2  # Number of columns in the subplot grid
    rows = math.ceil(len(scenarios) / cols)  # Number of rows in the subplot grid

    # Create a figure with subplots
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 4), squeeze=False)

    # Iterate over each scenario to compare empirical and simulated data
    for idx, scenario in enumerate(scenarios):
        # Filter the DataFrame for the current scenario
        group_df = df[df['source_file'].isin(scenario_groups[scenario])]
        real_data = group_df[col_name].dropna()  # Extract the column of interest
        ax = axes[idx // cols][idx % cols]  # Select the appropriate subplot axis

        # Skip if there is no data for the current scenario
        if real_data.empty:
            ax.set_visible(False)
            continue

        # Simulate truncated exponential data with the same sample size as the real data
        sim_data = truncated_exponential_sample(len(real_data), lam)

        # Plot the empirical data as a histogram
        sns.histplot(real_data, stat="density", binwidth=binwidth, label="Empirical", color="skyblue", edgecolor="black", ax=ax)
        # Plot the simulated truncated exponential data as a histogram
        sns.histplot(sim_data, stat="density", binwidth=binwidth, label="Truncated Exp", color="tomato", alpha=0.4, ax=ax)

        # Set the title and labels for the subplot
        ax.set_title(f"{scenario}\nEmpirical vs. Truncated Exp")
        ax.set_xlabel(f"{col_name} (minutes)")
        ax.set_ylabel("Density")
        ax.grid(True)  # Add a grid for better readability
        ax.legend(fontsize="small")  # Add a legend to distinguish the datasets

    # Hide unused subplots if the grid is larger than the number of scenarios
    for i in range(len(scenarios), rows * cols):
        fig.delaxes(axes[i // cols][i % cols])

    # Adjust layout and save the figure to the specified directory
    plt.tight_layout()
    out_path = os.path.join(save_dir, f"avg_combined_{col_name}_compare_trunc_exp.png")
    plt.savefig(out_path)
    plt.close()

def hourly_arrival_count_avg_by_scenario(df, event_filter="arrival", save_dir="output"):
    # Ensure the output directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Group simulation files by scenario
    scenario_groups = defaultdict(list)
    for sim in df['source_file'].unique():
        base = sim.split("_run")[0]  # Customize if your filenames vary
        scenario_groups[base].append(sim)

    # Determine the number of scenarios and layout for subplots
    scenarios = list(scenario_groups.keys())
    cols = 2  # Number of columns in the subplot grid
    rows = math.ceil(len(scenarios) / cols)  # Number of rows in the subplot grid

    # Create a figure with subplots
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 4), squeeze=False)

    # Iterate over each scenario to generate heatmaps
    for idx, scenario in enumerate(scenarios):
        # Filter the DataFrame for the current scenario
        sim_df = df[df['source_file'].isin(scenario_groups[scenario])]
        if event_filter:
            # Further filter by the specified event type
            sim_df = sim_df[sim_df['event'] == event_filter]

        # Group data by day and simulation hour, and count occurrences
        grouped = sim_df.groupby(["day", "sim_hour"]).size().reset_index(name="count")

        # Pivot the grouped data to create a heatmap-friendly format
        pivot = grouped.pivot(index="day", columns="sim_hour", values="count").fillna(0)

        # Select the appropriate subplot axis
        ax = axes[idx // cols][idx % cols]

        # Plot the heatmap for the current scenario
        sns.heatmap(pivot, cmap="Blues", ax=ax, cbar=False, annot=True, fmt=".0f")

        # Set titles and labels for the subplot
        ax.set_title(f"{scenario}\nHourly {event_filter.capitalize()} Counts")
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Simulation Day")

    # Hide unused subplots if the grid is larger than the number of scenarios
    for i in range(len(scenarios), rows * cols):
        fig.delaxes(axes[i // cols][i % cols])

    # Adjust layout and save the figure to the specified directory
    plt.tight_layout()
    out_path = os.path.join(save_dir, f"avg_hourly_arrivals_{event_filter}.png")
    plt.savefig(out_path)
    plt.close()

def erlang_c(scenario, lambda_rate, mu_rate, chargers=4):
    # Dictionary to store results for each number of chargers
    output_data = {}
    
    # Iterate over the number of chargers from 1 to the specified maximum
    for c in range(1, chargers + 1):
        a = lambda_rate / mu_rate  # Calculate the offered load
        rho = a / c  # Utilization factor (traffic intensity per server)

        # Calculate the denominator of the Erlang C formula
        sum_terms = sum([(a ** k) / math.factorial(k) for k in range(c)])  # Sum of terms for k < c
        last_term = (a ** c) / (math.factorial(c) * (1 - rho))  # Last term for k = c
        denom = sum_terms + last_term  # Total denominator

        # Calculate the probability of waiting (Erlang C formula)
        pw = last_term / denom

        # Calculate the expected waiting time in the queue
        ewq = pw / (c * mu_rate - lambda_rate)  # Expected queue wait time
        ew = ewq + 1 / mu_rate  # Total expected wait time (queue + service)

        # Store results for the current number of chargers
        results = {
            "lambda_rate": lambda_rate,  # Arrival rate
            "mu_rate": mu_rate,  # Service rate
            "c": c,  # Number of chargers
            "ErlangC_Prob_Wait": pw,  # Probability of waiting
            "E[Wq] (hrs)": ewq,  # Expected queue wait time in hours
            "E[W_total] (hrs)": ew,  # Total expected wait time in hours
            "Utilization": rho  # Utilization factor
        }
        output_data[f"c_{c}"] = results  # Add results to the output dictionary

    # Ensure the output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Save the results to a JSON file in the output directory
    output_file = os.path.join("output", f"{scenario}_erlang_c_results.json")
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=4)

def calculate_poisson_rates_avg_by_scenario(df, save_dir="logs"):
    # Ensure the output directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Group simulation files by scenario
    scenario_groups = defaultdict(list)
    for sim in df['source_file'].unique():
        base = sim.split("_run")[0]  # Extract the base scenario name from the file name
        scenario_groups[base].append(sim)

    results = []  # Initialize a list to store results for each scenario

    # Iterate over each scenario and its associated runs
    for scenario, runs in scenario_groups.items():
        run_stats = []  # List to store per-run statistics

        # Process each run in the current scenario
        for sim in runs:
            sub_df = df[df['source_file'] == sim]  # Filter the DataFrame for the current run
            mean_arrival_time = sub_df['return_delay'].dropna().mean() / 60  # Calculate mean arrival time in hours
            mean_service_time = sub_df['charging_time'].dropna().mean() / 60  # Calculate mean service time in hours

            # Calculate arrival rate (lambda), service rate (mu), and utilization (rho)
            lambda_rate = 1 / mean_arrival_time if mean_arrival_time else None
            mu_rate = 1 / mean_service_time if mean_service_time else None
            rho = lambda_rate / mu_rate if lambda_rate and mu_rate else None

            # Append the calculated rates for the current run
            run_stats.append((lambda_rate, mu_rate, rho))

        # Aggregate statistics across all runs in the scenario
        lambda_values = [x[0] for x in run_stats if x[0] is not None]  # Filter valid lambda values
        mu_values = [x[1] for x in run_stats if x[1] is not None]  # Filter valid mu values
        rho_values = [x[2] for x in run_stats if x[2] is not None]  # Filter valid rho values

        # Calculate mean rates and utilization
        lambda_mean = sum(lambda_values) / len(lambda_values) if lambda_values else None
        lambda_rate_mean = 1 / (sum(lambda_values) / len(lambda_values)) if lambda_values else None
        mu_mean = sum(mu_values) / len(mu_values) if mu_values else None
        mu_rate_mean = 1 / (sum(mu_values) / len(mu_values)) if mu_values else None
        rho_mean = sum(rho_values) / len(rho_values) if rho_values else None

        # Perform Erlang C calculations for the scenario
        erlang_c(scenario=scenario, lambda_rate=lambda_rate_mean, mu_rate=mu_rate_mean, chargers=4)

        # Append the aggregated results for the current scenario
        results.append({
            "scenario": scenario,
            "mean_lambda (1/lambda) (arrivals/hr)": lambda_mean,
            "mean_lambda_rate (arrivals/hrs)": lambda_rate_mean,
            "mean_mu (services/hr)": mu_mean,
            "mean_mu_rate (services/hrs)": mu_rate_mean,
            "mean_rho (utilization)": rho_mean,
            "n_runs": len(runs)  # Number of runs in the scenario
        })

    # Convert the results to a DataFrame
    results_df = pd.DataFrame(results)

    # Save the results to a CSV file in the specified directory
    out_path = os.path.join(save_dir, "poisson_rates_summary_avg.csv")
    results_df.to_csv(out_path, index=False)

    # Return the results DataFrame
    return results_df

if __name__ == "__main__":
    # Load logs from the default "logs" directory and convert them into a DataFrame
    df = load_logs()
    print(f"Loaded {len(df)} logs from {len(df['source_file'].unique())} files.")
    
    # Unpack the 'extra' column into separate columns for easier analysis
    df = unpack_extra(df)
    
    # Plot histograms for the 'return_delay' column, grouped by scenario, with a bin width of 5 minutes
    plot_histograms_by_sim_combined_avg_by_scenario(df, 'return_delay', binwidth=5)
    # Plot histograms for the 'charging_time' column, grouped by scenario, with a bin width of 30 minutes
    plot_histograms_by_sim_combined_avg_by_scenario(df, 'charging_time', binwidth=30)
    
    # Fit and plot distributions for the 'return_delay' column, grouped by scenario, with a bin width of 5 minutes
    fit_and_plot_distributions_combined_avg_by_scenario(df, 'return_delay', binwidth=5)
    # Fit and plot distributions for the 'charging_time' column, grouped by scenario, with a bin width of 30 minutes
    fit_and_plot_distributions_combined_avg_by_scenario(df, 'charging_time', binwidth=30)
    
    # Compare the 'return_delay' column to a truncated exponential distribution with lambda=10.375
    compare_to_truncated_exponential_avg_by_scenario(df, col_name="return_delay", lam=10.375, binwidth=30)
    
    # Generate heatmaps for hourly arrival counts of events filtered by "requesting charger"
    hourly_arrival_count_avg_by_scenario(df, event_filter="requesting charger")
    
    # Calculate Poisson rates (arrival and service rates) for each scenario and save the summary
    rate_summary = calculate_poisson_rates_avg_by_scenario(df)
    
    # Print the summary of calculated rates
    print(rate_summary)