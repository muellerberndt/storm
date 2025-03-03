#!/bin/bash
# Example script to test a local Ethereum node

# Make sure the directory exists
mkdir -p examples

# Test with default settings
echo "Running basic test against local node..."
storm eth http://localhost:8545

# Test with specific methods
echo "Testing specific methods..."
storm eth http://localhost:8545 --methods eth_blockNumber,eth_getBalance,eth_call --duration 30

# Test with higher request rate
echo "Testing with higher request rate..."
storm eth http://localhost:8545 --requests-per-second 200 --duration 30

# Test with verbose output
echo "Testing with verbose output..."
storm eth http://localhost:8545 --verbose --duration 10 