#!/usr/bin/env python3
"""
Main module for Storm
"""

import argparse
import asyncio
import sys
from typing import List, Optional

from storm.ethereum import RPCFloodTester
from storm.abci import ABCIFloodTester

async def run_ethereum_test(url: str, requests_per_second: int = 100, duration: int = 60, methods: Optional[List[str]] = None, verbose: bool = False):
    """
    Run Ethereum RPC flood testing
    """
    tester = RPCFloodTester(url, requests_per_second, methods, verbose)
    await tester.run(duration)

async def run_abci_test(url: str, requests_per_second: int = 100, duration: int = 60, methods: Optional[List[str]] = None, verbose: bool = False):
    """
    Run ABCI RPC flood testing
    """
    tester = ABCIFloodTester(url, requests_per_second, methods, verbose)
    await tester.run(duration)

def main():
    """
    Main entry point for Storm
    """
    parser = argparse.ArgumentParser(description="Storm - RPC Flood Testing Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Ethereum subcommand
    eth_parser = subparsers.add_parser("eth", help="Run Ethereum RPC flood testing")
    eth_parser.add_argument("url", help="URL of the Ethereum JSON-RPC API")
    eth_parser.add_argument("-r", "--requests-per-second", type=int, default=100, help="Number of requests per second")
    eth_parser.add_argument("-d", "--duration", type=int, default=60, help="Duration of the test in seconds")
    eth_parser.add_argument("-m", "--methods", nargs="+", help="Methods to test (default: all)")
    eth_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # ABCI subcommand
    abci_parser = subparsers.add_parser("abci", help="Run ABCI RPC flood testing")
    abci_parser.add_argument("url", help="URL of the ABCI RPC endpoint")
    abci_parser.add_argument("-r", "--requests-per-second", type=int, default=100, help="Number of requests per second")
    abci_parser.add_argument("-d", "--duration", type=int, default=60, help="Duration of the test in seconds")
    abci_parser.add_argument("-m", "--methods", nargs="+", help="Methods to test (default: all)")
    abci_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.command == "eth":
        asyncio.run(run_ethereum_test(args.url, args.requests_per_second, args.duration, args.methods, args.verbose))
    elif args.command == "abci":
        asyncio.run(run_abci_test(args.url, args.requests_per_second, args.duration, args.methods, args.verbose))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 