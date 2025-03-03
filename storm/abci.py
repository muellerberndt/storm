"""
ABCI RPC flood testing module for Storm
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
import base64
from datetime import datetime
import sys

# Initialize colorama
colorama.init()

class ABCIFloodTester:
    """
    ABCI RPC flood testing implementation
    """
    
    def __init__(self, url: str, requests_per_second: int = 100, methods: Optional[List[str]] = None, verbose: bool = False):
        """
        Initialize the ABCI RPC flood tester
        
        Args:
            url: URL of the ABCI RPC endpoint
            requests_per_second: Number of requests per second to send
            methods: List of methods to test (default: all)
            verbose: Whether to print verbose output
        """
        self.url = url
        self.requests_per_second = requests_per_second
        self.verbose = verbose
        self.session = None
        self.request_id = 0
        
        # Define all available ABCI methods - use Tendermint RPC methods instead
        self.all_methods = [
            "abci_info", 
            "abci_query",
            "broadcast_tx_sync", 
            "broadcast_tx_async",
            "broadcast_tx_commit",
            "block", 
            "block_results",
            "blockchain", 
            "consensus_state",
            "status", 
            "net_info",
            "validators",
            "tx",
            "tx_search",
            "health",
            "commit",
            "genesis",
            "num_unconfirmed_txs",
            "unconfirmed_txs"
        ]
        
        # Use specified methods or all methods
        self.methods = methods if methods else self.all_methods
        
        # Validate methods
        for method in self.methods:
            if method not in self.all_methods:
                raise ValueError(f"Unknown ABCI method: {method}")
        
        # Initialize statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "requests_by_method": {},
            "errors_by_method": {},
            "min_response_time": float('inf'),
            "max_response_time": 0,
            "total_response_time": 0,
            "start_time": 0,
            "end_time": 0,
            "available_methods": set()
        }
        
        # Initialize request counters for each method
        for method in self.all_methods:
            self.stats["requests_by_method"][method] = 0
            self.stats["errors_by_method"][method] = 0
        
        # Parameter generators for different methods
        self.param_generators = {
            "abci_info": self._generate_abci_info_params,
            "abci_query": self._generate_abci_query_params,
            "broadcast_tx_sync": self._generate_broadcast_tx_params,
            "broadcast_tx_async": self._generate_broadcast_tx_params,
            "broadcast_tx_commit": self._generate_broadcast_tx_params,
            "block": self._generate_block_params,
            "block_results": self._generate_block_params,
            "blockchain": self._generate_blockchain_params,
            "consensus_state": self._generate_empty_params,
            "status": self._generate_empty_params,
            "net_info": self._generate_empty_params,
            "validators": self._generate_validators_params,
            "tx": self._generate_tx_params,
            "tx_search": self._generate_tx_search_params,
            "health": self._generate_empty_params,
            "commit": self._generate_commit_params,
            "genesis": self._generate_empty_params,
            "num_unconfirmed_txs": self._generate_empty_params,
            "unconfirmed_txs": self._generate_unconfirmed_txs_params
        }
        
        # Create log directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Create a log file for failed requests
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"logs/abci_failed_requests_{timestamp}.log"
        
        # Log file header
        with open(self.log_file, "w") as f:
            f.write(f"# ABCI RPC Failed Requests Log\n")
            f.write(f"# Target: {url}\n")
            f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Methods: {', '.join(self.methods)}\n")
            f.write(f"# Format: [timestamp] method | request | response/error\n\n")
    
    async def _create_session(self):
        """Create an aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def _close_session(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_request_id(self) -> int:
        """Get a unique request ID"""
        self.request_id += 1
        return self.request_id
    
    async def _check_service_availability(self) -> bool:
        """
        Check if the ABCI service is available at the specified URL
        
        Returns:
            bool: True if service is available, False otherwise
        """
        try:
            # Try a simple echo request to check if service is available
            request = {
                "jsonrpc": "2.0",
                "id": self._get_request_id(),
                "method": "echo",
                "params": {"message": "Storm ABCI Test"}
            }
            
            async with self.session.post(self.url, json=request, timeout=5) as response:
                return response.status == 200
        except Exception as e:
            if self.verbose:
                print(f"\n{Fore.RED}Error checking service availability: {str(e)}{Style.RESET_ALL}")
            return False
    
    async def _check_method_availability(self) -> Dict[str, bool]:
        """
        Check which methods are available on the ABCI service
        
        Returns:
            Dict[str, bool]: Dictionary of method availability
        """
        available_methods = {}
        
        print(f"{Fore.CYAN}Checking method availability...{Style.RESET_ALL}")
        
        for method in self.methods:
            try:
                params = self.param_generators[method]()
                request = {
                    "jsonrpc": "2.0",
                    "id": self._get_request_id(),
                    "method": method,
                    "params": params
                }
                
                async with self.session.post(self.url, json=request, timeout=5) as response:
                    available = response.status == 200
                    available_methods[method] = available
                    
                    status_color = Fore.GREEN if available else Fore.RED
                    status_text = "Available" if available else "Not Available"
                    print(f"  {Fore.CYAN}{method}:{Style.RESET_ALL} {status_color}{status_text}{Style.RESET_ALL}")
                    
                    if available:
                        self.stats["available_methods"].add(method)
            
            except Exception as e:
                available_methods[method] = False
                print(f"  {Fore.CYAN}{method}:{Style.RESET_ALL} {Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        
        return available_methods
    
    def _create_timestamp(self) -> Dict[str, Any]:
        """Create a timestamp for JSON"""
        now = datetime.now()
        return {
            "seconds": int(now.timestamp()),
            "nanos": int((now.timestamp() - int(now.timestamp())) * 1e9)
        }
    
    def _generate_empty_params(self) -> List[Any]:
        """Generate empty parameters"""
        return []
    
    def _generate_abci_info_params(self) -> List[Any]:
        """Generate parameters for abci_info"""
        return []
    
    def _generate_abci_query_params(self) -> Dict[str, Any]:
        """Generate parameters for abci_query"""
        return {
            "path": random.choice(["/store/acc/key", "/store/staking/key", "/custom/gov/proposals"]),
            "data": base64.b64encode(os.urandom(random.randint(1, 32))).decode('utf-8'),
            "height": str(random.randint(1, 1000)),
            "prove": random.choice([True, False])
        }
    
    def _generate_broadcast_tx_params(self) -> Dict[str, Any]:
        """Generate parameters for broadcast_tx methods"""
        return {
            "tx": base64.b64encode(os.urandom(random.randint(32, 128))).decode('utf-8')
        }
    
    def _generate_block_params(self) -> Dict[str, Any]:
        """Generate parameters for block and block_results"""
        return {
            "height": str(random.randint(1, 1000))
        }
    
    def _generate_blockchain_params(self) -> Dict[str, Any]:
        """Generate parameters for blockchain"""
        min_height = random.randint(1, 500)
        max_height = min_height + random.randint(1, 500)
        return {
            "minHeight": str(min_height),
            "maxHeight": str(max_height)
        }
    
    def _generate_validators_params(self) -> Dict[str, Any]:
        """Generate parameters for validators"""
        return {
            "height": str(random.randint(1, 1000)),
            "page": str(random.randint(1, 5)),
            "per_page": str(random.randint(10, 100))
        }
    
    def _generate_tx_params(self) -> Dict[str, Any]:
        """Generate parameters for tx"""
        return {
            "hash": base64.b64encode(os.urandom(32)).decode('utf-8'),
            "prove": random.choice([True, False])
        }
    
    def _generate_tx_search_params(self) -> Dict[str, Any]:
        """Generate parameters for tx_search"""
        return {
            "query": f"tx.height={random.randint(1, 1000)}",
            "prove": random.choice([True, False]),
            "page": str(random.randint(1, 5)),
            "per_page": str(random.randint(10, 100)),
            "order_by": random.choice(["asc", "desc"])
        }
    
    def _generate_commit_params(self) -> Dict[str, Any]:
        """Generate parameters for commit"""
        return {
            "height": str(random.randint(1, 1000))
        }
    
    def _generate_unconfirmed_txs_params(self) -> Dict[str, Any]:
        """Generate parameters for unconfirmed_txs"""
        return {
            "limit": str(random.randint(10, 100))
        }
    
    async def _send_request(self, method: str) -> Tuple[bool, float]:
        """
        Send a request to the ABCI RPC endpoint
        
        Args:
            method: The method to call
            
        Returns:
            Tuple of (success, response_time)
        """
        # Generate parameters for the method
        params = self.param_generators[method]()
        
        # Create the JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": method,
            "params": params
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
                                print(f"\n{Fore.RED}Error for method {method}: {response_json['error']}{Style.RESET_ALL}")
                            return False, response_time
                        else:
                            if self.verbose:
                                print(f"\n{Fore.GREEN}Request: {json.dumps(request)}{Style.RESET_ALL}")
                                print(f"{Fore.GREEN}Response: {response_text}{Style.RESET_ALL}")
                            return True, response_time
                    except json.JSONDecodeError:
                        # Log failed request
                        self._log_failed_request(method, request, f"Invalid JSON: {response_text}")
                        if self.verbose:
                            print(f"\n{Fore.RED}Invalid JSON response for method {method}: {response_text}{Style.RESET_ALL}")
                        return False, response_time
                else:
                    # Log failed request
                    self._log_failed_request(method, request, f"HTTP {response.status}: {response_text}")
                    if self.verbose:
                        print(f"\n{Fore.RED}Error for method {method}: {response.status} - {response_text}{Style.RESET_ALL}")
                    return False, response_time
        except Exception as e:
            # Log failed request
            self._log_failed_request(method, request, f"Exception: {str(e)}")
            if self.verbose:
                print(f"\n{Fore.RED}Exception for method {method}: {str(e)}{Style.RESET_ALL}")
            return False, response_time
    
    def _log_failed_request(self, method: str, request: Dict, error: Any):
        """
        Log a failed request to the log file
        
        Args:
            method: The method that failed
            request: The request that was sent
            error: The error response or exception
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] {method}\n")
            f.write(f"Request: {json.dumps(request, indent=2)}\n")
            f.write(f"Error: {json.dumps(error, indent=2) if isinstance(error, dict) else str(error)}\n")
            f.write("-" * 80 + "\n\n")
    
    async def run(self, duration: int = 60):
        """
        Run the ABCI RPC flood test
        
        Args:
            duration: Duration of the test in seconds
        """
        print(f"{Fore.CYAN}Starting ABCI RPC flood testing against {self.url}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Testing methods: {', '.join(self.methods)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Requests per second: {self.requests_per_second}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Duration: {duration} seconds{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Failed requests will be logged to: {Fore.YELLOW}{self.log_file}{Style.RESET_ALL}")
        
        # Create session
        await self._create_session()
        
        # Check if service is available
        service_available = await self._check_service_availability()
        if not service_available:
            print(f"\n{Fore.RED}Error: ABCI service is not available at {self.url}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please check that the service is running and the URL is correct.{Style.RESET_ALL}")
            await self._close_session()
            sys.exit(1)
        
        # Check which methods are available
        available_methods = await self._check_method_availability()
        
        # Filter methods to only include available ones
        available_method_list = [m for m in self.methods if m in self.stats["available_methods"]]
        
        if not available_method_list:
            print(f"\n{Fore.RED}Error: No methods are available for testing.{Style.RESET_ALL}")
            await self._close_session()
            sys.exit(1)
        
        print(f"\n{Fore.GREEN}Available methods: {Fore.YELLOW}{', '.join(self.stats['available_methods'])}{Style.RESET_ALL}")
        if len(self.stats["available_methods"]) < len(self.methods):
            unavailable = [m for m in self.methods if m not in self.stats["available_methods"]]
            print(f"{Fore.RED}Unavailable methods: {Fore.YELLOW}{', '.join(unavailable)}{Style.RESET_ALL}")
        
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
                        # Select a random method from available methods
                        method = random.choice(list(self.stats["available_methods"]))
                        methods_for_this_batch.append(method)
                        tasks.append(self._send_request(method))
                        self.stats["requests_by_method"][method] += 1
                    
                    # Execute tasks
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Update statistics
                    for result, method in zip(results, methods_for_this_batch):
                        if isinstance(result, Exception):
                            self.stats["failed_requests"] += 1
                            self.stats["errors_by_method"][method] += 1
                            # Log failed request
                            self._log_failed_request(method, {"method": method, "error": str(result)}, f"Exception: {str(result)}")
                            if self.verbose:
                                print(f"\n{Fore.RED}Exception for method {method}: {str(result)}{Style.RESET_ALL}")
                        else:
                            success, response_time = result
                            if success:
                                self.stats["successful_requests"] += 1
                            else:
                                self.stats["failed_requests"] += 1
                                self.stats["errors_by_method"][method] += 1
                            
                            if response_time < self.stats["min_response_time"]:
                                self.stats["min_response_time"] = response_time
                            if response_time > self.stats["max_response_time"]:
                                self.stats["max_response_time"] = response_time
                            self.stats["total_response_time"] += response_time
                    
                    # Sleep to maintain the requests per second rate
                    elapsed = time.time() - start_loop
                    if elapsed < 1.0:
                        await asyncio.sleep(1.0 - elapsed)
                    
                    # Update progress bar
                    pbar.update(1)
                    
                    # Update total requests count
                    self.stats["total_requests"] += len(tasks)
            
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Test interrupted by user.{Style.RESET_ALL}")
        
        # Record end time
        self.stats["end_time"] = time.time()
        
        # Close session
        await self._close_session()
        
        # Print report
        self._print_report()
    
    def _print_report(self):
        """Print the test report"""
        actual_duration = self.stats["end_time"] - self.stats["start_time"]
        avg_response_time = self.stats["total_response_time"] / max(1, self.stats["total_requests"])
        requests_per_sec = self.stats["total_requests"] / actual_duration
        success_rate = (self.stats["successful_requests"] / max(1, self.stats["total_requests"])) * 100
        
        terminal_width = os.get_terminal_size().columns
        
        print("\n" + "=" * terminal_width)
        print(f"{Fore.YELLOW}{'RPC FLOOD TESTING REPORT':^{terminal_width}}{Style.RESET_ALL}")
        print("=" * terminal_width)
        print(f"{Fore.CYAN}Target URL:{Style.RESET_ALL} {self.url}")
        print(f"{Fore.CYAN}Duration:{Style.RESET_ALL} {actual_duration:.2f} seconds")
        print(f"{Fore.CYAN}Total Requests:{Style.RESET_ALL} {self.stats['total_requests']}")
        
        success_color = Fore.GREEN if success_rate > 90 else Fore.YELLOW if success_rate > 70 else Fore.RED
        print(f"{Fore.CYAN}Successful Requests:{Style.RESET_ALL} {self.stats['successful_requests']} "
              f"({success_color}{success_rate:.2f}%{Style.RESET_ALL})")
        
        print(f"{Fore.CYAN}Failed Requests:{Style.RESET_ALL} {self.stats['failed_requests']}")
        print(f"{Fore.CYAN}Requests per Second:{Style.RESET_ALL} {requests_per_sec:.2f}")
        
        if self.stats["min_response_time"] != float('inf'):
            print(f"{Fore.CYAN}Min Response Time:{Style.RESET_ALL} {self.stats['min_response_time'] * 1000:.2f} ms")
        else:
            print(f"{Fore.CYAN}Min Response Time:{Style.RESET_ALL} N/A")
            
        print(f"{Fore.CYAN}Max Response Time:{Style.RESET_ALL} {self.stats['max_response_time'] * 1000:.2f} ms")
        print(f"{Fore.CYAN}Avg Response Time:{Style.RESET_ALL} {avg_response_time * 1000:.2f} ms")
        
        print("\n" + "-" * terminal_width)
        print(f"{Fore.YELLOW}{'Requests by Method':^{terminal_width}}{Style.RESET_ALL}")
        print("-" * terminal_width)
        
        for method, count in sorted(self.stats["requests_by_method"].items()):
            errors = self.stats["errors_by_method"].get(method, 0)
            if count > 0:
                method_success_rate = ((count - errors) / count) * 100
                success_color = Fore.GREEN if method_success_rate > 90 else Fore.YELLOW if method_success_rate > 70 else Fore.RED
                print(f"{Fore.CYAN}{method}:{Style.RESET_ALL} {count} requests, {errors} errors "
                      f"({success_color}{method_success_rate:.2f}%{Style.RESET_ALL} success)")
        
        print("\n" + "=" * terminal_width)
    
    async def _check_endpoint_health(self):
        """Check if the endpoint is responding at all"""
        try:
            # Try a simple HTTP GET request
            async with self.session.get(self.url) as response:
                if response.status == 200:
                    print(f"{Fore.GREEN}Endpoint is responding to HTTP GET{Style.RESET_ALL}")
                    return True
                else:
                    print(f"{Fore.RED}Endpoint returned status {response.status} for HTTP GET{Style.RESET_ALL}")
                    return False
        except Exception as e:
            print(f"{Fore.RED}Error connecting to endpoint: {str(e)}{Style.RESET_ALL}")
            return False
    
    async def _send_tendermint_request(self, method: str) -> Tuple[bool, float]:
        """Try sending request in Tendermint RPC format"""
        # Strip abci_ prefix if present
        abci_method = method
        if method.startswith("abci_"):
            abci_method = method[5:]
        
        # Create Tendermint RPC request
        request = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "abci_query",
            "params": {
                "path": abci_method,
                "data": base64.b64encode(json.dumps(self.param_generators[abci_method]()).encode()).decode(),
                "height": "0",
                "prove": False
            }
        }
        
        # Log and send request
        # ... 