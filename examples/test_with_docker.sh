#!/bin/bash
# Example script to test a local Ethereum node using Docker

# Make sure we're in the project root directory
cd "$(dirname "$0")/.." || exit

# Build the Docker image
echo "Building Docker image..."
docker build -t storm .

# Test with default settings
echo "Running basic test against local node..."
docker run storm eth http://host.docker.internal:8545 --duration 30

# Test with specific methods
echo "Testing specific methods..."
docker run storm eth http://host.docker.internal:8545 --methods eth_blockNumber,eth_getBalance,eth_call --duration 20

# Test with higher request rate
echo "Testing with higher request rate..."
docker run storm eth http://host.docker.internal:8545 --requests-per-second 200 --duration 20

# Test with verbose output
echo "Testing with verbose output..."
docker run storm eth http://host.docker.internal:8545 --verbose --duration 5 