#!/bin/bash
# Example script to test a local Ethereum node without installing Storm

# Make sure we're in the project root directory
cd "$(dirname "$0")/.." || exit

# Test with default settings
echo "Running basic test against local node..."
./run_storm.py eth http://localhost:8545 --duration 30

# Test with specific methods
echo "Testing specific methods..."
./run_storm.py eth http://localhost:8545 --methods eth_blockNumber,eth_getBalance,eth_call --duration 20

# Test with higher request rate
echo "Testing with higher request rate..."
./run_storm.py eth http://localhost:8545 --requests-per-second 200 --duration 20

# Test with verbose output
echo "Testing with verbose output..."
./run_storm.py eth http://localhost:8545 --verbose --duration 5 