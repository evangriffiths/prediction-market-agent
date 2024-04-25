import random
import typing as t

from loguru import logger
from prediction_market_agent_tooling.deploy.agent import Answer, DeployableAgent
from prediction_market_agent_tooling.markets.agent_market import AgentMarket
from prediction_market_agent_tooling.markets.markets import MarketType

from prediction_market_agent.agents.think_thoroughly_agent.think_thoroughly_agent import (
    CrewAIAgentSubquestions,
)
from prediction_market_agent.agents.utils import market_is_saturated


class DeployableThinkThoroughlyAgent(DeployableAgent):
    model: str = "gpt-4-turbo-2024-04-09"

    def load(self) -> None:
        self.agent = CrewAIAgentSubquestions(model=self.model)

    def pick_markets(self, markets: t.Sequence[AgentMarket]) -> t.Sequence[AgentMarket]:
        # We simply pick 5 random markets to bet on
        picked_markets: list[AgentMarket] = []
        markets = list(markets)
        random.shuffle(markets)
        for market in markets:
            # Assume very high probability markets are already known, and have
            # been correctly bet on, and therefore the value of betting on them
            # is low.
            if not market_is_saturated(market=market):
                picked_markets.append(market)
                if len(picked_markets) == 5:
                    break
            else:
                logger.info(
                    f"Market {market.url} is too saturated to bet on with p_yes {market.current_p_yes}."
                )

        return picked_markets

    def answer_binary_market(self, market: AgentMarket) -> Answer | None:
        return self.agent.answer_binary_market(market.question)


if __name__ == "__main__":
    agent = DeployableThinkThoroughlyAgent()
    agent.deploy_local(
        market_type=MarketType.OMEN, sleep_time=540, timeout=180, place_bet=False
    )
