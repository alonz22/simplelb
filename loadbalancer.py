import socket
import threading
import configparser
import ssl
import time
import http.client
import logging
from logging.handlers import RotatingFileHandler

log_file = "/var/log/simplelb_access.log"
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

max_log_size = 10 * 1024 * 1024  # 10 MB in bytes

# Configure the rotating file handler
file_handler = RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=5)
file_handler.setLevel(logging.INFO)

# Create a formatter and attach it to the handler
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Get the root logger and add the file handler
logger = logging.getLogger()
logger.addHandler(file_handler)

# Load configuration from the config file
config = configparser.ConfigParser()
config.read("/etc/simplelb/config.ini")
backend_servers = config["backend_servers"]
load_balancing_method = config["frontend"]["method"]
rate_limit_period = int(config["frontend"]["rate_limit_period"])
penalty_duration = int(config["frontend"]["penalty_duration"])
rate_limit_max_requests = int(config["frontend"]["rate_limit_max_requests"])
frontend_ip = config["frontend"]["frontend_ip"]
frontend_port = int(config["frontend"]["frontend_port"])
ssl_cert_file = config["frontend"].get("ssl_cert_file", None)
ssl_key_file = config["frontend"].get("ssl_key_file", None)

# Dictionary to keep track of active connections for each backend server
active_connections = {server: 0 for server in backend_servers}

# Dictionary to store sticky sessions, mapping client IP to the backend server
sticky_sessions = {}

# Dictionary to store the status of each backend server (True for up, False for down)
backend_server_status = {server: True for server in backend_servers}

# Function to implement Layer 4 health check
def health_check():
    while True:
        time.sleep(5)  # Check server health every 5 seconds (adjust this as needed)

        for server, server_entry in backend_servers.items():
            backend_ip, backend_port = server_entry.split(":")
            backend_port = int(backend_port)

            try:
                # Try to connect to the backend server to check its health
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as health_socket:
                    health_socket.settimeout(2)  # Set a timeout for the connection attempt
                    health_socket.connect((backend_ip, backend_port))
                    backend_server_status[server] = True
            
            except (socket.error, socket.timeout):
                # If connection attempt fails, mark the server as down
                backend_server_status[server] = False
                logging.error(f"Error connecting to backend server {server}")

# Initialize and start the health check thread
health_check_thread = threading.Thread(target=health_check)
health_check_thread.daemon = True
health_check_thread.start()

def leastconn_balancer(client_ip):
    # Check if there is a sticky session for the client
    if client_ip in sticky_sessions and sticky_sessions[client_ip] in backend_servers:
        backend_server = sticky_sessions[client_ip]
        if backend_server_status[backend_server]:
            return backend_server, backend_servers[backend_server]

    # If no sticky session or the previous server is down, use the least connections balancer
    for server in sorted(backend_servers, key=lambda x: (active_connections[x], backend_server_status[x])):
        if backend_server_status[server]:
            return server, backend_servers[server]

# Function to implement round-robin load balancing
current_server_index = 0

def round_robin_balancer(client_ip):
    # Access the global backend_server_status variable
    global backend_server_status

    # Check if there is a sticky session for the client
    if client_ip in sticky_sessions and sticky_sessions[client_ip] in backend_servers:
        backend_server = sticky_sessions[client_ip]
        if backend_server_status[backend_server]:
            return backend_server, backend_servers[backend_server]

    # If no sticky session or the previous server is down, use the round-robin balancer
    global current_server_index
    backend_servers_list = list(backend_servers.items())
    server_count = len(backend_servers_list)
    backend_server_name = backend_servers_list[current_server_index % server_count][0]
    backend_server_entry = backend_servers[backend_server_name]
    current_server_index += 1

    # Save sticky session for the client
    sticky_sessions[client_ip] = backend_server_name

    return backend_server_name, backend_server_entry

sticky_sessions = {}

# Function to implement sticky session
def sticky_session_balancer(client_ip):
    if client_ip in sticky_sessions and backend_server_status[sticky_sessions[client_ip]]:
        backend_server_name = sticky_sessions[client_ip]
    else:
        backend_server_name, _ = leastconn_balancer(client_ip)

    return backend_server_name, backend_servers[backend_server_name]

#RATE_LIMIT_PERIOD = 2  # Rate limit period in seconds
#RATE_LIMIT_MAX_REQUESTS = 6  # Maximum allowed requests in the rate limit period
#PENALTY_DURATION = 5  # Penalty duration in seconds

# Dictionary to track the request timestamps for each client IP
client_request_times = {}

# Set to track IP addresses under penalty (Forbidden) and their penalty expiration times
penalty_ips = {}



def handle_client(client_socket, client_ip):
    # Check if the IP address is under penalty (Forbidden) and if the penalty has expired
    if client_ip in penalty_ips and penalty_ips[client_ip] >= time.time():
        print(f"Request from {client_ip} is still under penalty. Waiting for 10 seconds.")
        client_socket.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\n")
        client_socket.close()
        logger.info(f"Request from {client_ip} is still under penalty. Waiting for 10 seconds.")
        return
    # Check if there is an existing sticky session for the client
    if client_ip in sticky_sessions and backend_server_status[sticky_sessions[client_ip]]:
        backend_server_name = sticky_sessions[client_ip]
    else:
        # If no sticky session or the previous server is down, use the load balancer
        backend_server_name, backend_server_entry = sticky_session_balancer(client_ip)
        # Store the sticky session information even if the server is down
        sticky_sessions[client_ip] = backend_server_name

    print(f"Request from {client_ip} goes to backend server: {backend_server_name}")
    logger.info(f"Request from {client_ip} goes to backend server: {backend_server_name}")
    request = client_socket.recv(1024)
    # Rate limiting logic
    current_time = time.time()
    if client_ip not in client_request_times:
        client_request_times[client_ip] = [current_time]
    else:
        # Remove the request timestamps older than 2 seconds
        client_request_times[client_ip] = [t for t in client_request_times[client_ip] if current_time - t <= rate_limit_period]

    # Check if the number of requests in the rate limit period exceeds the maximum allowed
    if len(client_request_times[client_ip]) >= rate_limit_max_requests:
        print(f"Rate limit exceeded for {client_ip}. Putting under penalty.")
        logger.info(f"Rate limit exceeded for {client_ip}. Putting under penalty.")
        penalty_ips[client_ip] = current_time + penalty_duration  # Set the penalty expiration time
        client_socket.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\n")
        client_socket.close()

        return
    request_str = request.decode()

    # Extract the requested path from the HTTP request
    request_lines = request_str.split("\r\n")
    if request_lines:
        # The first line should contain the request method and path
        first_line = request_lines[0]
        method, path, _ = first_line.split()

        # Log the request path
        print(f"Request from {client_ip} for path: {path}")
        logger.info(f"Request from {client_ip} for path: {path}")
    # Add the current request timestamp to the list
    client_request_times[client_ip].append(current_time)

    # Extract IP address and port number from the backend_server entry
    backend_ip, backend_port = backend_servers[backend_server_name].split(":")
    backend_port = int(backend_port)

    # Connect to the selected backend server
    backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    backend_socket.connect((backend_ip, backend_port))

    # Increment the active connections count for the selected backend server
    active_connections[backend_server_name] += 1

    # Forward the client request to the backend server

    backend_socket.sendall(request)
    
    # Receive the response from the backend server
    response = backend_socket.recv(100000000)
    
    client_socket.sendall(response)

    # Decrement the active connections count for the selected backend server
    active_connections[backend_server_name] -= 1

    # Close the sockets
    client_socket.close()
    backend_socket.close()


def main():
    # Create and bind the plain HTTP socket
    lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lb_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lb_socket.bind((frontend_ip, frontend_port))
    lb_socket.listen(10)

    print(f"Load Balancer listening on {frontend_ip}:{frontend_port} (HTTP)")
    logger.info(f"Load Balancer listening on {frontend_ip}:{frontend_port} (HTTP)")
    # Handle incoming HTTP connections
    while True:
        client_socket, client_address = lb_socket.accept()
        print(f"Accepted HTTP connection from {client_address[0]}:{client_address[1]}")
        logger.info(f"Accepted HTTP connection from {client_address[0]}:{client_address[1]}")
        # Extract the client IP address from the client_address tuple
        client_ip = client_address[0]

        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_ip))
        client_handler.start()

    # Check if SSL certificate and key are configured
    if ssl_cert_file and ssl_key_file:
        try:
            # Create and bind the SSL socket
            lb_ssl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            lb_ssl_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            lb_ssl_socket.bind((frontend_ip, frontend_port))
            lb_ssl_socket.listen(10)

            # Load SSL certificate and key
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(certfile=ssl_cert_file, keyfile=ssl_key_file)

            # Disable certificate verification for self-signed certificates
            ssl_context.verify_mode = ssl.CERT_NONE

            # Wrap the SSL socket with SSL
            lb_ssl_socket = ssl_context.wrap_socket(lb_ssl_socket, server_side=True)

            print(f"Load Balancer listening on {frontend_ip}:{frontend_port} (HTTPS)")
            logger.info(f"Load Balancer listening on {frontend_ip}:{frontend_port} (HTTPS)")
            # Handle incoming HTTPS connections
            while True:
                client_socket, client_address = lb_ssl_socket.accept()
                print(f"Accepted HTTPS connection from {client_address[0]}:{client_address[1]}")
                logger.info(f"Accepted HTTPS connection from {client_address[0]}:{client_address[1]}")
                client_ip = client_address[0]
                client_handler = threading.Thread(target=handle_client, args=(client_socket, client_ip))
                client_handler.start()
        except FileNotFoundError as e:
            print("Error: SSL certificate or key file not found.")
            logger.info(f"Error: SSL certificate or key file not found.")
            return
    else:
        print(f"SSL certificate and key not configured. HTTPS not enabled.")
        logger.info(f"SSL certificate and key not configured. HTTPS not enabled.")
if __name__ == "__main__":
    if load_balancing_method == "round_robin":
        load_balancer = round_robin_balancer
    elif load_balancing_method == "leastconn":
        load_balancer = leastconn_balancer
    else:
        print(f"Unsupported load balancing method: {load_balancing_method}")
        logger.info(f"Unsupported load balancing method: {load_balancing_method}.")
        exit(1)

    main()
