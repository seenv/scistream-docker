import psutil
import time
import json

## This code could possibly be replaced by prometheus
## or some other type of monitoring agent
## I wrote this because it was the path of least resistance

def get_metrics(duration=60):
    duration = int(duration)

    cpu_usage = []
    ram_usage = []
    disk_usage = []
    network_sent = []
    network_recv = []
    process_count = []

    start_time = time.time()

    # Get initial network stats for comparison
    initial_net = psutil.net_io_counters()
    initial_sent = initial_net.bytes_sent
    initial_recv = initial_net.bytes_recv

    while time.time() - start_time < duration:
        # Collect metrics every second
        cpu_usage.append(psutil.cpu_percent(interval=1))
        ram_usage.append(psutil.virtual_memory().percent)
        disk_usage.append(psutil.disk_usage('/').percent)

        net_io = psutil.net_io_counters()
        network_sent.append(net_io.bytes_sent - initial_sent)
        network_recv.append(net_io.bytes_recv - initial_recv)
        initial_sent = net_io.bytes_sent  # Update for next interval
        initial_recv = net_io.bytes_recv  # Update for next interval

        process_count.append(len(psutil.pids()))
        physical_cores = psutil.cpu_count(logical=False)

    # Calculate averages and sums
    metrics = {
        'average_cpu_usage': sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0,
        'average_ram_usage': sum(ram_usage) / len(ram_usage) if ram_usage else 0,
        'average_disk_usage': sum(disk_usage) / len(disk_usage) if disk_usage else 0,
        'total_network_sent': sum(network_sent),
        'total_network_recv': sum(network_recv),
        'average_process_count': sum(process_count) / len(process_count) if process_count else 0,
        'physical_cores': physical_cores
    }

    # Convert network usage to megabytes
    metrics['total_network_sent'] /= 1024 * 1024
    metrics['total_network_recv'] /= 1024 * 1024

    return metrics

# To execute the test
if __name__ == "__main__":
    duration = 30  # Test duration in seconds
    results = get_metrics(duration=duration)
    for key, value in results.items():
        results[key] = round(value,2)
    print(json.dumps(results, indent=4))
