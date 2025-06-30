#!/bin/bash

# Health Monitoring System - Development Environment Setup Script
# This script sets up the local development environment

set -e

echo "🏥 Setting up Health Monitoring System Development Environment"
echo "============================================================="

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
port_available() {
    ! nc -z localhost $1 >/dev/null 2>&1
}

# Check prerequisites
print_step "Checking prerequisites..."

MISSING_DEPS=()

if ! command_exists docker; then
    MISSING_DEPS+=("docker")
fi

if ! command_exists docker-compose; then
    MISSING_DEPS+=("docker-compose")
fi

if ! command_exists python3; then
    MISSING_DEPS+=("python3")
fi

if ! command_exists node; then
    MISSING_DEPS+=("node")
fi

if ! command_exists java; then
    MISSING_DEPS+=("java")
fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    print_error "Missing required dependencies: ${MISSING_DEPS[*]}"
    echo "Please install the missing dependencies and run this script again."
    exit 1
fi

print_status "All prerequisites are installed ✓"

# Check ports
print_step "Checking port availability..."

REQUIRED_PORTS=(3306 6379 8086 9200 5601 5000 8080 3000 5173)
BUSY_PORTS=()

for port in "${REQUIRED_PORTS[@]}"; do
    if ! port_available $port; then
        BUSY_PORTS+=($port)
    fi
done

if [ ${#BUSY_PORTS[@]} -ne 0 ]; then
    print_warning "The following ports are busy: ${BUSY_PORTS[*]}"
    print_warning "Please stop services using these ports or modify the configuration."
fi

# Create environment files
print_step "Creating environment configuration files..."

# Edge client config
mkdir -p edge-client/config
cat > edge-client/config/development.json << 'EOF'
{
  "device_id": "edge-device-dev-001",
  "federation_server_url": "http://localhost:5000",
  "backend_api_url": "http://localhost:8080",
  
  "sensors": {
    "heart_rate": {
      "enabled": true,
      "pin": null,
      "simulation_mode": true
    },
    "spo2": {
      "enabled": true,
      "i2c_address": 87,
      "simulation_mode": true
    },
    "activity": {
      "enabled": true,
      "i2c_address": 106,
      "simulation_mode": true
    }
  },
  
  "model_dir": "models",
  "log_level": "INFO",
  "sensor_sampling_interval": 1.0,
  
  "transmission": {
    "batch_size": 10,
    "interval_seconds": 30,
    "encryption_enabled": true
  },
  
  "federated_learning": {
    "update_interval_hours": 1,
    "min_samples_for_update": 10,
    "privacy_budget": 1.0,
    "noise_multiplier": 0.1
  },
  
  "encryption": {
    "key": "development-key-change-in-production",
    "algorithm": "AES-256-GCM"
  }
}
EOF

# Federation server config
cat > federation-server/.env << 'EOF'
FLASK_ENV=development
DATABASE_URL=mysql://health_user:health_password@localhost:3306/health_monitoring
REDIS_URL=redis://localhost:6379
ENCRYPTION_KEY=development-key-change-in-production
LOG_LEVEL=DEBUG
EOF

# Backend application config
cat > backend/src/main/resources/application-development.yml << 'EOF'
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/health_monitoring
    username: health_user
    password: health_password
  
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: true
  
  data:
    redis:
      host: localhost
      port: 6379

app:
  influxdb:
    url: http://localhost:8086
    token: development-token
    org: health-monitoring
    bucket: health-metrics
  
  federation:
    server-url: http://localhost:5000
    api-key: development-api-key

logging:
  level:
    com.healthmonitoring: DEBUG
EOF

# Web portal config
cat > web-portal/.env.development << 'EOF'
VITE_API_BASE_URL=http://localhost:8080
VITE_WEBSOCKET_URL=ws://localhost:8080/ws
VITE_FEDERATION_SERVER_URL=http://localhost:5000
EOF

# Mobile app config
cat > mobile-app/.env << 'EOF'
API_BASE_URL=http://localhost:8080
WEBSOCKET_URL=ws://localhost:8080/ws
FIREBASE_PROJECT_ID=health-monitoring-dev
EOF

print_status "Environment configuration files created ✓"

# Setup Python virtual environments
print_step "Setting up Python virtual environments..."

# Edge client
cd edge-client
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Created Python virtual environment for edge client"
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
print_status "Edge client Python dependencies installed ✓"
cd ..

# Federation server
cd federation-server
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Created Python virtual environment for federation server"
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
print_status "Federation server Python dependencies installed ✓"
cd ..

# Setup Node.js dependencies
print_step "Setting up Node.js dependencies..."

# Web portal
cd web-portal
npm install
print_status "Web portal Node.js dependencies installed ✓"
cd ..

# Mobile app
cd mobile-app
npm install
print_status "Mobile app Node.js dependencies installed ✓"
cd ..

# Setup Java dependencies
print_step "Setting up Java dependencies..."

cd backend
./mvnw dependency:resolve
print_status "Backend Java dependencies resolved ✓"
cd ..

# Start infrastructure services
print_step "Starting infrastructure services..."

docker-compose up -d mysql influxdb redis elasticsearch kibana prometheus grafana

print_status "Waiting for services to be ready..."
sleep 30

# Initialize database
print_step "Initializing database..."

# Wait for MySQL to be ready
until docker-compose exec mysql mysqladmin ping -h"localhost" --silent; do
    print_status "Waiting for MySQL..."
    sleep 2
done

# Create database schema
docker-compose exec mysql mysql -u root -prootpassword -e "
CREATE DATABASE IF NOT EXISTS health_monitoring;
GRANT ALL PRIVILEGES ON health_monitoring.* TO 'health_user'@'%';
FLUSH PRIVILEGES;
"

print_status "Database initialized ✓"

# Setup InfluxDB
print_step "Setting up InfluxDB..."

# Wait for InfluxDB to be ready
sleep 10

# Setup InfluxDB (this would normally be done through the UI or CLI)
print_status "InfluxDB setup completed (manual setup required via UI) ✓"

# Create model directories
print_step "Creating model directories..."

mkdir -p edge-client/models
mkdir -p federation-server/models

# Create dummy model files for development
cat > edge-client/models/README.md << 'EOF'
# Model Directory

This directory contains TensorFlow Lite models for edge inference.
In development mode, dummy models are used for testing.

## Models:
- heart_rate_anomaly.tflite - Heart rate anomaly detection
- spo2_prediction.tflite - SpO2 level prediction  
- activity_recognition.tflite - Activity classification
EOF

print_status "Model directories created ✓"

# Setup monitoring configuration
print_step "Setting up monitoring configuration..."

mkdir -p config/prometheus
cat > config/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'federation-server'
    static_configs:
      - targets: ['federation-server:5000']
  
  - job_name: 'backend-api'
    static_configs:
      - targets: ['backend-api:8080']
    metrics_path: '/actuator/prometheus'
EOF

mkdir -p config/grafana/provisioning/dashboards
mkdir -p config/grafana/provisioning/datasources

cat > config/grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

print_status "Monitoring configuration created ✓"

# Final setup steps
print_step "Performing final setup steps..."

# Make scripts executable
chmod +x scripts/*.sh

# Create logs directory
mkdir -p logs

print_status "Development environment setup completed! ✓"

echo ""
echo "🎉 Development Environment Ready!"
echo "================================="
echo ""
echo "Services running:"
echo "  📊 MySQL:         http://localhost:3306"
echo "  📈 InfluxDB:      http://localhost:8086"
echo "  🔄 Redis:         http://localhost:6379"
echo "  🔍 Elasticsearch: http://localhost:9200"
echo "  📊 Kibana:        http://localhost:5601"
echo "  📈 Prometheus:    http://localhost:9090"
echo "  📊 Grafana:       http://localhost:3000 (admin/admin)"
echo ""
echo "To start the application services:"
echo "  🔧 Federation Server: cd federation-server && source venv/bin/activate && python app.py"
echo "  ⚙️  Backend API:       cd backend && ./mvnw spring-boot:run"
echo "  🌐 Web Portal:        cd web-portal && npm run dev"
echo "  📱 Mobile App:        cd mobile-app && npm start"
echo "  🔌 Edge Client:       cd edge-client && source venv/bin/activate && python edge_client.py"
echo ""
echo "Happy coding! 🚀"