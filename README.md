# Distributed Load-Balanced Multi-Instance Architecture

[![CI/CD Pipeline](https://github.com/Aryan-Goyat/distributed-load-balancer-app/actions/workflows/ci.yml/badge.svg)](https://github.com/Aryan-Goyat/distributed-load-balancer-app/actions/workflows/ci.yml)
![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)
![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-Load--Balancer-009639.svg?logo=nginx&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688.svg?logo=fastapi&logoColor=white)
![AWS EC2](https://img.shields.io/badge/AWS-EC2%20Deployment-FF9900.svg?logo=amazon-aws&logoColor=white)

A production-grade demonstration of **horizontal scaling**, **reverse proxy load balancing**, and **distributed request routing**. This project deploys multiple containerized backend instances behind an **Nginx** reverse proxy running the **round-robin** distribution algorithm. It includes an automated test suite, GitHub Actions CI/CD with automatic push-blocking on failure, and full deployment instructions for AWS.

---

## Architecture

### System Flow
```
                         +-----------------------------+
                         |      Client / Browser       |
                         +--------------+--------------+
                                        |
                                        v  HTTP Port 80
                    +---------------------------------------+
                    |       Nginx Load Balancer Proxy       |
                    |       (Round-Robin Distribution)      |
                    +-------------------+-------------------+
                                        |
                          Alternating Request Routing
                                        |
                      +-----------------+-----------------+
                      |                                   |
                      v                                   v
           +--------------------+              +--------------------+
           | Backend Instance 1 |              | Backend Instance 2 |
           | (FastAPI - Alpha)  |              | (FastAPI - Beta)   |
           | Port: 8000 (app-1) |              | Port: 8000 (app-2) |
           +--------------------+              +--------------------+
                      |                                   |
                      +-----------------+-----------------+
                                        v
                          HTTP Response with Node ID:
                        {"instance_id": "backend-instance-alpha"}
                        {"instance_id": "backend-instance-beta"}
```

### Mermaid Architecture Diagram
```mermaid
graph TD
    User([Client / Web Browser / API Consumer]) -->|HTTP Port 80| LB[Nginx Reverse Proxy & Load Balancer]
    
    subgraph "Docker Bridge Network (app-net)"
        LB -->|Request 1, 3, 5... (Round-Robin)| App1["Backend Replica 1<br>(FastAPI - backend-instance-alpha)"]
        LB -->|Request 2, 4, 6... (Round-Robin)| App2["Backend Replica 2<br>(FastAPI - backend-instance-beta)"]
    end

    App1 -->|JSON + Node Stamp| User
    App2 -->|JSON + Node Stamp| User
```

---

## Key Distributed Systems Concepts Demonstrated

1. **Horizontal Scaling:** Instead of vertically scaling (increasing CPU/RAM on one machine), compute capacity is scaled outward across independent, stateless container replicas.
2. **Reverse Proxying & Decoupling:** Clients only interact with the unified Nginx gateway on port 80; backend topologies, ports, and internal networking remain hidden.
3. **Round-Robin Scheduling:** Inbound requests are systematically rotated across available healthy backends.
4. **Failure Resiliency & Upstream Retries:** Nginx monitors upstream health (`fail_timeout=10s`, `max_fails=3`). If an instance drops, `proxy_next_upstream` automatically re-routes the active request to a healthy peer with zero client interruption.
5. **Observability:** Each response explicitly stamps the unique `instance_id`, hostname, request sequence counter, and response header `X-Handled-By`.

---

## Project Structure

```
distributed-load-balancer-app/
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI workflow (blocks on test failure)
├── .githooks/
│       └── pre-push           # Git pre-push hook to block failing pushes locally
├── app/
│   ├── main.py                # FastAPI backend with health & instance tracking
│   └── requirements.txt       # Python backend and testing dependencies
├── nginx/
│   └── nginx.conf             # Upstream cluster and round-robin proxy config
├── tests/
│   └── test_app.py            # Automated test suite (6 comprehensive tests)
├── .gitignore                 # Standard Python & environment exclusions
├── Dockerfile                 # Multi-stage lightweight container definition
├── docker-compose.yml         # Multi-container orchestration stack
├── setup-hooks.ps1            # PowerShell script to activate git hooks
├── setup-hooks.sh             # Bash script to activate git hooks
└── README.md                  # System documentation & deployment guide
```

---

## API Endpoints

| Method | Endpoint | Description | Sample Output |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Root endpoint stamping instance ID and request count | `{"instance_id": "backend-instance-alpha", "request_count": 12, ...}` |
| `GET` | `/health` | Health check endpoint for monitoring/load balancers | `{"status": "healthy", "instance_id": "backend-instance-alpha", "uptime_seconds": 120.5}` |
| `GET` | `/stats` | Cumulative runtime metrics and request counter | `{"instance_id": "...", "total_requests_served": 45, ...}` |
| `POST` | `/api/echo` | Payload processor validating JSON body | `{"processed_by": "backend-instance-beta", "echo": {...}}` |
| `GET` | `/lb-health` | Load balancer direct diagnostic check | `{"load_balancer": "active", "algorithm": "round-robin"}` |

---

## Quickstart: Running Locally

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
- [Python 3.10+](https://www.python.org/) (optional for local testing)

### 1. Launch with Docker Compose
Run the following single command from the project root:
```bash
docker compose up -d --build
```

Verify that all three containers are healthy and running:
```bash
docker compose ps
```

### 2. Witness Load Balancing Live
Send sequential HTTP requests to the Load Balancer on port 80:

**On Linux / macOS:**
```bash
for i in {1..6}; do curl -s http://localhost/ | grep -o '"instance_id":"[^"]*' ; done
```

**On Windows (PowerShell):**
```powershell
1..6 | ForEach-Object { (Invoke-RestMethod -Uri http://localhost/).instance_id }
```

**Observed Output:**
```
backend-instance-alpha
backend-instance-beta
backend-instance-alpha
backend-instance-beta
backend-instance-alpha
backend-instance-beta
```
Notice how each request alternates perfectly between the two backend replicas!

### 3. Inspect Upstream Headers
```bash
curl -I http://localhost/
```
Output includes:
```http
HTTP/1.1 200 OK
Server: nginx/1.27.x
X-Handled-By: 172.28.0.2:8000
```

---

## Automated Testing & Push-Blocking Guardrails

The project includes **6 automated test cases** covering health checks, metadata generation, payload processing, 404 error handling, metrics tracking, and load balancing distribution logic:

- `test_health_check`: Validates `/health` returns 200 OK and healthy status.
- `test_instance_metadata`: Verifies `/` returns instance identity and monotonically increments request counters.
- `test_echo_payload_processing`: Verifies JSON deserialization and instance stamping.
- `test_error_handling_404`: Verifies structured error handling for nonexistent routes.
- `test_stats_endpoint`: Verifies cumulative performance telemetry.
- `test_load_balancer_round_robin_distribution`: Validates the round-robin distribution algorithm across backend clusters.

### Running Tests Locally
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate    # On Windows: .\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r app/requirements.txt

# Run pytest
pytest -v tests/
```

### How Failing Code is Blocked from Pushing

This project implements a **two-tier defense** against broken code:

#### Layer 1: Local Git Pre-Push Hook
Activate the pre-push hook:
- **Windows (PowerShell):** `.\setup-hooks.ps1`
- **Linux/macOS:** `./setup-hooks.sh`

When active, anytime a developer runs `git push`, the hook runs the test suite locally. If any test fails:
```
=============================================
 ❌ [PUSH BLOCKED] Tests failed!             
 You cannot push failing code to the remote. 
 Please resolve test failures first.         
=============================================
error: failed to push some refs to '...'
```

#### Layer 2: GitHub Actions CI/CD Pipeline (`.github/workflows/ci.yml`)
On every `push` and `pull_request` to `main`:
1. Checks out the code on `ubuntu-latest`.
2. Sets up Python 3.12 and installs dependencies.
3. Executes `pytest -v tests/`. If any test fails, the job immediately terminates with exit code 1.
4. If tests pass, builds Docker images and starts a live container cluster to perform end-to-end integration smoke tests.

---

## AWS Deployment Guide (Hands-On Exposure)

Deploy this architecture to **AWS Free Tier** using an Amazon EC2 instance:

### Step 1: Launch an AWS EC2 Instance
1. Log in to the [AWS Management Console](https://console.aws.amazon.com/).
2. Navigate to **EC2** > **Launch Instance**.
3. Configure the instance:
   - **Name:** `distributed-load-balancer-app`
   - **AMI:** Ubuntu Server 24.04 LTS (HVM), SSD Volume Type (Free Tier eligible).
   - **Instance Type:** `t2.micro` or `t3.micro` (Free Tier eligible).
   - **Key Pair:** Select an existing key pair or create a new one (download the `.pem` file).

### Step 2: Configure Security Group
In the **Network Settings** section, configure the following inbound rules:
| Type | Protocol | Port Range | Source | Description |
| :--- | :--- | :--- | :--- | :--- |
| **SSH** | TCP | 22 | My IP | Secure terminal administration |
| **HTTP** | TCP | 80 | Anywhere (0.0.0.0/0) | Public web traffic to Nginx Load Balancer |

### Step 3: Connect via SSH
Open your local terminal and connect:
```bash
chmod 400 your-key.pem   # Linux/macOS only
ssh -i "your-key.pem" ubuntu@<YOUR-EC2-PUBLIC-IP>
```

### Step 4: Install Docker & Docker Compose on EC2
Run the following script to set up Docker on Ubuntu:
```bash
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg git

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Apply group membership without logging out
newgrp docker
```

### Step 5: Deploy the Application
Clone your repository and start the cluster:
```bash
git clone https://github.com/Aryan-Goyat/distributed-load-balancer-app.git
cd distributed-load-balancer-app

# Launch the distributed container cluster in daemon mode
docker compose up -d --build
```

Verify the containers:
```bash
docker compose ps
```

### Step 6: Test from Your Web Browser or Terminal
Visit your EC2 public IP:
```
http://<YOUR-EC2-PUBLIC-IP>/
```
Refresh the page multiple times, or run from your local terminal:
```bash
for i in {1..8}; do curl http://<YOUR-EC2-PUBLIC-IP>/; echo ""; done
```
You will observe live round-robin distribution across `backend-instance-alpha` and `backend-instance-beta`!

### Step 7: Clean-Up (To Avoid Unwanted AWS Charges)
When finished:
```bash
# On the EC2 instance
docker compose down

# In AWS Console:
# EC2 Dashboard -> Instances -> Select Instance -> Instance State -> Terminate Instance
```

---

## License
MIT License. Open for educational and development use.
