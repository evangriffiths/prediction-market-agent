import requests
from web3.types import Wei

from prediction_market_agent.tools.web3_utils import wei_to_xdai

GNOSIS_RPC_URL = "https://rpc.gnosischain.com/"


def get_balance(address: str) -> Wei:
    response = requests.post(
        GNOSIS_RPC_URL,
        json={
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"],
            "id": 1,
        },
        headers={"content-type": "application/json"},
    ).json()
    balance = Wei(int(response["result"], 16))  # Convert hex value to int.
    return balance


if __name__ == "__main__":
    balance = get_balance("0xf3318C420e5e30C12786C4001D600e9EE1A7eBb1")
    print(f"Wei: {balance}, xDai: {wei_to_xdai(balance)}")
