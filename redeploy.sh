#!/bin/sh

# Default values
HA_TOKEN=""
HA_HOST=""
PORT=8080
CONTAINER_PORT=8080
RADIATION_INTERVAL=30
WATER_INTERVAL=30
ELECTRICITY_INTERVAL=30
COOLANT_INTERVAL=30
WEATHER_INTERVAL=600

# Parse arguments
while [ $# -gt 0 ]; do
    case "$1" in
        -t|--ha-token)
            HA_TOKEN="$2"
            shift 2
            ;;
        -h|--ha-host)
            HA_HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        -p|--container-port)
            CONTAINER_PORT="$2"
            shift 2
            ;;
        --radiation-interval)
            RADIATION_INTERVAL="$2"
            shift 2
            ;;
        --water-interval)
            WATER_INTERVAL="$2"
            shift 2
            ;;
        --electricity-interval)
            ELECTRICITY_INTERVAL="$2"
            shift 2
            ;;
        --coolant-interval)
            COOLANT_INTERVAL="$2"
            shift 2
            ;;
        --weather-interval)
            WEATHER_INTERVAL="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 -t TOKEN -h HOST [OPTIONS]"
            echo ""
            echo "Required arguments:"
            echo "  -t, --ha-token TOKEN              Home Assistant authentication token"
            echo "  -h, --ha-host HOST                Home Assistant host (IP or domain)"
            echo ""
            echo "Optional arguments:"
            echo "      --port PORT                   Application port (default: 8080)"
            echo "  -p, --container-port PORT         Docker host port (default: 8080)"
            echo "      --radiation-interval SECONDS  Radiation polling interval (default: 30)"
            echo "      --water-interval SECONDS      Water polling interval (default: 30)"
            echo "      --electricity-interval SEC    Electricity polling interval (default: 30)"
            echo "      --coolant-interval SECONDS    Coolant polling interval (default: 30)"
            echo "      --weather-interval SECONDS    Weather polling interval (default: 600)"
            echo ""
            echo "Example:"
            echo "  $0 -t 'your_token' -h 127.0.0.1"
            echo "  $0 -t 'your_token' -h 10.2.0.49 --radiation-interval 60 -p 9090"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$HA_TOKEN" ]; then
    echo "Error: Home Assistant token is required!"
    echo "Use: $0 -t TOKEN -h HOST"
    echo "Or use --help for more information"
    exit 1
fi

if [ -z "$HA_HOST" ]; then
    echo "Error: Home Assistant host is required!"
    echo "Use: $0 -t TOKEN -h HOST"
    echo "Or use --help for more information"
    exit 1
fi

# Display configuration
echo "========================================"
echo "Deployment Configuration:"
echo "========================================"
echo "HA_HOST:              $HA_HOST"
# Show only first 20 chars of token
TOKEN_PREFIX=$(echo "$HA_TOKEN" | cut -c1-20)
echo "HA_TOKEN:             ${TOKEN_PREFIX}..."
echo "PORT:                 $PORT"
echo "CONTAINER_PORT:       $CONTAINER_PORT"
echo "RADIATION_INTERVAL:   $RADIATION_INTERVAL seconds"
echo "WATER_INTERVAL:       $WATER_INTERVAL seconds"
echo "ELECTRICITY_INTERVAL: $ELECTRICITY_INTERVAL seconds"
echo "COOLANT_INTERVAL:     $COOLANT_INTERVAL seconds"
echo "WEATHER_INTERVAL:     $WEATHER_INTERVAL seconds"
echo "========================================"
echo ""

# Updating the Git repo
echo "Updating Git repo..."
git pull

# Building Docker image
echo "Building Docker image..."
docker build -t home_assistant_viewer -f Dockerfile .

# Stopping and removing the old container (if exists)
echo "Stopping and removing old container..."
docker stop home_assistant_viewer || true
docker rm home_assistant_viewer || true

# Deploying the new container
echo "Deploying new container..."
docker run --name home_assistant_viewer \
    --restart unless-stopped \
    -d \
    -p "$CONTAINER_PORT":8080 \
    --env HA_TOKEN="$HA_TOKEN" \
    --env HA_HOST="$HA_HOST" \
    --env PORT="$PORT" \
    --env RADIATION_INTERVAL="$RADIATION_INTERVAL" \
    --env WATER_INTERVAL="$WATER_INTERVAL" \
    --env ELECTRICITY_INTERVAL="$ELECTRICITY_INTERVAL" \
    --env COOLANT_INTERVAL="$COOLANT_INTERVAL" \
    --env WEATHER_INTERVAL="$WEATHER_INTERVAL" \
    home_assistant_viewer

echo ""
echo "========================================"
echo "Container deployed successfully!"
echo "========================================"
echo ""
echo "Useful commands:"
echo "  docker logs -f home_assistant_viewer    # View logs"
echo "  docker stop home_assistant_viewer       # Stop container"
echo "  docker start home_assistant_viewer      # Start container"
echo "  curl http://localhost:$CONTAINER_PORT/  # Test endpoint"
echo "  curl http://localhost:$CONTAINER_PORT/docs  # API documentation"
echo "  curl http://localhost:$CONTAINER_PORT/debug/cache  # View cache status"
