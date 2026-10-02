# Concurrent File Sharing System with SDN

## Overview

A multi-user file-sharing system using TCP sockets, Python threading, Mininet, Open vSwitch, and an OS-Ken SDN controller.

The system supports:

- User authentication
- File listing
- File upload
- File download
- File metadata tracking
- Concurrent client connections
- SDN-based access control
- File-transfer performance testing

## Architecture

```text
              OS-Ken Controller
                     |
                 Open vSwitch
                     |
          +----------+----------+
          |          |          |
         h1         h2         h3
       Client     Client     Client
          \          |          /
           \         |         /
                File Server
                 10.0.0.4
## Files

| File | Purpose |
|---|---|
| `server.py` | Multi-threaded TCP file server |
| `client.py` | File-sharing client |
| `concurrent_client.py` | Concurrent transfer testing |
| `controller.py` | OS-Ken SDN controller |
| `topology.py` | SDN Mininet topology |
| `baseline_topology.py` | Baseline topology |
| `performance_test.py` | Transfer performance testing |
| `metadata.json` | File metadata |

## Requirements

- Ubuntu / WSL2
- Python 3
- Mininet
- Open vSwitch
- OS-Ken
- Git

## Running the Project

### Start the SDN Controller

```bash
cd ~/file-sharing-sdn
osken-manager controller.py

### Start Mininet

In another terminal:

```bash
cd ~/file-sharing-sdn
sudo python3 topology.py

### Start the File Server

Inside Mininet:

```text
server python3 /home/bsubr/file-sharing-sdn/server.py

### Test a Client

```text
h2 python3 /home/bsubr/file-sharing-sdn/concurrent_client.py

## SDN Access Control

The controller blocks TCP file-sharing traffic from:

```text
h1 (10.0.0.1) -> server (10.0.0.4):5000

## Concurrent Transfers

Multiple clients can connect to the server simultaneously because the server creates a separate thread for each client.

Example:

```text
h2 python3 /home/bsubr/file-sharing-sdn/concurrent_client.py &
h3 python3 /home/bsubr/file-sharing-sdn/concurrent_client.py

## Performance Testing

A 1 MiB test file was used to measure transfer time and throughput.

The project also includes a baseline Mininet topology without the SDN controller for comparison.

## Testing

The project was tested for:

- TCP communication
- Authentication
- File upload/download
- Metadata tracking
- Concurrent clients
- SDN access control
- Unauthorized access blocking
- Performance measurement
- Baseline comparison
