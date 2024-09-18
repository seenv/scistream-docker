import sys
import fire                           # Provides a library for creating CLI commands from functions
import grpc                           # For gRPC communication
import threading                      # For threading support

from .proto import scistream_pb2       # Imports gRPC service definitions (protobufs)
from .proto import scistream_pb2_grpc  # Imports gRPC service definitions (stub classes)

from concurrent import futures         # For concurrent execution of tasks
from .s2ds import create_instance      # Function to create an instance of a service type
from .utils import request_decorator, set_verbosity, authenticated  # Utility functions and decorators
from globus_action_provider_tools.authentication import TokenChecker  # For Globus token validation

# Custom exception for S2CS errors
class S2CSException(Exception):
    pass

# Default values for configuration
default_cid = 'c42c0dac-0a52-408e-a04f-5d31bfe0aef8'
default_secret = ""
default_server_crt = 'server.crt'
default_server_key = 'server.key'

import importlib.metadata
__version__ = importlib.metadata.version('scistream-proto')     # Retrieves the version of the 'scistream-proto' package

# S2CS class implementing the gRPC service
class S2CS(scistream_pb2_grpc.ControlServicer):
    TIMEOUT = 180       # Timeout value in seconds for waiting for 'hello' message

    def __init__(self, listener_ip, verbose, type="Haproxy", client_id=default_cid, client_secret=default_secret):
        self.response = None  # Holds the response to be sent back to the client
        self.resource_map = {}  # Maps request IDs to resource information
        self.listener_ip = listener_ip
        self.client_id = client_id
        self.client_secret = client_secret
        self.type = type

        # TokenChecker setup for authorization if client_secret is provided
        # Moving checker instantiation to the begginning, this was making the request take too long
        if self.client_secret != "":
            self.checker = TokenChecker(
                client_id=self.client_id,
                client_secret=self.client_secret,
                expected_scopes=[f"https://auth.globus.org/scopes/{self.client_id}/scistream"]
                )
        set_verbosity(self, verbose)    # Set verbosity level for logging

    #@validate_args(has=["role", "uid", "num_conn", "rate"])
    @request_decorator
    @authenticated
    def req(self, request: scistream_pb2.Request, context=None):
        """
        Handles the 'req' gRPC request. This function sets up a resource based on the request parameters,
        waits for a 'hello' message within the timeout period, and returns the response.
        """
        self.resource_map[request.uid] = {
            "role": request.role,
            "num_conn": request.num_conn,
            "rate": request.rate,
            "hello_received": threading.Event(),
            "prod_listeners": []
        }
        self.logger.debug(f"Added key: '{request.uid}' with entry: {self.resource_map[request.uid]}")

        self.s2ds=create_instance(self.type)                            # Creates an instance of the service type
        reply = self.s2ds.start(request.num_conn, self.listener_ip)     # Starts the service and gets the reply
        self.resource_map[request.uid].update(reply)                    # Updates resource map with reply data
        ##DEBUG message here show resource map
        
        # Wait for the 'hello' message within the specified timeout period
        hello_received = self.resource_map[request.uid]['hello_received'].wait(S2CS.TIMEOUT)

        if not hello_received:
            self.release_request(request.uid)       # Release resources if 'hello' message not received
            raise S2CSException(f"Hello not received within the timeout period")

        return self.response                        # Return the response to the client

    @request_decorator
    @authenticated
    def update(self, request, context=None):
        """
        Handles the 'update' gRPC request. Updates the listeners based on the role (PROD or other),
        and returns the updated listeners in the response.
        """
        #improve validation
        listeners=request.remote_listeners
        entry = self.resource_map[request.uid]
        print(request.role)
        if (request.role == "PROD"):
            listeners = [ listeners[ i % len(listeners) ] for i in range(entry["num_conn"]) ]
        else:
            entry["prods2cs_listeners"] = listeners
            # Include remote listeners for transparency to user
        self.s2ds.update_listeners(listeners, entry["s2ds_proc"], request.uid, request.role)
        response = scistream_pb2.Response(listeners=entry["listeners"], prod_listeners=listeners)
        return response

    @request_decorator
    @authenticated
    def release(self, request, context=None):
        """
        Handles the 'release' gRPC request. Releases resources associated with the given request ID.
        """
        self.release_request(request.uid)       # Release resources associated with the request ID
        response = scistream_pb2.Response()     # Create an empty response to indicate success
        return response

    # Release all resources used by a particular request
    def release_request(self, uid):
        """
        Releases all resources associated with the specified request ID.
        """
        removed_item = self.resource_map.pop(uid, None)     # Remove the entry (resource) from the resource map
        self.s2ds.release(removed_item)                     # Release resources associated with the entry
        self.logger.debug(f"Removed key: '{uid}' with entry: {removed_item}")

    def release_all(self):
        """
        Releases all resources for all request IDs.
        """
        uids = [i for i in self.resource_map]
        for i in uids:
            self.release_request(i)

    @authenticated
    @request_decorator
    def hello(self, request, context=None):
        """
        Handles the 'hello' gRPC request. Updates the 'prod_listeners' based on the request role,
        and sends a response with listener information.
        """
        ## Possible race condition here between REQ and HELLO
        entry = self.resource_map[request.uid]
        if request.role == "PROD":
            entry["prod_listeners"] = request.prod_listeners
            self.response = scistream_pb2.Response(listeners = entry["listeners"], prod_listeners = entry["prod_listeners"])
            AppResponse = scistream_pb2.AppResponse(message="Sending Prod listeners...")
            print("receiving ports")
            print(entry["listeners"])
            print("target ports")
            print(entry["prod_listeners"])
            print("DEBUG HERE")
            print(self.response)
        else:
            self.response = scistream_pb2.Response(listeners = entry["listeners"])
            print(entry["listeners"])
            print("DEBUG HERE")
            AppResponse = scistream_pb2.AppResponse(message="Sending listeners...",
                listeners = entry["listeners"])
        entry["hello_received"].set()
        return AppResponse

    def validate_creds(self, access_token):
        auth_state=self.checker.check_token(access_token)
        return len(auth_state.identities) > 0
        #return False

def start(listener_ip='0.0.0.0', port=5000, type= "S2DS", v=False, verbose=False, client_id=default_cid, client_secret=default_secret, version=False, server_crt=default_server_crt, server_key=default_server_key):
    """
    Starts a gRPC implementation of Scistream server.

    Args:
        listener_ip (str): IP address on which the server listens. Defaults to '0.0.0.0'.
        port (int): Port number on which the server listens. Defaults to 5000.
        type (str): Specifies the type of server to start. Options are 'S2DS', 'Nginx', 'Haproxy'.
                    'Haproxy' is the default type.
        v or verbose (bool): Enables basic verbosity. Defaults to False.
        client_id (str): Client ID for authentication. Defaults to value of 'default_cid'.
        client_secret (str): Client secret for authentication. Defaults to value of 'default_secret'.
        version (bool): Prints the version of the package.
        server_crt (str): Path to the server certificate file. Defaults to 'server.crt'.
        server_key (str): Path to the server key file. Defaults to 'server.key'.
    """
    if version:
        print(f"s2cs, version: {__version__}")
        return
    with open(server_key, 'rb') as f:
        private_key = f.read()
    with open(server_crt, 'rb') as f:
        certificate_chain = f.read()
    server_credentials = grpc.ssl_server_credentials([(private_key, certificate_chain)])
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        servicer = S2CS(listener_ip, (v or verbose), type, client_id, client_secret)
        scistream_pb2_grpc.add_ControlServicer_to_server(servicer, server)
        server.add_secure_port(f'[::]:{port}', server_credentials)
        server.start()
        print(f"Secure Server started on {listener_ip}:{port}")
        server.wait_for_termination()
    except KeyboardInterrupt:
        servicer.release_all()
        print("\nTerminating server")
        sys.exit(0)

def main():
    fire.Fire(start)

if __name__ == '__main__':
        main()
