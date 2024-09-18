import os
import logging
import subprocess
from pathlib import Path
import requests
import json
import time
import urllib3

# Custom exception class for S2DS-related errors
class S2DSException(Exception):
    pass

##Instance Names allowed:
# Haproxy
# Nginx
# Stunnel

# Dynamically create an instance of the provided class_name (Haproxy, Nginx, etc.)
def create_instance(class_name):
    try:
        # Use eval to create an instance of the given class_name
        # Python’s eval() function to dynamically create an instance of a class
        instance = eval(f"{class_name}()")
        return instance
    # Handle the case where the class_name doesn't exist
    except NameError:
         print(f"Class {class_name} is not defined.")
    return create_instance(type)

# Retrieve the HAProxy configuration file path (from environment variable or default location)
def get_haproxy_config_path():
    # Check if the environment variable for HAProxy config path is set
    config_path = os.environ.get('HAPROXY_CONFIG_PATH')

    if config_path:
        # If the environment variable is set, use its value
        return config_path
    else:
        # If the environment variable is not set, use the default path
        default_path = os.path.expanduser('~/.scistream')

        # Create the directory if it doesn't exist
        os.makedirs(default_path, exist_ok=True)

        # Create an empty file if it doesn't exist
        if not os.path.exists(default_path):
            open(default_path, 'a').close()

        return default_path

# Main S2DS class for managing S2DS processes and their listeners
class S2DS():
    ## TODO Cleanup
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    # Start a given number of S2DS subprocesses and return a dictionary with process information
    def start(self, num_conn, listener_ip):
        self.logger.info(f"Starting {num_conn} S2DS subprocess(es)...")
        s2ds_path =  Path(__file__).resolve().parent.parent / "scistream" / "S2DS" / "S2DS.out"
        entry={"s2ds_proc":[], "listeners":[]}
        try:
            for _ in range(num_conn):
                # Start a new S2DS subprocess
                new_proc = subprocess.Popen([s2ds_path], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
                """
                Popen is a class in Python’s subprocess module. It represents an external process started by
                the Python code. The Popen object allows the Python program to interact with the process, send
                input, capture output, and check its status. For example, it can run a command-line tool and
                capture its output or send input to it programmatically.
                """

                # Read the listener port from the subprocess output                
                new_listener_port = new_proc.stdout.readline().decode("utf-8").split("\n")[0]
                # Validate the listener port
                if not new_listener_port.isdigit() or int(new_listener_port) < 0 or int(new_listener_port) > 65535:
                    raise S2DSException(f"S2DS subprocess returned invalid listener port '{new_listener_port}'")
                # Append the listener information to the entry
                new_listener = listener_ip + ":" + new_listener_port
                entry["s2ds_proc"].append(new_proc)
                entry["listeners"].append(new_listener)
        except Exception as e:
            # Log and raise an exception in case of an error
            self.logger.error(f"Error starting S2DS subprocess(es): {e}")
            raise S2DSException(f"Error starting S2DS subprocess(es): {e}") from e
        return entry

    # Terminate all S2DS subprocesses and log the termination
    def release(self, entry):
        if entry["s2ds_proc"] != []:
            for i, rem_proc in enumerate(entry["s2ds_proc"]):
                # Send termination signal to each subprocess
                rem_proc.terminate() # TODO: Make sure s2ds buffer handles this signal gracefully
                # Replace the process object with the PID for logging
                entry["s2ds_proc"][i] = rem_proc.pid # Print out PID rather than Popen object
            self.logger.info(f"Terminated {len(entry['s2ds_proc'])} S2DS subprocess(es)")

    # Send listener updates to S2DS subprocesses
    def update_listeners(self, listeners, s2ds_proc, uid, role):
        # Send remote port information to S2DS subprocesses in format "remote_ip:remote_port\n"
        for i in range(len(listeners)):
            # Send termination signal to each subprocess
            curr_proc = s2ds_proc[i]
            curr_remote_conn = listeners[i] + "\n"
            # Check if the subprocess has unexpectedly exited
            if curr_proc.poll() is not None:
                raise S2CSException(f"S2DS subprocess with PID '{curr_proc.pid}' unexpectedly quit")
            # Write listener info to the subprocess stdin
            curr_proc.stdin.write(curr_remote_conn.encode())
            curr_proc.stdin.flush()
            self.logger.info(f"S2DS subprocess establishing connection with {curr_remote_conn.strip()}...")

import docker
from jinja2 import Environment, FileSystemLoader        # imports the Jinja2 templating engine
"""
jinja2 allows you to create dynamic files (like configuration files) by
rendering templates with specific variables. FileSystemLoader tells Jinja2
where to look for template files (in this case, on the file system)
"""

# Base class for proxy container management (HAProxy, Nginx, etc.)
"""
The container (like HAProxy, Nginx, or Stunnel) serves as a proxy server.
It listens on specific ports and forwards requests to backend services
(like S2DS subprocesses). The container configuration, managed by Docker,
specifies the necessary files and settings for these proxies. Depending on
the role (PROD or CONS), the container acts either as a producer or consumer
in the data streaming setup.
"""
class ProxyContainer():
    def __init__(self, service_plugin_type="docker"):
        self.service_plugin_type = service_plugin_type
        pass

    # Placeholder for stopping the container
    def release(self, entry):
        pass

    # Start container processes and set up listeners (custom ports are hardcoded)
    def start(self, num_conn, listener_ip):
        ##STOP hardcoding port 5001
        #self.local_ports = [5064 + i for i in range(num_conn)]
        # Predefined list of ports for local connections
        self.local_ports = [5074, 5075, 5076, 6000, 6001]
        entry={"s2ds_proc":[], "listeners":[f"{listener_ip}:{port}" for port in self.local_ports]}
        return entry

    # Generate configuration and start proxy containers
    def update_listeners(self, listeners, s2ds_proc, uid, role = "PROD"):
        # Select appropriate Docker client based on plugin type
        """
        The correct plugin is chosen based on how the containers are being
        managed—whether through the Docker API, a custom Janus service, or
        direct interaction with Docker’s UNIX socket (DockerSock).
        """
        if self.service_plugin_type == "docker":
           docker_client = DockerPlugin()
        if self.service_plugin_type == "janus":
           docker_client = JanusPlugin()
        if self.service_plugin_type == "dockersock":
           docker_client = DockerSockPlugin()

        # Variables to be used in the Jinja2 template rendering
        vars = {
            'local_ports': self.local_ports,
            'dest_array': listeners,
            'client': "yes" if role == "CONS" else "no"
        }
        # Load and render the Jinja2 template env for the configuration
        env = Environment(loader=FileSystemLoader(f'{Path(__file__).parent}'))
        template = env.get_template(f'{self.cfg_filename}.j2')
        # Render the template to create the configuration file
        #renders file to a slightly different location
        """
        Jinja2 template rendering is a process in which a template (a file
        with placeholders) is filled with actual data (variables) and converted
        into a final output file (like a configuration file). The placeholders
        in the template are replaced by the values you pass in. It’s used to
        create configuration files dynamically, based on variables like listener
        ports, IPs, etc.
        """

        # Get the path to save the rendered configuration
        config_path = get_haproxy_config_path()

        # Write the rendered template to the configuration file
        with open(f'{config_path}/{self.cfg_filename}', 'w') as f:
            f.write(template.render(vars))

        # Write UID to the key file
        with open(f'{config_path}/{self.key_filename}', 'w') as f:
            f.write("client1:"+uid.replace("-", ""))

        # Define the Docker container configuration
        container_config = {
            'image': self.image_name ,
            'name': self.container_name,
            'detach': True,
            'volumes': {
                        f"{config_path}/{self.cfg_filename}": {'bind': self.cfg_location, 'mode': 'ro'},
                        f"{config_path}/{self.key_filename}": {'bind': self.key_location, 'mode': 'ro'}
                        },
            'network_mode': 'host'
        }

        # Start the proxy container (docker container)
        name = self.container_name
        docker_client.start(name, container_config)

# Specific implementations for HAProxy, Nginx, and Stunnel proxy containers
class Haproxy(ProxyContainer):
    def __init__(self, service_plugin_type="docker"):
        self.service_plugin_type = service_plugin_type
        self.cfg_location = '/usr/local/etc/haproxy/haproxy.cfg'
        self.key_location = '/usr/local/etc/haproxy/haproxy.key'
        self.image_name = 'haproxy:latest'
        self.container_name = "myhaproxy"
        self.cfg_filename = 'haproxy.cfg'
        self.key_filename = 'haproxy.cfg.j2'
        if self.service_plugin_type == "dockersock":
           self.cfg_filename = "/data/scistream-demo/configs/haproxy.cfg"
        pass

class Nginx(ProxyContainer):
    def __init__(self, service_plugin_type="docker"):
        self.service_plugin_type = service_plugin_type
        self.cfg_location = '/etc/nginx/nginx.conf'
        self.key_location = '/etc/nginx/nginx.key'
        self.image_name = 'nginx:latest'
        self.container_name = "mynginx"
        self.cfg_filename = f'nginx.conf'
        self.key_filename = 'nginx.conf.j2'
        if self.service_plugin_type == "dockersock":
           self.cfg_filename = "/data/scistream-demo/configs/nginx.conf"
        pass

class Stunnel(ProxyContainer):
    def __init__(self, service_plugin_type="docker"):
        self.service_plugin_type = service_plugin_type
        self.cfg_location = '/etc/stunnel/stunnel.conf'
        self.key_location = '/etc/stunnel/stunnel.key'
        self.image_name = 'stunnel:latest'
        self.container_name = "mystunnel"
        self.cfg_filename = 'stunnel.conf'
        self.key_filename = 'stunnel.key'
        
        if self.service_plugin_type == "dockersock":
            self.cfg_filename = "/data/scistream-demo/configs/stunnel.conf"
            self.key_filename = "/data/scistream-demo/configs/stunnel.key"
        pass

# Specialized subclasses for Janus and DockerSock services (stubbed out)
"""
Janus, DockerSock, DockerPlugin, DockerSockPlugin, and JanusPlugin are different types of
service management plugins that manage proxy containers (HAProxy, Nginx, Stunnel). Each of
these classes is responsible for managing containers, starting them, and interacting with
specific types of service management backends.
	•	JanusPlugin: Manages containers using the Janus service (possibly a custom service).
    •	DockerPlugin: Uses Docker to manage the containers.
    •	DockerSockPlugin: Likely manages containers via Docker socket access, which allows
        communication with Docker via a UNIX socket.
"""
class Janus(Haproxy):
    def __init__(self):
        self.service_plugin_type = "janus"

class DockerSock(Haproxy):
    def __init__(self):
        self.service_plugin_type = "dockersock"

class DockerPlugin():
    def __init__(self):
        self.client = docker.from_env()

    def start(self, name, container_config):
        try:
            container = self.client.containers.get(name)
            print(f'Container {name} already exists')
            container.restart()
        except docker.errors.NotFound:
            print(f'Creating container {name}')
            container = self.client.containers.run(**container_config)
        print(f'Started container with ID {container.id}')

class DockerSockPlugin(DockerPlugin):
    def __init__(self):
        self.client = docker.DockerClient(base_url='unix://var/run/docker.sock')

class JanusPlugin():
    def __init__(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.auth = ('admin', 'admin')# update this

    def start(name, container_config):
        ## check if a container exists. 
        # This line sends an HTTP PUT request to a URL (in this case, a testbed server).
        # It likely activates or configures a session on the server.
        active_session = requests.put(url='https://nersc-srv-1.testbed100.es.net:5000/api/janus/controller/active', auth=self.auth, verify=False)
        if len(active_session.json()) == 0:
            ## create container
            response = requests.post(url="https://nersc-srv-1.testbed100.es.net:5000/api/janus/controller/create", auth = self.auth, json={"errors":[],"instances":["nersc-dtnaas-1"],"image":"haproxy:latest","profile":"scistream-demo","arguments":"","kwargs":{"USER_NAME":"","PUBLIC_KEY":""},"remove_container":"None"}, verify=False)
            assert response.status_code == 200
            session_id = list(json.loads(response.text).keys())[0]
            print("JANUS CONTAINER DOESNT EXIST")
        else:
            session_id = active_session.json()[0]['id']
            print("JANUS CONTAINER EXIST")
        print(f"SESSION_ID = {session_id}")
        ## Container exists, now update config stop and start
        cfg= Path(__file__).parent / "haproxy.cfg"
        dest_path = Path("/data/scistream-demo/configs/haproxy.cfg")
        os.system(f'cp {cfg} {dest_path}')
        ## This assumes we are running this code in the same location as the docker platform
        stop_response = requests.put(url=f'https://nersc-srv-1.testbed100.es.net:5000/api/janus/controller/stop/{session_id}', auth=self.auth, verify=False)
        start_response = requests.put(url=f'https://nersc-srv-1.testbed100.es.net:5000/api/janus/controller/start/{session_id}', auth=self.auth, verify=False)
