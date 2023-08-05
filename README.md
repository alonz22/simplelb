# SimpleLB Load Balancer Service



![logo](https://github.com/alonz22/simplelb/assets/72250573/92189780-7664-4fcd-a47f-06d078690db8)



SimpleLB is a lightweight and efficient load balancer service designed to balance traffic on Layer 4 (Transport Layer) for your web applications or services. It provides essential features to manage traffic effectively and optimize the performance of your server infrastructure.

# Features
SimpleLB focuses on Layer 4 load balancing, allowing you to distribute incoming network traffic across multiple backend servers based on various algorithms such as round-robin, least connections, or IP hash.

## SSL Certificate Support
Secure your communication with clients using SSL certificates. SimpleLB supports SSL termination, enabling you to offload SSL encryption and decryption to the load balancer and pass unencrypted traffic to your backend servers.

## IP-Based Rate Limiting
To protect your servers from potential abuse or excessive traffic from specific IP addresses, SimpleLB provides an IP-based rate limiting feature. You can configure thresholds to put clients in penalty for an extended period if they exceed the allowed requests per second.

## Sticky Session
Enable sticky session support to ensure that client requests from the same IP address are consistently directed to the same backend server. This feature is useful for applications that rely on session persistence.

## Request Logging
SimpleLB offers detailed request logging, helping you monitor traffic patterns, analyze user behavior, and troubleshoot any issues that may arise. Log files include client IP addresses, requested URLs, response codes, and more.

## Limitations
Single Frontend and Backend (Current Limitation)
Currently, SimpleLB supports only one frontend and backend configuration. However, we are continuously working to enhance the load balancer's capabilities and plan to introduce the following features:

## Roadmap
Multiple Frontends and Backends
In the upcoming release, SimpleLB will support multiple frontend and backend configurations. You will be able to define multiple frontend listeners and associate them with different backend servers, allowing you to load balance traffic for multiple services simultaneously.

## Custom Response Headers
We understand the importance of customizing response headers to comply with specific application requirements or security policies. SimpleLB will allow you to define custom response headers, enabling you to add, modify, or remove headers for responses sent to clients.

## Getting Started
To use SimpleLB Load Balancer Service, follow these steps:

## Prerequisites:

Ensure you have Python 3.x installed on your server.
Install any necessary dependencies listed in the project's requirements.
Download and Setup:

Clone this repository to your server.
run ``` ./install.sh```
Modify the config.ini file in the /etc/simplelb/ directory to configure your load balancer settings, SSL certificates, and penalty thresholds.
Run the Load Balancer:


## Logging:

Review the access logs located at /var/log/simplelb_access.log to monitor user requests and server responses.
Log file contents is human readable and easy to understand.
Configuration
The config.ini file is the heart of SimpleLB's configuration. It provides options to customize the load balancer behavior, define SSL certificate paths, set penalty thresholds, and more. Refer to the comments in the file for detailed explanations of each option.
## Modifying the config file:
The config file, located at /etc/simplelb, contains a simple configuration syntax, as the following:
```
[frontend]

method = leastconn
frontend_ip = 0.0.0.0
frontend_port = 8080
#ssl_cert_file = /etc/haproxy/ssl/your-cert.com.pem
#ssl_key_file = /etc/haproxy/ssl/your-key.com.key
rate_limit_period = 2
rate_limit_max_requests = 8
penalty_duration = 10


[backend_servers]
server1 = 192.168.33.12:80
server2 = 192.168.33.13:80

[server1]
stickey_session_time = 15
active = yes

[server2]
stickey_session_time = 120
active = no



```
## Contributing
We welcome contributions from the community to make SimpleLB even better. If you encounter any issues, have feature requests, or want to contribute code, please check our Contributing Guidelines and open an issue or pull request.

## License
SimpleLB is released under the MIT License. You are free to use, modify, and distribute the software as per the terms of the license.

## Disclaimer
The SimpleLB Load Balancer Service is provided "as is," without warranty of any kind, express or implied. The authors and contributors of this software make no representations or warranties, either express or implied, including but not limited to warranties of merchantability, fitness for a particular purpose, or non-infringement. The entire risk arising out of the use or performance of the software remains with you.

In no event shall the authors or contributors be liable for any damages whatsoever, including but not limited to direct, indirect, consequential, or any other damages arising out of the use or inability to use this software, even if advised of the possibility of such damages.

Use of SimpleLB Load Balancer Service is at your own risk. The software may not be suitable for every use, and its performance or behavior might not meet your expectations. It is your responsibility to review the source code and configuration settings before using the software in a production environment.



## Acknowledgments
We would like to express our gratitude to the open-source community for their continuous support and contributions.

Thank you for choosing SimpleLB Load Balancer Service!

SimpleLB logo designed by Alon Zur.
