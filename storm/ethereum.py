"""
RPC flood testing module for Storm
"""

import asyncio
import json
import random
import time
from typing import Dict, List, Any, Optional, Tuple, Set
import aiohttp
import uuid
import colorama
from colorama import Fore, Style
from tqdm import tqdm
import os
import datetime
from .ethereum_params import ParameterGenerator

# Initialize colorama
colorama.init()

class RPCFloodTester:
    """
    Flood tester for JSON-RPC API
    """

    def __init__(
        self, 
        url: str, 
        requests_per_second: int = 100, 
        methods: Optional[List[str]] = None,
        verbose: bool = False
    ):
        self.url = url
        self.requests_per_second = requests_per_second
        self.methods = methods
        self.verbose = verbose
        self.session = None
        self.request_id = 0
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "errors_by_method": {},
            "requests_by_method": {},
            "min_response_time": float('inf'),
            "max_response_time": 0,
            "total_response_time": 0,
            "available_methods": [],
            "unavailable_methods": [],
        }
        
        # Initialize parameter generator
        self.param_generator = ParameterGenerator()
        
        # Define all available methods and their parameters
        self.available_methods = self.param_generator.get_available_methods()
        
        # If methods are specified, filter the available methods
        if methods:
            self.available_methods = {
                method: params_generator 
                for method, params_generator in self.available_methods.items() 
                if method in methods
            }
        
        # Create log directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Create a log file for failed requests
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"logs/eth_failed_requests_{timestamp}.log"
        
        # Log file header
        with open(self.log_file, "w") as f:
            f.write(f"# ETH RPC Failed Requests Log\n")
            f.write(f"# Target: {url}\n")
            f.write(f"# Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Methods: {', '.join(self.available_methods.keys()) if methods else 'All'}\n")
            f.write(f"# Format: [timestamp] method | request | response/error\n\n")
        
        # Sample addresses, block hashes, and transaction hashes for testing
        self.sample_addresses = [
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # vitalik.eth
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
            "0x0000000000000000000000000000000000000000",  # Zero address
        ]
        
        self.sample_block_hashes = [
            "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3",  # Genesis block
            "0x88e96d4537bea4d9c05d12549907b32561d3bf31f45aae734cdc119f13406cb6",
            "0xb495a1d7e6663152ae92708da4843337b958146015a2802f4193a410044698c9",
            "0x0000000000000000000000000000000000000000000000000000000000000000",  # Invalid hash
        ]
        
        self.sample_tx_hashes = [
            "0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060",
            "0x2cc6c94c21685b7e0f8ddabf277a5ccf98db157c62619cde8baea696a74ed18e",
            "0x0000000000000000000000000000000000000000000000000000000000000000",  # Invalid hash
        ]
        
        self.sample_block_numbers = [
            "0x0",  # Genesis block
            "0x1",  # Block 1
            "0xa",  # Block 10
            "0x100",  # Block 256
            "0x1000000",  # Block 16777216
            "latest",
            "pending",
            "earliest",
        ]
        
        self.sample_filter_ids = [
            "0x1",
            "0x2",
            "0x3",
            "0x0",
            "0x10",
            "0x100",
            "0xffffffffffffffff",
            "0x0000000000000000",
        ]

    async def _send_request(self, method: str) -> Tuple[bool, float]:
        """
        Send a JSON-RPC request to the node
        
        Args:
            method: The method to call
            
        Returns:
            Tuple of (success, response_time)
        """
        # Generate parameters for the method
        params_generator = self.available_methods[method]
        params = params_generator()
        
        # Create the JSON-RPC request
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id
        }
        
        start_time = time.time()
        try:
            async with self.session.post(self.url, json=request) as response:
                response_text = await response.text()
                response_time = time.time() - start_time
                
                if response.status == 200:
                    try:
                        response_json = json.loads(response_text)
                        if "error" in response_json:
                            # Log failed request
                            self._log_failed_request(method, request, response_json)
                            if self.verbose:
                                print(f"\nError for method {method}: {response_json['error']}")
                            return False, response_time
                        else:
                            if self.verbose:
                                print(f"\nRequest: {json.dumps(request)}")
                                print(f"Response: {response_text}")
                            return True, response_time
                    except json.JSONDecodeError:
                        # Log failed request
                        self._log_failed_request(method, request, f"Invalid JSON: {response_text}")
                        if self.verbose:
                            print(f"\nInvalid JSON response for method {method}: {response_text}")
                        return False, response_time
                else:
                    # Log failed request
                    self._log_failed_request(method, request, f"HTTP {response.status}: {response_text}")
                    if self.verbose:
                        print(f"\nError for method {method}: {response.status} - {response_text}")
                    return False, response_time
        
        except Exception as e:
            # Log failed request
            self._log_failed_request(method, request, f"Exception: {str(e)}")
            if self.verbose:
                print(f"\nException for method {method}: {str(e)}")
            return False, time.time() - start_time
    
    def _log_failed_request(self, method: str, request: Dict, error: Any):
        """
        Log a failed request to the log file
        
        Args:
            method: The method that failed
            request: The request that was sent
            error: The error response or exception
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] {method}\n")
            f.write(f"Request: {json.dumps(request, indent=2)}\n")
            f.write(f"Error: {json.dumps(error, indent=2) if isinstance(error, dict) else str(error)}\n")
            f.write("-" * 80 + "\n\n")

    async def _test_method_availability(self):
        """Test which methods are available"""
        available_methods = []
        unavailable_methods = []
        
        with tqdm(total=len(self.available_methods), desc="Testing methods", unit="method") as pbar:
            for method in self.available_methods:
                success, _ = await self._send_request(method)
                if success:
                    available_methods.append(method)
                    self.stats["requests_by_method"][method] = 0
                else:
                    unavailable_methods.append(method)
                pbar.update(1)
        
        self.stats["available_methods"] = available_methods
        self.stats["unavailable_methods"] = unavailable_methods

    async def run(self, duration: int = 60) -> Dict[str, Any]:
        """
        Run the flood tester for the specified duration
        
        Args:
            duration: Duration in seconds
            
        Returns:
            Statistics about the run
        """
        print(f"{Fore.CYAN}Starting RPC flood testing against {Fore.YELLOW}{self.url}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Requests per second: {Fore.YELLOW}{self.requests_per_second}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Duration: {Fore.YELLOW}{duration} seconds{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Methods: {Fore.YELLOW}{', '.join(self.available_methods.keys()) if self.methods else 'All'}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Failed requests will be logged to: {Fore.YELLOW}{self.log_file}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Press Ctrl+C to stop{Style.RESET_ALL}\n")
        
        self.session = aiohttp.ClientSession()
        
        # Test which methods are available before starting the flood testing
        print(f"{Fore.CYAN}Testing method availability...{Style.RESET_ALL}")
        await self._test_method_availability()
        
        if not self.stats["available_methods"]:
            print(f"{Fore.RED}No methods available. Exiting.{Style.RESET_ALL}")
            await self.session.close()
            return self.stats
            
        print(f"{Fore.GREEN}Available methods: {Fore.YELLOW}{', '.join(self.stats['available_methods'])}{Style.RESET_ALL}")
        if self.stats["unavailable_methods"]:
            print(f"{Fore.RED}Unavailable methods: {Fore.YELLOW}{', '.join(self.stats['unavailable_methods'])}{Style.RESET_ALL}")
        
        # Filter available_methods to only include those that are actually available
        self.available_methods = {
            method: params_generator 
            for method, params_generator in self.available_methods.items() 
            if method in self.stats["available_methods"]
        }
        
        # Record start time
        self.stats["start_time"] = time.time()
        end_time = self.stats["start_time"] + duration
        
        # Create a progress bar
        with tqdm(total=duration, desc="Testing progress", unit="s") as pbar:
            try:
                while time.time() < end_time:
                    start_loop = time.time()
                    
                    # Create tasks for this batch
                    tasks = []
                    methods_for_this_batch = []
                    
                    for _ in range(self.requests_per_second):
                        # Select a random method
                        method = random.choice(list(self.available_methods.keys()))
                        methods_for_this_batch.append(method)
                        tasks.append(self._send_request(method))
                    
                    # Execute tasks
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Update statistics
                    for result, method in zip(results, methods_for_this_batch):
                        self.stats["total_requests"] += 1
                        self.stats["requests_by_method"][method] = self.stats["requests_by_method"].get(method, 0) + 1
                        
                        if isinstance(result, Exception):
                            self.stats["failed_requests"] += 1
                            self.stats["errors_by_method"][method] = self.stats["errors_by_method"].get(method, 0) + 1
                            # Log failed request
                            self._log_failed_request(method, {"method": method, "error": str(result)}, f"Exception: {str(result)}")
                            if self.verbose:
                                print(f"{Fore.RED}Error in {method}: {str(result)}{Style.RESET_ALL}")
                        else:
                            success, response_time = result
                            if success:
                                self.stats["successful_requests"] += 1
                                self.stats["total_response_time"] += response_time
                                if response_time < self.stats["min_response_time"]:
                                    self.stats["min_response_time"] = response_time
                                if response_time > self.stats["max_response_time"]:
                                    self.stats["max_response_time"] = response_time
                            else:
                                self.stats["failed_requests"] += 1
                                self.stats["errors_by_method"][method] = self.stats["errors_by_method"].get(method, 0) + 1
                    
                    # Sleep to maintain the requests per second rate
                    elapsed = time.time() - start_loop
                    if elapsed < 1.0:
                        await asyncio.sleep(1.0 - elapsed)
                    
                    # Update progress bar
                    pbar.update(1)
            
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Test interrupted by user.{Style.RESET_ALL}")
        
        # Record end time
        self.stats["end_time"] = time.time()
        
        # Calculate average response time
        if self.stats["successful_requests"] > 0:
            self.stats["avg_response_time"] = self.stats["total_response_time"] / self.stats["successful_requests"]
        else:
            self.stats["avg_response_time"] = 0
        
        # Close the session
        await self.session.close()
        
        # Print report
        self._print_report()
        
        return self.stats
    
    def _print_report(self):
        """Print a report of the flood testing run"""
        terminal_width = os.get_terminal_size().columns
        
        print(f"\n{Fore.CYAN}{'=' * terminal_width}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'RPC FLOOD TESTING REPORT':^{terminal_width}}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * terminal_width}{Style.RESET_ALL}")
        
        # Calculate success rate
        success_rate = self.stats['successful_requests']/max(1, self.stats['total_requests'])*100
        success_color = Fore.GREEN if success_rate > 90 else Fore.YELLOW if success_rate > 70 else Fore.RED
        
        print(f"{Fore.CYAN}Target URL:{Style.RESET_ALL} {self.url}")
        print(f"{Fore.CYAN}Total requests:{Style.RESET_ALL} {self.stats['total_requests']}")
        print(f"{Fore.CYAN}Successful requests:{Style.RESET_ALL} {self.stats['successful_requests']} "
              f"({success_color}{success_rate:.1f}%{Style.RESET_ALL})")
        print(f"{Fore.CYAN}Failed requests:{Style.RESET_ALL} {self.stats['failed_requests']} "
              f"({Fore.RED}{self.stats['failed_requests']/max(1, self.stats['total_requests'])*100:.1f}%{Style.RESET_ALL})")
        print(f"{Fore.CYAN}Average response time:{Style.RESET_ALL} {self.stats['avg_response_time']*1000:.2f} ms")
        
        if self.stats["errors_by_method"]:
            print(f"\n{Fore.CYAN}Errors by method:{Style.RESET_ALL}")
            for method, errors in sorted(self.stats["errors_by_method"].items(), key=lambda x: x[1], reverse=True):
                error_rate = errors / max(1, self.stats['total_requests']) * 100
                error_color = Fore.RED if error_rate > 10 else Fore.YELLOW if error_rate > 5 else Fore.GREEN
                print(f"  {method}: {error_color}{errors} errors ({error_rate:.1f}%){Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{'=' * terminal_width}{Style.RESET_ALL}")
    
    async def _send_random_request(self) -> None:
        """
        Send a random JSON-RPC request to the node
        """
        # Select a random method
        method = random.choice(list(self.available_methods.keys()))
        
        # Generate parameters for the method
        params_generator = self.available_methods[method]
        params = params_generator()
        
        # Create the JSON-RPC request
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id
        }
        
        start_time = time.time()
        try:
            async with self.session.post(self.url, json=request) as response:
                response_text = await response.text()
                response_time = time.time() - start_time
                
                self.stats["total_requests"] += 1
                self.stats["total_response_time"] += response_time
                
                if response.status == 200:
                    self.stats["successful_requests"] += 1
                    if self.verbose:
                        print(f"\nRequest: {json.dumps(request)}")
                        print(f"Response: {response_text}")
                else:
                    self.stats["failed_requests"] += 1
                    if method not in self.stats["errors_by_method"]:
                        self.stats["errors_by_method"][method] = 0
                    self.stats["errors_by_method"][method] += 1
                    
                    if self.verbose:
                        print(f"\nError for method {method}: {response.status} - {response_text}")
        
        except Exception as e:
            self.stats["total_requests"] += 1
            self.stats["failed_requests"] += 1
            
            if method not in self.stats["errors_by_method"]:
                self.stats["errors_by_method"][method] = 0
            self.stats["errors_by_method"][method] += 1
            
            if self.verbose:
                print(f"\nException for method {method}: {str(e)}")
