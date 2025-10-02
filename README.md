# Telegraph
 A p2p messanger application

### Create python virtual environment
```bash
python3 -m venv venv
```

### Activate python virtual environment
```bash
source ./venv/bin/activate
```

### Update requirements.txt
```bash
pip freeze > requirements.txt
```

### Run the application

1. Build Images
```bash
# identity-manager
docker build -t src-identity-manager:latest ./identity-manager

# client
docker build -t src-client:latest ./client
```

2. Create a network
```bash
docker network create network_name
```

3. Run Identity Manager Container
```bash
docker run -d \
  --name identity-manager \
  --network network_name \
  -v $(pwd)/identity-manager/app:/app \
  -v $(pwd)/volumes/identity-data:/data \
  -p 8100:8000 \
  src-identity-manager:latest
```

4. Create as many clients as you need
```bash
docker run -d \
  --name client_name \
  --network network_name \
  -v $(pwd)/client/app:/app \
  -v $(pwd)/volumes/client_name-data:/data \
  -p port_on_host:5000 \
  -p port_on_host:8000 \
  -e USERNAME=client_name \
  -e PORT=5000 \
  -e API_PORT=8000 \
  src-client:latest
```

5. Remove containers (optional)
```bash
docker rm -f container_name
```