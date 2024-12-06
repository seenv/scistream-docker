import subprocess
import pandas as pd

# Define header descriptions
HEADER_DESCRIPTIONS = {
    "pxname": "Proxy name",
    "svname": "Server name",
    "qcur": "Current number of queued requests",
    "qmax": "Maximum number of queued requests observed",
    "scur": "Current number of active sessions",
    "smax": "Maximum number of concurrent sessions observed",
    "slim": "Session limit",
    "stot": "Total number of sessions (connections) handled",
    "bin": "Total bytes received",
    "bout": "Total bytes sent",
    "dreq": "Denied requests due to security or rules",
    "dresp": "Denied responses due to security or rules",
    "ereq": "Number of request errors",
    "econ": "Number of connection errors with backend",
    "eresp": "Number of response errors from backend",
    "wretr": "Number of retries on backend",
    "wredis": "Number of redispatches to another backend",
    "status": "Current status",
    "weight": "Server weight for load balancing",
    "act": "Number of active servers in the backend",
    "bck": "Number of backup servers in the backend",
    "chkfail": "Number of failed health checks",
    "chkdown": "Number of times server was marked down",
    "lastchg": "Time since the last status change (seconds)",
    "downtime": "Total downtime since start (seconds)",
    "qlimit": "Maximum queue size",
    "pid": "Process ID of HAProxy instance",
    "iid": "Proxy ID",
    "sid": "Server ID",
    "throttle": "Throttle percentage for slow starts",
    "lbtot": "Total sessions via load balancing",
    "tracked": "Tracks another proxy's status",
    "type": "Proxy type",
    "rate": "Sessions per second (last second)",
    "rate_lim": "Configured session rate limit",
    "rate_max": "Maximum observed session rate",
    "check_status": "Last health check status",
    "check_code": "Response code from last health check",
    "check_duration": "Duration of last health check (ms)",
    "hrsp_1xx": "HTTP 1xx responses",
    "hrsp_2xx": "HTTP 2xx responses",
    "hrsp_3xx": "HTTP 3xx responses",
    "hrsp_4xx": "HTTP 4xx responses",
    "hrsp_5xx": "HTTP 5xx responses",
    "hrsp_other": "Non-standard HTTP responses",
    "hanafail": "Failed handshakes",
    "req_rate": "Request rate (last second)",
    "req_rate_max": "Maximum observed request rate",
    "req_tot": "Total requests handled",
    "cli_abrt": "Client-side aborts",
    "srv_abrt": "Server-side aborts",
    "comp_in": "Bytes in for compression",
    "comp_out": "Bytes out after compression",
    "comp_byp": "Bytes bypassed for compression",
    "comp_rsp": "Compressed responses",
    "lastsess": "Time since last session (seconds)",
    "qtime": "Request time (ms)",
    "ctime": "Connection time (ms)",
    "rtime": "Response time (ms)",
    "ttime": "Total time (ms)",
}

def get_haproxy_stats():
    try:
        # Run the HAProxy stats command and capture the output
        result = subprocess.run(
            'echo "show stat" | socat /tmp/haproxy.sock stdio',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        if result.returncode != 0:
            raise Exception(f"Error executing command: {result.stderr.strip()}")
        return result.stdout
    except Exception as e:
        print(f"Failed to fetch HAProxy stats: {e}")
        return ""

def parse_haproxy_stats(output):
    if not output:
        print("No stats to parse!")
        return None

    lines = output.strip().split("\n")

    # First line contains headers
    headers = lines[0][2:].split(",")  # Remove "# " prefix and split by commas
    rows = [line.split(",") for line in lines[1:]]
    # Create a DataFrame for better manipulation
    df = pd.DataFrame(rows, columns=headers)
    return df

def write_to_files(df, txt_file="haproxy_stats.txt", csv_file="haproxy_stats.csv"):
    if df is None:
        print("No data available to save!")
        return

    # Write TXT file with descriptions and values
    with open(txt_file, "w") as file:
        for header in df.columns:
            description = HEADER_DESCRIPTIONS.get(header, header)
            values = " , ".join(df[header].tolist())
            file.write(f"{description}, {values}\n")

    print(f"HAProxy stats saved in text format to {txt_file}.")

    # Write CSV file with headers and values
    df.to_csv(csv_file, index=False)
    print(f"HAProxy stats saved in CSV format to {csv_file}.")

def main():
    # Fetch the stats
    haproxy_output = get_haproxy_stats()
    # Parse the stats
    df = parse_haproxy_stats(haproxy_output)

    if df is None:
        return

    # Save stats in both TXT and CSV formats
    write_to_files(df, txt_file="haproxy_new_stats.txt", csv_file="haproxy_new_stats.csv")

if __name__ == "__main__":
    main()