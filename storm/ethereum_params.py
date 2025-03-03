"""
Parameter generators for Ethereum JSON-RPC API fuzzing
"""

import random
from typing import List, Any, Callable, Dict


class ParameterGenerator:
    """
    Generates parameters for Ethereum JSON-RPC API methods
    """
    
    def __init__(self):
        # Sample addresses, block hashes, and transaction hashes for fuzzing
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
            "safe",
            "finalized",
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
    
    def get_available_methods(self) -> Dict[str, Callable[[], List[Any]]]:
        """
        Returns a dictionary of available methods and their parameter generators
        """
        return {
            # Web3 Namespace
            "web3_clientVersion": self._generate_no_params,
            "web3_sha3": self._generate_web3_sha3_params,
            
            # Net Namespace
            "net_version": self._generate_no_params,
            "net_peerCount": self._generate_no_params,
            "net_listening": self._generate_no_params,
            
            # Eth Namespace
            "eth_protocolVersion": self._generate_no_params,
            "eth_syncing": self._generate_no_params,
            "eth_coinbase": self._generate_no_params,
            "eth_mining": self._generate_no_params,
            "eth_hashrate": self._generate_no_params,
            "eth_gasPrice": self._generate_no_params,
            "eth_accounts": self._generate_no_params,
            "eth_blockNumber": self._generate_no_params,
            "eth_getBalance": self._generate_eth_getBalance_params,
            "eth_getStorageAt": self._generate_eth_getStorageAt_params,
            "eth_getTransactionCount": self._generate_eth_getTransactionCount_params,
            "eth_getBlockTransactionCountByHash": self._generate_eth_getBlockTransactionCountByHash_params,
            "eth_getBlockTransactionCountByNumber": self._generate_eth_getBlockTransactionCountByNumber_params,
            "eth_getUncleCountByBlockHash": self._generate_eth_getUncleCountByBlockHash_params,
            "eth_getUncleCountByBlockNumber": self._generate_eth_getUncleCountByBlockNumber_params,
            "eth_getCode": self._generate_eth_getCode_params,
            "eth_call": self._generate_eth_call_params,
            "eth_estimateGas": self._generate_eth_estimateGas_params,
            "eth_getBlockByHash": self._generate_eth_getBlockByHash_params,
            "eth_getBlockByNumber": self._generate_eth_getBlockByNumber_params,
            "eth_getTransactionByHash": self._generate_eth_getTransactionByHash_params,
            "eth_getTransactionByBlockHashAndIndex": self._generate_eth_getTransactionByBlockHashAndIndex_params,
            "eth_getTransactionByBlockNumberAndIndex": self._generate_eth_getTransactionByBlockNumberAndIndex_params,
            "eth_getTransactionReceipt": self._generate_eth_getTransactionReceipt_params,
            "eth_getUncleByBlockHashAndIndex": self._generate_eth_getUncleByBlockHashAndIndex_params,
            "eth_getUncleByBlockNumberAndIndex": self._generate_eth_getUncleByBlockNumberAndIndex_params,
            "eth_newFilter": self._generate_eth_newFilter_params,
            "eth_newBlockFilter": self._generate_no_params,
            "eth_newPendingTransactionFilter": self._generate_no_params,
            "eth_uninstallFilter": self._generate_eth_uninstallFilter_params,
            "eth_getFilterChanges": self._generate_eth_getFilterChanges_params,
            "eth_getFilterLogs": self._generate_eth_getFilterLogs_params,
        }
    
    # Parameter generators for each method
    def _generate_no_params(self) -> List[Any]:
        """Generate empty parameters for methods that don't require any"""
        return []
    
    def _generate_web3_sha3_params(self) -> List[Any]:
        """Generate parameters for web3_sha3"""
        # Generate random hex data
        data_length = random.randint(2, 100)  # Length in bytes
        random_data = "0x" + "".join(random.choice("0123456789abcdef") for _ in range(data_length * 2))
        return [random_data]
    
    def _generate_eth_getBalance_params(self) -> List[Any]:
        """Generate parameters for eth_getBalance"""
        address = random.choice(self.sample_addresses)
        block = random.choice(self.sample_block_numbers)
        return [address, block]
    
    def _generate_eth_getStorageAt_params(self) -> List[Any]:
        """Generate parameters for eth_getStorageAt"""
        address = random.choice(self.sample_addresses)
        position = "0x" + "".join(random.choice("0123456789abcdef") for _ in range(64))
        block = random.choice(self.sample_block_numbers)
        return [address, position, block]
    
    def _generate_eth_getTransactionCount_params(self) -> List[Any]:
        """Generate parameters for eth_getTransactionCount"""
        address = random.choice(self.sample_addresses)
        block = random.choice(self.sample_block_numbers)
        return [address, block]
    
    def _generate_eth_getBlockTransactionCountByHash_params(self) -> List[Any]:
        """Generate parameters for eth_getBlockTransactionCountByHash"""
        block_hash = random.choice(self.sample_block_hashes)
        return [block_hash]
    
    def _generate_eth_getBlockTransactionCountByNumber_params(self) -> List[Any]:
        """Generate parameters for eth_getBlockTransactionCountByNumber"""
        block = random.choice(self.sample_block_numbers)
        return [block]
    
    def _generate_eth_getUncleCountByBlockHash_params(self) -> List[Any]:
        """Generate parameters for eth_getUncleCountByBlockHash"""
        block_hash = random.choice(self.sample_block_hashes)
        return [block_hash]
    
    def _generate_eth_getUncleCountByBlockNumber_params(self) -> List[Any]:
        """Generate parameters for eth_getUncleCountByBlockNumber"""
        block = random.choice(self.sample_block_numbers)
        return [block]
    
    def _generate_eth_getCode_params(self) -> List[Any]:
        """Generate parameters for eth_getCode"""
        address = random.choice(self.sample_addresses)
        block = random.choice(self.sample_block_numbers)
        return [address, block]
    
    def _generate_eth_call_params(self) -> List[Any]:
        """Generate parameters for eth_call"""
        # Generate a random transaction object
        to_address = random.choice(self.sample_addresses)
        from_address = random.choice(self.sample_addresses)
        
        # Sometimes include data, sometimes not
        if random.random() < 0.5:
            data_length = random.randint(2, 100)  # Length in bytes
            data = "0x" + "".join(random.choice("0123456789abcdef") for _ in range(data_length * 2))
            tx_object = {"to": to_address, "from": from_address, "data": data}
        else:
            tx_object = {"to": to_address, "from": from_address}
        
        # Sometimes include gas, gasPrice, value
        if random.random() < 0.3:
            tx_object["gas"] = "0x" + hex(random.randint(21000, 1000000))[2:]
        if random.random() < 0.3:
            tx_object["gasPrice"] = "0x" + hex(random.randint(1, 100) * 10**9)[2:]
        if random.random() < 0.3:
            tx_object["value"] = "0x" + hex(random.randint(0, 10) * 10**18)[2:]
        
        block = random.choice(self.sample_block_numbers)
        return [tx_object, block]
    
    def _generate_eth_estimateGas_params(self) -> List[Any]:
        """Generate parameters for eth_estimateGas"""
        # Similar to eth_call but without the block parameter
        to_address = random.choice(self.sample_addresses)
        from_address = random.choice(self.sample_addresses)
        
        if random.random() < 0.5:
            data_length = random.randint(2, 100)
            data = "0x" + "".join(random.choice("0123456789abcdef") for _ in range(data_length * 2))
            tx_object = {"to": to_address, "from": from_address, "data": data}
        else:
            tx_object = {"to": to_address, "from": from_address}
        
        if random.random() < 0.3:
            tx_object["gas"] = "0x" + hex(random.randint(21000, 1000000))[2:]
        if random.random() < 0.3:
            tx_object["gasPrice"] = "0x" + hex(random.randint(1, 100) * 10**9)[2:]
        if random.random() < 0.3:
            tx_object["value"] = "0x" + hex(random.randint(0, 10) * 10**18)[2:]
        
        return [tx_object]
    
    def _generate_eth_getBlockByHash_params(self) -> List[Any]:
        """Generate parameters for eth_getBlockByHash"""
        block_hash = random.choice(self.sample_block_hashes)
        full_tx = random.choice([True, False])
        return [block_hash, full_tx]
    
    def _generate_eth_getBlockByNumber_params(self) -> List[Any]:
        """Generate parameters for eth_getBlockByNumber"""
        block = random.choice(self.sample_block_numbers)
        full_tx = random.choice([True, False])
        return [block, full_tx]
    
    def _generate_eth_getTransactionByHash_params(self) -> List[Any]:
        """Generate parameters for eth_getTransactionByHash"""
        tx_hash = random.choice(self.sample_tx_hashes)
        return [tx_hash]
    
    def _generate_eth_getTransactionByBlockHashAndIndex_params(self) -> List[Any]:
        """Generate parameters for eth_getTransactionByBlockHashAndIndex"""
        block_hash = random.choice(self.sample_block_hashes)
        tx_index = "0x" + hex(random.randint(0, 500))[2:]
        return [block_hash, tx_index]
    
    def _generate_eth_getTransactionByBlockNumberAndIndex_params(self) -> List[Any]:
        """Generate parameters for eth_getTransactionByBlockNumberAndIndex"""
        block = random.choice(self.sample_block_numbers)
        tx_index = "0x" + hex(random.randint(0, 500))[2:]
        return [block, tx_index]
    
    def _generate_eth_getTransactionReceipt_params(self) -> List[Any]:
        """Generate parameters for eth_getTransactionReceipt"""
        tx_hash = random.choice(self.sample_tx_hashes)
        return [tx_hash]
    
    def _generate_eth_getUncleByBlockHashAndIndex_params(self) -> List[Any]:
        """Generate parameters for eth_getUncleByBlockHashAndIndex"""
        block_hash = random.choice(self.sample_block_hashes)
        uncle_index = "0x" + hex(random.randint(0, 10))[2:]
        return [block_hash, uncle_index]
    
    def _generate_eth_getUncleByBlockNumberAndIndex_params(self) -> List[Any]:
        """Generate parameters for eth_getUncleByBlockNumberAndIndex"""
        block = random.choice(self.sample_block_numbers)
        uncle_index = "0x" + hex(random.randint(0, 10))[2:]
        return [block, uncle_index]
    
    def _generate_eth_newFilter_params(self) -> List[Any]:
        """Generate parameters for eth_newFilter"""
        filter_obj = {}
        
        # Randomly include fromBlock, toBlock, address, topics
        if random.random() < 0.7:
            filter_obj["fromBlock"] = random.choice(self.sample_block_numbers)
        if random.random() < 0.7:
            filter_obj["toBlock"] = random.choice(self.sample_block_numbers)
        
        # Address can be a single address or an array of addresses
        if random.random() < 0.7:
            if random.random() < 0.5:
                filter_obj["address"] = random.choice(self.sample_addresses)
            else:
                num_addresses = random.randint(1, 3)
                filter_obj["address"] = random.sample(self.sample_addresses, num_addresses)
        
        # Topics can be complex, but we'll keep it simple for fuzzing
        if random.random() < 0.5:
            num_topics = random.randint(1, 4)
            topics = []
            for _ in range(num_topics):
                topic = "0x" + "".join(random.choice("0123456789abcdef") for _ in range(64))
                topics.append(topic)
            filter_obj["topics"] = topics
        
        return [filter_obj]
    
    def _generate_eth_uninstallFilter_params(self) -> List[Any]:
        """Generate parameters for eth_uninstallFilter"""
        filter_id = random.choice(self.sample_filter_ids)
        return [filter_id]
    
    def _generate_eth_getFilterChanges_params(self) -> List[Any]:
        """Generate parameters for eth_getFilterChanges"""
        filter_id = random.choice(self.sample_filter_ids)
        return [filter_id]
    
    def _generate_eth_getFilterLogs_params(self) -> List[Any]:
        """Generate parameters for eth_getFilterLogs"""
        filter_id = random.choice(self.sample_filter_ids)
        return [filter_id] 