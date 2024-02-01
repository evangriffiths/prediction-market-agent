from web3 import Web3

from prediction_market_agent.omen import get_market, omen_claim_winnings_tx
from prediction_market_agent.tools.gnosis_rpc import GNOSIS_RPC_URL
from prediction_market_agent.tools.web3_utils import xdai_to_wei
from prediction_market_agent.utils import get_bet_from_address, get_bet_from_private_key

web3 = Web3(Web3.HTTPProvider(GNOSIS_RPC_URL))

market_address = "0x1a875b15564939d640ad1ef13769eab5ec74ef03"

market = get_market(market_address)
omen_claim_winnings_tx(
    web3=web3,
    market=market,
    from_address=Web3.to_checksum_address(get_bet_from_address()),
    from_private_key=get_bet_from_private_key(),
    auto_withdraw=True,
    expected_amount=xdai_to_wei(0.4),
)
