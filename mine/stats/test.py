import subprocess

def get_output():
    try:
        # Use a single string for the shell command
        result = subprocess.run(
            'echo "show stat" | socat /tmp/haproxy.sock stdio',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )

        # Check if the command ran successfully
        if result.returncode != 0:
            print(f"Error: {result.stderr.strip()}")
        else:
            print("The result in the get_haproxy_stat:\n", result.stdout.strip())

    except Exception as e:
        print(f"Failed to fetch HAProxy stats: {e}")

get_output()