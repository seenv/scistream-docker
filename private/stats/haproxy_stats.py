import subprocess
import pandas as pd
from prettytable import PrettyTable

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

def save_table_to_file(df, file_name="haproxy_stats.txt"):
    if df is None:
        print("No data available to save!")
        return

    # Create a PrettyTable instance
    table = PrettyTable()
    table.field_names = df.columns.tolist()

    # Add rows to the PrettyTable
    for _, row in df.iterrows():
        table.add_row(row.tolist())

    # Write the table to a file
    with open(file_name, "w") as file:
        file.write(table.get_string())

    print(f"HAProxy stats saved to {file_name}")

def save_to_csv(df, file_name="haproxy_stats.csv"):
    if df is None:
        print("No data available to save!")
        return

    # Define the header descriptions
    header_info = {
                    "pxname": "Proxy name (frontend/backend)",
                    "svname": "Server name or special keywords like FRONTEND/BACKEND",
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
                    "status": "Current status (UP; DOWN; OPEN)",
                    "weight": "Server weight for load balancing",
                    "act": "Number of active servers in the backend",
                    "bck": "Number of backup servers in the backend",
                    "chkfail": "Number of failed health checks",
                    "chkdown": "Number of times server was marked down",
                    "lastchg": "Time since the last status change (seconds)",
                    "downtime": "Total downtime since start (seconds)",
                    "qlimit": "Maximum queue size",
                    "pid": "Process ID of HAProxy instance",
                    "iid": "Proxy ID (unique within a process)",
                    "sid": "Server ID (unique within a proxy)",
                    "throttle": "Throttle percentage for slow starts",
                    "lbtot": "Total number of sessions selected via load balancing",
                    "tracked": "Tracks another proxy's status",
                    "type": "Proxy type (0:frontend; 1:backend; 2:server)",
                    "rate": "Number of sessions per second over the last second",
                    "rate_lim": "Configured session rate limit",
                    "rate_max": "Maximum observed session rate",
                    "check_status": "Status of last health check",
                    "check_code": "Response code from last health check",
                    "check_duration": "Duration of last health check (ms)",
                    "hrsp_1xx": "HTTP responses with 1xx status codes",
                    "hrsp_2xx": "HTTP responses with 2xx status codes",
                    "hrsp_3xx": "HTTP responses with 3xx status codes",
                    "hrsp_4xx": "HTTP responses with 4xx status codes",
                    "hrsp_5xx": "HTTP responses with 5xx status codes",
                    "hrsp_other": "HTTP responses with nonstandard codes",
                    "hanafail": "Failed handshakes",
                    "req_rate": "Request rate over the last second",
                    "req_rate_max": "Maximum observed request rate",
                    "req_tot": "Total requests handled",
                    "cli_abrt": "Client-side aborts",
                    "srv_abrt": "Server-side aborts",
                    "comp_in": "Bytes in for HTTP compression",
                    "comp_out": "Bytes out after HTTP compression",
                    "comp_byp": "Bytes bypassed for HTTP compression",
                    "comp_rsp": "Number of compressed responses",
                    "lastsess": "Time since the last session (seconds)",
                    "last_chk": "Last health check result",
                    "last_agt": "Last agent check result",
                    "qtime": "Request time (ms)",
                    "ctime": "Connection time (ms)",
                    "rtime": "Response time (ms)",
                    "ttime": "Total time (ms)",
                    "agent_status": "Current agent status",
                    "agent_code": "Agent response code",
                    "agent_duration": "Agent check duration (ms)",
                    "check_desc": "Description of last health check",
                    "agent_desc": "Description of last agent check",
                    "check_rise": "Number of successful checks required to mark up",
                    "check_fall": "Number of failures required to mark down",
                    "check_health": "Current health score",
                    "agent_rise": "Number of agent successes required to mark up",
                    "agent_fall": "Number of agent failures required to mark down",
                    "agent_health": "Current agent health score",
                    "addr": "Address of the server",
                    "cookie": "Cookie value for the server",
                    "mode": "Mode of the proxy (HTTP; TCP)",
                    "algo": "Load balancing algorithm",
                    "conn_rate": "Connection rate over the last second",
                    "conn_rate_max": "Maximum observed connection rate",
                    "conn_tot": "Total connections handled",
                    "intercepted": "Connections intercepted for transparent proxy",
                    "dcon": "Connections denied due to security",
                    "dses": "Sessions denied due to security",
                    "wrew": "Number of retries to establish a connection",
                    "connect": "Number of successful connections",
                    "reuse": "Number of connection reuses",
                    "cache_lookups": "Number of cache lookups",
                    "cache_hits": "Number of cache hits",
                    "srv_icur": "Current number of connections on the server",
                    "src_ilim": "Source connection limit",
                    "qtime_max": "Maximum observed queue time (ms)",
                    "ctime_max": "Maximum observed connection time (ms)",
                    "rtime_max": "Maximum observed response time (ms)",
                    "ttime_max": "Maximum observed total time (ms)",
                    "eint": "Errors intercepted",
                    "idle_conn_cur": "Current number of idle connections",
                    "safe_conn_cur": "Current number of safe connections",
                    "used_conn_cur": "Current number of used connections",
                    "need_conn_est": "Number of connections needed to establish",
                    "uweight": "Weight for servers in use",
                    "agg_server_status": "Aggregated server status",
                    "agg_server_check_status": "Aggregated server health check status",
                    "agg_check_status": "Aggregated check status",
                    "srid": "Session ID for current requests",
                    "sess_other": "Sessions from other proxies",
                    "h1sess": "HTTP/1.1 sessions",
                    "h2sess": "HTTP/2 sessions",
                    "h3sess": "HTTP/3 sessions",
                    "req_other": "Requests from other proxies",
                    "h1req": "HTTP/1.1 requests",
                    "h2req": "HTTP/2 requests",
                    "h3req": "HTTP/3 requests",
                    "proto": "Protocol in use",
                    "-": "Reserved field (not used)",
                    "ssl_sess": "SSL sessions",
                    "ssl_reused_sess": "Reused SSL sessions",
                    "ssl_failed_handshake": "Failed SSL handshakes",
                    "h2_headers_rcvd": "HTTP/2 headers received",
                    "h2_data_rcvd": "HTTP/2 data frames received",
                    "h2_settings_rcvd": "HTTP/2 settings frames received",
                    "h2_rst_stream_rcvd": "HTTP/2 reset stream frames received",
                    "h2_goaway_rcvd": "HTTP/2 goaway frames received",
                    "h2_detected_conn_protocol_errors": "HTTP/2 connection-level protocol errors",
                    "h2_detected_strm_protocol_errors": "HTTP/2 stream-level protocol errors",
                    "h2_rst_stream_resp": "HTTP/2 reset stream responses",
                    "h2_goaway_resp": "HTTP/2 goaway responses",
                    "h2_open_connections": "Number of open HTTP/2 connections",
                    "h2_backend_open_streams": "Number of open HTTP/2 streams to backends",
                    "h2_total_connections": "Total HTTP/2 connections handled",
                    "h2_backend_total_streams": "Total HTTP/2 streams to backends",
                    "h1_open_connections": "Number of open HTTP/1.1 connections",
                    "h1_open_streams": "Number of open HTTP/1.1 streams",
                    "h1_total_connections": "Total HTTP/1.1 connections handled",
                    "h1_total_streams": "Total HTTP/1.1 streams",
                    "h1_bytes_in": "Bytes received on HTTP/1.1 connections",
                    "h1_bytes_out": "Bytes sent on HTTP/1.1 connections",
                    "h1_spliced_bytes_in": "Bytes spliced in HTTP/1.1 connections",
                    "h1_spliced_bytes_out": "Bytes spliced out in HTTP/1.1 connections"
                    }

    # Save the DataFrame to a CSV file
    df.to_csv(file_name, index=False)

    # Append the header descriptions to the CSV file
    with open(file_name, "a") as file:
        file.write("\n\n# Header Descriptions:\n")
        for key, value in header_info.items():
            file.write(f"# {key}: {value}\n")

    print(f"HAProxy stats saved to {file_name}")

    

def main():
    # Fetch the stats
    haproxy_output = get_haproxy_stats()
    # Parse the stats
    df = parse_haproxy_stats(haproxy_output)

    if df is None:
        return
    # Save all stats to a CSV file
    save_to_csv(df, file_name="/home/seena/scistream-docker/mine/stats/haproxy_stats.csv")

    # Save all stats to a file
    save_table_to_file(df, file_name="/home/seena/scistream-docker/mine/stats/haproxy_stats.txt")

if __name__ == "__main__":
    main()