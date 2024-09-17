##### commented

##### command-line interface (CLI) application for interacting
# with Globus-based service, leveraging Click for CLI commands
# and gRPC for remote procedure calls.IT provides several CLI
# commands for authentication, managing tokens, and interacting
# with a gRPC service.

import click        # For creating the CLI interface
import grpc         # For gRPC communication
import uuid         # For generating unique UUIDs
import time         # For time-related functions
import sys          # For system-related functions
from .appcontroller import AppCtrl
from .appcontroller import IperfCtrl
from concurrent import futures                  # For concurrent execution of tasks
from globus_sdk import NativeAppAuthClient      # For authenticating with Globus
from globus_sdk.scopes import ScopeBuilder      # For building Globus scopes
from .proto import scistream_pb2                # For importing the gRPC service definition
from .proto import scistream_pb2_grpc           # For importing the gRPC service definition
from . import utils                             # For utility functions
import importlib.metadata                       # For getting (retrieving) the version of the package
__version__ = importlib.metadata.version('scistream-proto')

@click.group()                                  #  Defines a CLI group. Commands defined under this group will be accessible from the CLI
@click.version_option(__version__, '--version', '-v', help='Show the version and exit')
def cli():
    # Defines the cli function that acts as the entry point for the CLI.
    # It does nothing here but serves as a placeholder for CLI commands
    pass

linkprompt = "Please authenticate with Globus here"
def get_client():
    # Defines a function that returns an instance of NativeAppAuthClient
    # initialized with a client ID
    return NativeAppAuthClient('4787c84e-9c55-4881-b941-cb6720cea11c')

@cli.command()
@click.option('--scope', default="c42c0dac-0a52-408e-a04f-5d31bfe0aef8")    # Adds an option for the command to specify the scope
def login(scope):           # Defines the login function, which handles Globus authentication
    """
    Get globus credentials for the Scistream User Client.

    This command directs you to the page necessary to permit S2UC to make API
    calls for you, and gets the OAuth2 tokens needed to use those permissions.

    The CLI will print a link for you to manually follow to the Globus
    authorization page. After consenting you will then need to copy and paste the
    given access code from the web to the CLI.
    """
    adapter = utils.storage_adapter()           # Creates a storage adapter instance from the utils module to manage tokens
    try:
        tokens = utils.get_access_token(scope)  # Retrieves access tokens for the given scope
        if "INVALID_TOKEN" in tokens:
            raise utils.UnauthorizedError
        else:
            click.echo("You are already logged in, to try different credentials please log out!")
        return
    except utils.UnauthorizedError:
        click.echo("To obtain token for the scope, please open the URL in your browser and follow the instructions")

    auth_client = get_client()
    StreamScopes = ScopeBuilder(scope, known_url_scopes=["scistream"])      # Creates a ScopeBuilder instance with the specified scope
    auth_client.oauth2_start_flow(requested_scopes=[StreamScopes.scistream], refresh_tokens=True)       # Starts the OAuth2 flow for the requested scopes
    click.echo("{0}:\n{1}\n{2}\n{1}\n".format(
        linkprompt,
        "-" * len(linkprompt),
        auth_client.oauth2_get_authorize_url(query_params={"prompt": "login"})
        )
    )
    auth_code = click.prompt("Enter the resulting Authorization Code here").strip()
    tkn=auth_client.oauth2_exchange_code_for_tokens(auth_code)
    adapter.store(tkn)

@cli.command()
@click.option('--ip', default=None, help='IP address to fetch the scope and then get the access token.')
@click.option('--scope', default="c42c0dac-0a52-408e-a04f-5d31bfe0aef8", help='Directly provide the scope to get the access token.')
def check_auth(ip, scope):
    """
    Displays globus credentials for a given ip or scope.
    """
    if ip:
        scope = utils.get_scope_id(ip)
    if scope:
        token = utils.get_access_token(scope)
        click.echo(f"Access Token for scope '{scope}': {token}")

@cli.command()
def logout():
    """
    Logout of Globus

    This command both removes all tokens used for authenticating the user from local
    storage and revokes them so that they cannot be used anymore globally.
    """
    adapter = utils.storage_adapter()
    native_client = get_client()
    for rs, tokendata in adapter.get_by_resource_server().items():  # Iterates over the tokens stored in the adapter
        for tok_key in ("access_token", "refresh_token"):
            token = tokendata[tok_key]                              # Retrieves the token from the token data
            native_client.oauth2_revoke_token(token)                # Revokes the token
        adapter.remove_tokens_for_resource_server(rs)               # Removes the token from the adapter
    click.echo("Successfully logged out!")

@cli.command()
@click.argument('uid', type=str, required=True)
@click.option('--s2cs', default="localhost:5000")
@click.option('--server_cert', default="server.crt", help="Path to the server certificate file")
@utils.authorize        # Decorator to authorize the user. verify if the user has valid credentials
                        # or access rights to perform the action
def release(uid, s2cs, server_cert, metadata=None):
    try:
        with open(server_cert, 'rb') as f:
            trusted_certs = f.read()
        credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
        with grpc.secure_channel(s2cs, credentials) as channel:
            # establishes a secure gRPC channel to the server specified by the s2cs argument
            # (defaulting to "localhost:5000")
            stub = scistream_pb2_grpc.ControlStub(channel)
            # This creates a gRPC client stub (stub) for communicating with the server. 
            # scistream_pb2_grpc.ControlStub is a class generated by the gRPC framework
            # from the Protocol Buffers definitions. The stub is used to invoke the server’s
            # RPC methods.
            msg = scistream_pb2.Release(uid=uid)
            resp = stub.release(msg, metadata=metadata)
            # creates a Release message (msg) using scistream_pb2.Release, setting the uid field
            # of the message to the provided uid value. The release method on the server is then
            # called with the message (stub.release(msg)), and the server’s response is stored in
            # resp. metadata=metadata: If any additional metadata is provided (such as authorization
            # tokens), it is sent with the request
            print("Release completed")
    except Exception as e:
        print(f"Error during release: {e}")

@cli.command()
@click.option('--num_conn', type=int, default=5)
@click.option('--rate', type=int, default=10000)
@click.option('--s2cs', default="localhost:5000")
@click.option('--server_cert', default="server.crt", help="Path to the server certificate file")
@click.option('--mock', default=False)
@click.option('--scope', default="")
def prod_req(num_conn, rate, s2cs, server_cert, mock, scope):
    with open(server_cert, 'rb') as f:
        trusted_certs = f.read()
        credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
    with grpc.secure_channel(s2cs, credentials) as channel:
        prod_stub = scistream_pb2_grpc.ControlStub(channel)
        
        uid = str(uuid.uuid1()) if not mock else "4f8583bc-a4d3-11ee-9fd6-034d1fcbd7c3"
        click.echo("uid; s2cs; access_token; role")
        if scope == "":
            # If scope is not provided, it is determined dynamically via utils.get_scope_id(s2cs).
	        # An access token is fetched using utils.get_access_token(scope).
            scope = utils.get_scope_id(s2cs)
        click.echo(f"{uid} {s2cs} {utils.get_access_token(scope)} PROD")
        with futures.ThreadPoolExecutor(max_workers=2) as executor:
            # A ThreadPoolExecutor with 2 workers is created to handle asynchronous requests.
            # This allows concurrent execution in threads. It submits the task client_request
            # to be processed: 1) client_request is a function (not shown here) that probably
            # sends requests to the gRPC server using prod_stub, passing the uid, the role (“PROD”),
            # number of connections (num_conn), rate, and scope ID. 2) The result of the request
            # is stored in prod_resp. Note: The prod_resp_future.result() blocks until the client
            # request is complete and returns the result.
            click.echo("waiting for hello message")
            prod_resp_future = executor.submit(client_request, prod_stub, uid, "PROD", num_conn, rate, scope_id=scope)
            prod_resp = prod_resp_future.result()
        print(prod_resp)  # Should this be printed?
        # Extracting listeners
        # The server response (prod_resp) with information about listeners, which are stored in
        # variables prod_lstn and prod_app_lstn.
        prod_lstn = prod_resp.listeners
        prod_app_lstn = prod_resp.prod_listeners
        # Update the prod_stub
        update(prod_stub, uid, prod_resp.prod_listeners, "PROD", scope_id=scope)
        print(prod_resp.listeners)

@cli.command()
@click.option('--num_conn', type=int, default=5)
@click.option('--rate', type=int, default=10000)
@click.option('--s2cs', default="localhost:6000")
@click.option('--scope', default="")
@click.option('--server_cert', default="server.crt", help="Path to the server certificate file")
@click.argument("uid")
@click.argument("prod_lstn")
def cons_req(num_conn, rate, s2cs, scope, server_cert, uid, prod_lstn):  # uid and prod_lstn are dependencies from PROD context
    with open(server_cert, 'rb') as f:  
        trusted_certs = f.read()
        credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
    with grpc.secure_channel(s2cs, credentials) as channel:
        cons_stub = scistream_pb2_grpc.ControlStub(channel)
        if scope == "":
            scope = utils.get_scope_id(s2cs)
        click.echo(f"{uid} {s2cs} {utils.get_access_token(scope)} CONS")
        with futures.ThreadPoolExecutor(max_workers=2) as executor:
            cons_resp_future = executor.submit(client_request, cons_stub, uid, "CONS", num_conn, rate, scope_id=scope)
            cons_resp = cons_resp_future.result()
        cons_lstn = cons_resp.listeners
        # Update the cons_stub
        if ',' in prod_lstn:
            listener_array = prod_lstn.split(',')
        else:
            listener_array = [prod_lstn]
        update(cons_stub, uid, listener_array, "CONS", scope_id=scope)
        # prod_lstn is a dependency from PROD context


@utils.authorize        # This decorator ensures that the function is executed only after authorization.
                        # Checks that the user or system has the right credentials and permissions
                        # before making the gRPC request.
def client_request(stub, uid, role, num_conn, rate, scope_id="", metadata=None):
    """
    This behaves slightly different than release,
    release gets an IP:port tuple as input
    This receives the grpc stub
    Not sure what are the implications
    """
    try:
        print("started client request")
        request = scistream_pb2.Request(uid=uid, role=role, num_conn=num_conn, rate=rate)       # Creates a Request message with the provided uid, role, num_conn, and rate
        response = stub.req(request, metadata=metadata)         # Sends the request to the gRPC server via the req method on the stub, passing in the request and any additional metadata 
        return response
    except grpc.RpcError as e:
        # If the gRPC request encounters an error, the function catches the exception (grpc.RpcError)
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            click.echo(f"Please obtain new credentials: {e.details()}")
            sys.exit(1)
        else:
            click.echo(f"Another GRPC error occurred: {e.details()}")

@utils.authorize
def update(stub, uid, remote_listeners, role= "PROD", scope_id="", metadata=None):
    """This behaves very similar to client_request"""
    try:
        update_request = scistream_pb2.UpdateTargets(uid=uid, remote_listeners=remote_listeners, role=role)
        stub.update(update_request, metadata=metadata)
    except Exception as e:
        print(f"Error during update: {e}")

if __name__ == '__main__':
    #running code only when the script is executed directly (not imported as a module)
    cli()
    
# __name__: This is a special built-in variable in Python that holds the name of the module or script.
    # If a Python file is executed directly (e.g., python script.py), the value of __name__ in that
    # script will be set to "__main__".
	# If the file is imported as a module in another script, the value of __name__ will be set to the
    # module’s name (e.g., script).


    # e.g. script.py
    """
    def my_function():
        print("Hello from my_function!")

    if __name__ == '__main__':
        print("This script is running directly!")
        my_function()
    """
    """
    $ python script.py

    output:
    This script is running directly!
    Hello from my_function!
    """

    """
    # another_script.py
    import script

    output:
    <no output>
    No output! Because when script.py is imported, the value of __name__ in script.py is not
    "__main__", so the code inside the if __name__ == '__main__': block is not executed. However, any
    function (like my_function) in script.py is still available to be used within another_script.py
    """