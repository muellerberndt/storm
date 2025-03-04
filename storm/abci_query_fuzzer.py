"""
ABCI Query Fuzzer module for Storm
"""

import asyncio
import json
import random
import time
import base64
from typing import Dict, List, Any, Optional, Tuple, Set
import aiohttp
import colorama
from colorama import Fore, Style
import os
import sys

class ABCIQueryFuzzer:
    """
    Specialized fuzzer for ABCI query endpoint
    """

    def __init__(self, url: str, verbose: bool = False, actor_address: Optional[str] = None):
        """
        Initialize the ABCI Query Fuzzer
        
        Args:
            url: URL of the ABCI RPC endpoint
            verbose: Whether to print verbose output
            actor_address: Optional known actor address to use in queries
        """
        self.url = url
        self.verbose = verbose
        self.actor_address = actor_address
        self.session = None
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "paths_tried": set(),
            "successful_paths": set(),
            "failed_paths": {},  # path -> count
            "min_response_time": float('inf'),
            "max_response_time": 0,
            "total_response_time": 0,
        }
        
        # Create log directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Define common path patterns for different Cosmos SDK modules
        self.path_templates = [
            # Bank module
            "/store/bank/key",
            "/cosmos.bank.v1beta1.Query/AllBalances",
            "/cosmos.bank.v1beta1.Query/Balance",
            "/cosmos.bank.v1beta1.Query/TotalSupply",
            "/cosmos.bank.v1beta1.Query/SupplyOf",
            "/cosmos.bank.v1beta1.Query/Params",
            "/cosmos.bank.v1beta1.Query/DenomMetadata",
            "/cosmos.bank.v1beta1.Query/DenomsMetadata",
            
            # Staking module
            "/store/staking/key",
            "/cosmos.staking.v1beta1.Query/Validators",
            "/cosmos.staking.v1beta1.Query/Validator",
            "/cosmos.staking.v1beta1.Query/ValidatorDelegations",
            "/cosmos.staking.v1beta1.Query/ValidatorUnbondingDelegations",
            "/cosmos.staking.v1beta1.Query/Delegation",
            "/cosmos.staking.v1beta1.Query/UnbondingDelegation",
            "/cosmos.staking.v1beta1.Query/DelegatorDelegations",
            "/cosmos.staking.v1beta1.Query/DelegatorUnbondingDelegations",
            "/cosmos.staking.v1beta1.Query/Redelegations",
            "/cosmos.staking.v1beta1.Query/DelegatorValidators",
            "/cosmos.staking.v1beta1.Query/DelegatorValidator",
            "/cosmos.staking.v1beta1.Query/HistoricalInfo",
            "/cosmos.staking.v1beta1.Query/Pool",
            "/cosmos.staking.v1beta1.Query/Params",
            
            # Governance module
            "/cosmos.gov.v1beta1.Query/Proposal",
            "/cosmos.gov.v1beta1.Query/Proposals",
            "/cosmos.gov.v1beta1.Query/Vote",
            "/cosmos.gov.v1beta1.Query/Votes",
            "/cosmos.gov.v1beta1.Query/Params",
            "/cosmos.gov.v1beta1.Query/Deposit",
            "/cosmos.gov.v1beta1.Query/Deposits",
            "/cosmos.gov.v1beta1.Query/TallyResult",
            
            # Auth module
            "/cosmos.auth.v1beta1.Query/Account",
            "/cosmos.auth.v1beta1.Query/Accounts",
            "/cosmos.auth.v1beta1.Query/Params",
            
            # Distribution module
            "/cosmos.distribution.v1beta1.Query/Params",
            "/cosmos.distribution.v1beta1.Query/ValidatorOutstandingRewards",
            "/cosmos.distribution.v1beta1.Query/ValidatorCommission",
            "/cosmos.distribution.v1beta1.Query/ValidatorSlashes",
            "/cosmos.distribution.v1beta1.Query/DelegationRewards",
            "/cosmos.distribution.v1beta1.Query/DelegationTotalRewards",
            "/cosmos.distribution.v1beta1.Query/DelegatorValidators",
            "/cosmos.distribution.v1beta1.Query/DelegatorWithdrawAddress",
            "/cosmos.distribution.v1beta1.Query/CommunityPool",
            
            # Slashing module
            "/cosmos.slashing.v1beta1.Query/Params",
            "/cosmos.slashing.v1beta1.Query/SigningInfo",
            "/cosmos.slashing.v1beta1.Query/SigningInfos",
            
            # FVM specific paths (if applicable)
            "/fvm/ipld/{cid}",
            "/fvm/actor_state/{address}",
            "/fvm/actor_code/{address}",
            "/fvm/actor_balance/{address}",
            "/fvm/actor_nonce/{address}",
        ]
        
        # Sample values to use in path parameters
        self.sample_addresses = [
            "cosmos1jxv0u20scum4trha72c7ltfgfqef6nscwf8dg8",
            "cosmos1xyxs3skf3f4jfqeuv89yyaqvjc6lffavxqhc8g",
            "cosmos1e0jnq2sun3dzjh8p2xq95kk0expwmd7shwjpfg",
            "cosmos1ujax3mefa6mn5zeq7xcnetwz9skv9stmuf59sf",
        ]
        
        # If an actor address was provided, add it to the front of the list
        if self.actor_address:
            self.sample_addresses.insert(0, self.actor_address)
            print(f"{Fore.CYAN}Using provided actor address: {self.actor_address}{Style.RESET_ALL}")
        
        self.sample_cids = [
            "bafy2bzacecmda75ovposbdateg7eyhwij3uucabtxgziaf3aeyn6tuqje7psm",
            "bafy2bzaceaxm23epjsmh75yvzcecsrbavlmkcxnva66bkdcfpsp4fzwovuv6q",
            "bafy2bzacedikkmeotawrxrrbnrdqlsknlad4xjyubo52cmlmuxfhrgxvktws6",
        ]
        
        self.sample_coins = [
            "1000uatom",
            "5000stake",
            "10000ustake",
            "1000000uusd",
        ]
        
        self.sample_proposals = ["1", "2", "3", "10", "100"]
        
    async def create_session(self):
        """Create an aiohttp session"""
        self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
    
    def _get_random_height(self) -> str:
        """Get a random height"""
        options = ["0", "1", "10", "100", "latest"]
        return random.choice(options)
    
    def _get_random_prove(self) -> bool:
        """Get a random prove value"""
        return random.choice([True, False])
    
    def _replace_path_params(self, path: str) -> str:
        """Replace path parameters with random values"""
        if "{address}" in path:
            # If we have a provided actor address and this is the first query for this path type,
            # always use the provided address first
            if self.actor_address and path not in self.stats["paths_tried"]:
                path = path.replace("{address}", self.actor_address)
            else:
                path = path.replace("{address}", random.choice(self.sample_addresses))
        if "{cid}" in path:
            path = path.replace("{cid}", random.choice(self.sample_cids))
        return path
    
    def _generate_data_for_path(self, path: str) -> str:
        """Generate appropriate data for a given path"""
        # Default to empty object
        data = {}
        
        # Bank module
        if "AllBalances" in path:
            data = {"address": random.choice(self.sample_addresses)}
        elif "Balance" in path:
            data = {
                "address": random.choice(self.sample_addresses),
                "denom": random.choice(["uatom", "stake", "ustake"])
            }
        elif "SupplyOf" in path:
            data = {"denom": random.choice(["uatom", "stake", "ustake"])}
        
        # Staking module
        elif "Validator" in path and not "Validators" in path:
            data = {"validator_addr": random.choice(self.sample_addresses)}
        elif "Delegation" in path:
            data = {
                "delegator_addr": random.choice(self.sample_addresses),
                "validator_addr": random.choice(self.sample_addresses)
            }
        
        # Governance module
        elif "Proposal" in path and not "Proposals" in path:
            data = {"proposal_id": random.choice(self.sample_proposals)}
        elif "Vote" in path and not "Votes" in path:
            data = {
                "proposal_id": random.choice(self.sample_proposals),
                "voter": random.choice(self.sample_addresses)
            }
        
        # Auth module
        elif "Account" in path and not "Accounts" in path:
            data = {"address": random.choice(self.sample_addresses)}
        
        # FVM specific paths
        elif "/fvm/ipld/" in path:
            # Already handled in path parameter replacement
            pass
        elif "/fvm/actor_" in path:
            # Already handled in path parameter replacement
            pass
        
        # Convert to JSON and base64 encode
        return base64.b64encode(json.dumps(data).encode()).decode()
    
    async def query(self, path: str, data: str = "", height: str = "0", prove: bool = False) -> Tuple[bool, float, Any]:
        """
        Send an ABCI query
        
        Args:
            path: Query path
            data: Base64 encoded data
            height: Block height (0 for latest)
            prove: Whether to include proofs
            
        Returns:
            Tuple of (success, response_time, response)
        """
        # Build query parameters
        params = {
            "path": path,
            "data": data,
            "height": height,
            "prove": str(prove).lower()
        }
        
        url = f"{self.url}"
        
        # Create the JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": str(random.randint(1, 1000000)),
            "method": "abci_query",
            "params": params
        }
        
        if self.verbose:
            print(f"{Fore.CYAN}Querying path: {path}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Data: {data}{Style.RESET_ALL}")
        
        start_time = time.time()
        try:
            async with self.session.post(url, json=request) as response:
                response_text = await response.text()
                response_time = time.time() - start_time
                
                if response.status == 200:
                    try:
                        response_json = json.loads(response_text)
                        
                        # Check if there's an error in the response
                        if "error" in response_json:
                            if self.verbose:
                                print(f"{Fore.RED}Error: {response_json['error']}{Style.RESET_ALL}")
                            return False, response_time, response_json
                        
                        # Check if the result contains an error code
                        result = response_json.get("result", {})
                        response_value = result.get("response", {})
                        
                        if response_value.get("code", 0) != 0:
                            log_msg = f"Code: {response_value.get('code')}, Log: {response_value.get('log')}"
                            if self.verbose:
                                print(f"{Fore.YELLOW}Query failed: {log_msg}{Style.RESET_ALL}")
                            return False, response_time, response_json
                        
                        if self.verbose:
                            print(f"{Fore.GREEN}Query successful!{Style.RESET_ALL}")
                        return True, response_time, response_json
                    except json.JSONDecodeError:
                        if self.verbose:
                            print(f"{Fore.RED}Invalid JSON response: {response_text}{Style.RESET_ALL}")
                        return False, response_time, response_text
                else:
                    if self.verbose:
                        print(f"{Fore.RED}HTTP error: {response.status} - {response_text}{Style.RESET_ALL}")
                    return False, response_time, response_text
                    
        except Exception as e:
            response_time = time.time() - start_time
            if self.verbose:
                print(f"{Fore.RED}Exception: {str(e)}{Style.RESET_ALL}")
            return False, response_time, str(e)
    
    async def _validate_endpoint(self) -> bool:
        """
        Validate that the endpoint is a working Tendermint/ABCI endpoint
        
        Returns:
            bool: True if the endpoint is valid, False otherwise
        """
        print(f"{Fore.CYAN}Validating endpoint: {self.url}{Style.RESET_ALL}")
        
        # First try a simple status request to check if the endpoint is responsive
        request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "status",
            "params": []
        }
        
        try:
            async with self.session.post(self.url, json=request) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        response_json = json.loads(response_text)
                        if "result" in response_json:
                            # It responded to a status request, likely a Tendermint node
                            print(f"{Fore.GREEN}✓ Endpoint is responsive and appears to be a Tendermint node.{Style.RESET_ALL}")
                            node_info = response_json.get("result", {}).get("node_info", {})
                            if node_info:
                                print(f"{Fore.GREEN}  Node version: {node_info.get('version', 'unknown')}{Style.RESET_ALL}")
                                print(f"{Fore.GREEN}  Network: {node_info.get('network', 'unknown')}{Style.RESET_ALL}")
                            return True
                        elif "error" in response_json:
                            # It responded with an error, but in JSON-RPC format
                            print(f"{Fore.YELLOW}⚠ Endpoint responded with an error: {response_json['error'].get('message', 'Unknown error')}{Style.RESET_ALL}")
                            print(f"{Fore.YELLOW}  This might still be a valid endpoint but 'status' method may not be supported.{Style.RESET_ALL}")
                            return True
                    except json.JSONDecodeError:
                        # Not a JSON response, check if it's HTML
                        if "<html" in response_text.lower():
                            print(f"{Fore.RED}✗ Endpoint returned HTML instead of JSON. This is likely not a Tendermint RPC endpoint.{Style.RESET_ALL}")
                            return False
                        print(f"{Fore.RED}✗ Endpoint returned non-JSON response: {response_text[:100]}{Style.RESET_ALL}")
                        return False
                else:
                    print(f"{Fore.RED}✗ Endpoint returned HTTP {response.status}: {response_text[:100]}{Style.RESET_ALL}")
                    return False
        except Exception as e:
            print(f"{Fore.RED}✗ Error connecting to endpoint: {str(e)}{Style.RESET_ALL}")
            return False
        
        # If we get here, the status check failed, try an abci_info request
        request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "abci_info",
            "params": []
        }
        
        try:
            async with self.session.post(self.url, json=request) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        response_json = json.loads(response_text)
                        if "result" in response_json:
                            print(f"{Fore.GREEN}✓ Endpoint responded to abci_info, it appears to be a Tendermint node.{Style.RESET_ALL}")
                            return True
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass
            
        # If both checks failed, this is probably not a Tendermint endpoint
        print(f"{Fore.RED}✗ Endpoint failed validation. This doesn't appear to be a Tendermint/ABCI RPC endpoint.{Style.RESET_ALL}")
        return False
    
    async def _test_direct_query(self) -> bool:
        """
        Test if abci_query works at all
        
        Returns:
            bool: True if abci_query works, False otherwise
        """
        print(f"{Fore.CYAN}Testing if abci_query endpoint works...{Style.RESET_ALL}")
        
        # Try a simple query with minimal parameters
        params = {
            "path": "/app/version",  # Often available in Cosmos apps
            "data": "",
            "height": "0",
            "prove": "false"
        }
        
        request = {
            "jsonrpc": "2.0",
            "id": "test",
            "method": "abci_query",
            "params": params
        }
        
        try:
            async with self.session.post(self.url, json=request) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        response_json = json.loads(response_text)
                        
                        # Check if there's an error in the response
                        if "error" in response_json:
                            error_msg = response_json.get("error", {}).get("message", "Unknown error")
                            print(f"{Fore.YELLOW}⚠ abci_query returned error: {error_msg}{Style.RESET_ALL}")
                            if "not found" in error_msg.lower() or "method not found" in error_msg.lower():
                                print(f"{Fore.RED}✗ The abci_query method is not supported by this endpoint.{Style.RESET_ALL}")
                                return False
                            print(f"{Fore.YELLOW}  This might be because the path is invalid, but the method exists.{Style.RESET_ALL}")
                            return True
                        
                        # We got a successful response
                        print(f"{Fore.GREEN}✓ abci_query endpoint is working!{Style.RESET_ALL}")
                        return True
                    except json.JSONDecodeError:
                        print(f"{Fore.RED}✗ abci_query returned non-JSON response: {response_text[:100]}{Style.RESET_ALL}")
                        return False
                else:
                    print(f"{Fore.RED}✗ abci_query returned HTTP {response.status}: {response_text[:100]}{Style.RESET_ALL}")
                    return False
        except Exception as e:
            print(f"{Fore.RED}✗ Error testing abci_query: {str(e)}{Style.RESET_ALL}")
            return False

    async def discover_working_paths(self, max_attempts: int = 1000):
        """
        Try to discover working ABCI query paths
        
        Args:
            max_attempts: Maximum number of query attempts
        """
        print(f"{Fore.CYAN}Starting ABCI query path discovery...{Style.RESET_ALL}")
        
        # Create session
        await self.create_session()
        
        # Validate that the endpoint is a Tendermint node
        if not await self._validate_endpoint():
            print(f"{Fore.RED}Endpoint validation failed. Aborting path discovery.{Style.RESET_ALL}")
            await self.close_session()
            return
        
        # Test if abci_query works at all
        if not await self._test_direct_query():
            print(f"{Fore.RED}The abci_query method is not supported by this endpoint. Aborting path discovery.{Style.RESET_ALL}")
            await self.close_session()
            return
        
        print(f"{Fore.CYAN}Trying up to {max_attempts} combinations of paths and parameters{Style.RESET_ALL}")
        
        # Add simple paths that are likely to work
        simple_paths = [
            "/", 
            "/app/info",
            "/app/version",
            "/info",
            "/version",
            "/store",
            "/key",
            "/custom",
            "/p2p/filter/addr",
            "/p2p/filter/id",
            "/validators"
        ]
        
        # Add them to the beginning of the path_templates
        self.path_templates = simple_paths + self.path_templates
        
        for i in range(max_attempts):
            # Select a random path
            path_template = random.choice(self.path_templates)
            path = self._replace_path_params(path_template)
            
            # Generate appropriate data
            data = self._generate_data_for_path(path)
            
            # Random height and prove
            height = self._get_random_height()
            prove = self._get_random_prove()
            
            # Send query
            success, response_time, response = await self.query(path, data, height, prove)
            
            # Update statistics
            self.stats["total_queries"] += 1
            self.stats["paths_tried"].add(path_template)
            
            if success:
                self.stats["successful_queries"] += 1
                self.stats["successful_paths"].add(path_template)
                print(f"{Fore.GREEN}✓ Working path found: {path_template}{Style.RESET_ALL}")
            else:
                self.stats["failed_queries"] += 1
                self.stats["failed_paths"][path_template] = self.stats["failed_paths"].get(path_template, 0) + 1
            
            # Update response time stats
            if response_time < self.stats["min_response_time"]:
                self.stats["min_response_time"] = response_time
            if response_time > self.stats["max_response_time"]:
                self.stats["max_response_time"] = response_time
            self.stats["total_response_time"] += response_time
            
            # Progress update
            if (i + 1) % 10 == 0:
                success_rate = self.stats["successful_queries"] / self.stats["total_queries"] * 100
                print(f"{Fore.CYAN}Progress: {i+1}/{max_attempts} queries, {len(self.stats['successful_paths'])} working paths found ({success_rate:.1f}% success rate){Style.RESET_ALL}")
        
        await self.close_session()
        self._print_report()
    
    def _print_report(self):
        """Print a report of the discovery run"""
        terminal_width = os.get_terminal_size().columns
        
        print(f"\n{Fore.CYAN}{'=' * terminal_width}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'ABCI QUERY PATH DISCOVERY REPORT':^{terminal_width}}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * terminal_width}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}Target URL:{Style.RESET_ALL} {self.url}")
        print(f"{Fore.CYAN}Total queries:{Style.RESET_ALL} {self.stats['total_queries']}")
        print(f"{Fore.CYAN}Successful queries:{Style.RESET_ALL} {self.stats['successful_queries']} " 
              f"({Fore.GREEN}{self.stats['successful_queries']/max(1, self.stats['total_queries'])*100:.1f}%{Style.RESET_ALL})")
        print(f"{Fore.CYAN}Failed queries:{Style.RESET_ALL} {self.stats['failed_queries']} "
              f"({Fore.RED}{self.stats['failed_queries']/max(1, self.stats['total_queries'])*100:.1f}%{Style.RESET_ALL})")
        
        if self.stats["successful_paths"]:
            print(f"\n{Fore.GREEN}Working paths:{Style.RESET_ALL}")
            for path in sorted(self.stats["successful_paths"]):
                print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {path}")
        
        print(f"\n{Fore.CYAN}Paths tried: {len(self.stats['paths_tried'])}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Average response time: {self.stats['total_response_time']/max(1, self.stats['total_queries'])*1000:.2f} ms{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{'=' * terminal_width}{Style.RESET_ALL}")

# Example usage
async def main():
    fuzzer = ABCIQueryFuzzer("http://localhost:26657", verbose=False)
    await fuzzer.discover_working_paths(max_attempts=100)

if __name__ == "__main__":
    # Initialize colorama
    colorama.init()
    
    # Run the fuzzer
    asyncio.run(main()) 