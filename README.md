# Storm

A tool for flood testing and light fuzzing of blockchain node APIs.

## Overview

Storm is designed to stress test blockchain nodes by sending a high volume of JSON-RPC requests with randomized parameters. It can help identify potential issues with node stability, performance, and error handling.

Currently supported RPC endpoints:
- Ethereum (ETH)
- CometBFT ABCI++ (ABCI)

## Installation

### Option 1: Install as a package

```bash
# Clone the repository
git clone https://github.com/yourusername/storm.git
cd storm

# Install the package
pip install -e .
```

### Option 2: Run without installation

You can also run Storm without installing it:

```bash
# Clone the repository
git clone https://github.com/yourusername/storm.git
cd storm

# Install dependencies
pip install -r requirements.txt

# Run using the standalone script
./run_storm.py eth http://localhost:8545
# Or for ABCI++
./run_storm.py abci http://localhost:26657
```

### Option 3: Run with Docker

You can run Storm in a Docker container:

```bash
# Clone the repository
git clone https://github.com/yourusername/storm.git
cd storm

# Build and run with docker-compose
docker-compose up

# Or build and run manually
docker build -t storm .
docker run storm eth http://host.docker.internal:8545
# Or for ABCI++
docker run storm abci http://host.docker.internal:26657
```

Note: Use `host.docker.internal` to access services running on your host machine from within the Docker container.

## Usage

Basic usage:

```bash
# For Ethereum
storm eth http://localhost:8545

# For ABCI++
storm abci http://localhost:26657

# If running without installation
./run_storm.py eth http://localhost:8545
./run_storm.py abci http://localhost:26657

# If running with Docker
docker run storm eth http://host.docker.internal:8545
docker run storm abci http://host.docker.internal:26657
```

This will send 100 requests per second for 60 seconds to the specified node.

### Options

```
# For Ethereum
storm eth <url> [options]
# or
./run_storm.py eth <url> [options]

# For ABCI++
storm abci <url> [options]
# or
./run_storm.py abci <url> [options]

Options:
  -r, --requests-per-second INT  Number of requests per second (default: 100)
  -d, --duration INT             Duration of the test in seconds (default: 60)
  -m, --methods METHODS          Space-separated list of methods to test (default: all)
  -v, --verbose                  Enable verbose output
```

### Examples

Test a specific set of Ethereum methods:

```bash
storm eth http://localhost:8545 -m eth_getBalance eth_blockNumber eth_call
```

Test specific ABCI++ methods:

```bash
storm abci http://localhost:26657 -m echo info query
```

Run a more intensive test:

```bash
storm eth http://localhost:8545 -r 500 -d 300
```

Show detailed request/response information:

```bash
storm eth http://localhost:8545 -v
```

## ABCI++ Support

Storm supports testing CometBFT ABCI++ endpoints with the following methods:

### Core ABCI Methods
- `echo` - Echo a message
- `flush` - Flush the response queue
- `info` - Get node information
- `initChain` - Initialize the blockchain
- `query` - Query the application state
- `checkTx` - Validate a transaction
- `beginBlock` - Begin a new block
- `deliverTx` - Deliver a transaction
- `endBlock` - End a block
- `commit` - Commit the block

### State Sync Methods
- `listSnapshots` - List available snapshots
- `loadSnapshotChunk` - Load a snapshot chunk
- `offerSnapshot` - Offer a snapshot
- `applySnapshotChunk` - Apply a snapshot chunk

### ABCI++ Methods
- `prepareProposal` - Prepare a proposal
- `processProposal` - Process a proposal

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
