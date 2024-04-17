from datetime import timedelta

from loguru import logger
from prediction_market_agent_tooling.config import APIKeys
from prediction_market_agent_tooling.deploy.agent import DeployableAgent
from prediction_market_agent_tooling.gtypes import xdai_type
from prediction_market_agent_tooling.markets.markets import MarketType
from prediction_market_agent_tooling.markets.omen.omen import (
    redeem_from_all_user_positions,
)
from prediction_market_agent_tooling.markets.omen.omen_replicate import (
    omen_replicate_from_tx,
    omen_unfund_replicated_known_markets_tx,
)
from prediction_market_agent_tooling.markets.omen.omen_resolve_replicated import (
    omen_finalize_and_resolve_and_claim_back_all_markets_based_on_others_tx,
)
from prediction_market_agent_tooling.tools.utils import utcnow
from pydantic_settings import BaseSettings, SettingsConfigDict


class ReplicateSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    N_TO_REPLICATE: int
    INITIAL_FUNDS: str
    CLOSE_TIME_UP_TO_N_DAYS: int


class DeployableReplicateToOmenAgent(DeployableAgent):
    def run(
        self, market_type: MarketType = MarketType.MANIFOLD, _place_bet: bool = True
    ) -> None:
        if market_type != MarketType.OMEN:
            raise RuntimeError("Can replicate only into Omen.")

        keys = APIKeys()
        settings = ReplicateSettings()

        logger.info(
            f"Finalising, resolving and claiming back xDai from existing markets replicated by {keys.bet_from_address}."
        )
        omen_finalize_and_resolve_and_claim_back_all_markets_based_on_others_tx(
            from_private_key=keys.bet_from_private_key
        )

        logger.info(
            f"Unfunding soon to be known markets replicated by {keys.bet_from_address}."
        )
        omen_unfund_replicated_known_markets_tx(
            keys.bet_from_private_key, saturation_above_threshold=0.9
        )

        logger.info("Redeeming funds from previously unfunded markets.")
        redeem_from_all_user_positions(keys.bet_from_private_key)

        close_time_before = utcnow() + timedelta(days=settings.CLOSE_TIME_UP_TO_N_DAYS)
        initial_funds_per_market = xdai_type(settings.INITIAL_FUNDS)

        logger.info(f"Replicating from {MarketType.MANIFOLD}.")
        omen_replicate_from_tx(
            market_type=MarketType.MANIFOLD,
            n_to_replicate=settings.N_TO_REPLICATE,
            initial_funds=initial_funds_per_market,
            from_private_key=keys.bet_from_private_key,
            close_time_before=close_time_before,
            auto_deposit=True,
        )
        logger.info(f"Replicating from {MarketType.POLYMARKET}.")
        omen_replicate_from_tx(
            market_type=MarketType.POLYMARKET,
            n_to_replicate=settings.N_TO_REPLICATE,
            initial_funds=initial_funds_per_market,
            from_private_key=keys.bet_from_private_key,
            close_time_before=close_time_before,
            auto_deposit=True,
        )
        logger.debug("Done.")