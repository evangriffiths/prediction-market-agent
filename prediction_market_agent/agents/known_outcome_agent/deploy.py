import getpass

from prediction_market_agent_tooling.config import APIKeys
from prediction_market_agent_tooling.deploy.agent import DeployableAgent
from prediction_market_agent_tooling.deploy.constants import OWNER_KEY
from prediction_market_agent_tooling.markets.agent_market import AgentMarket
from prediction_market_agent_tooling.markets.data_models import BetAmount, Currency
from prediction_market_agent_tooling.markets.markets import MarketType
from prediction_market_agent_tooling.tools.utils import get_current_git_commit_sha

from prediction_market_agent.agents.known_outcome_agent.known_outcome_agent import (
    Result,
    get_known_outcome,
)


def market_is_saturated(market: AgentMarket) -> bool:
    return market.p_yes > 0.95 or market.p_no > 0.95


class DeployableKnownOutcomeAgent(DeployableAgent):
    model = "gpt-3.5-turbo-0125"

    def load(self) -> None:
        self.markets_with_known_outcomes: dict[str, Result] = {}

    def pick_markets(self, markets: list[AgentMarket]) -> list[AgentMarket]:
        picked_markets: list[AgentMarket] = []
        for market in markets:
            # Assume very high probability markets are already known, and have
            # been correctly bet on, and therefore the value of betting on them
            # is low.
            if not market_is_saturated(market=markets[0]):
                answer = get_known_outcome(
                    model=self.model,
                    question=market.question,
                    max_tries=3,
                )
                if answer.has_known_outcome():
                    picked_markets.append(market)
                    self.markets_with_known_outcomes[market.id] = answer.result

        return picked_markets

    def answer_binary_market(self, market: AgentMarket) -> bool:
        # The answer has already been determined in `pick_markets` so we just
        # return it here.
        return self.markets_with_known_outcomes[market.id].to_boolean()

    def calculate_bet_amount(self, answer: bool, market: AgentMarket) -> BetAmount:
        if market.currency == Currency.xDai:
            return BetAmount(amount=0.1, currency=Currency.xDai)
        else:
            raise NotImplementedError("This agent only supports xDai markets")


if __name__ == "__main__":
    agent = DeployableKnownOutcomeAgent()
    github_repo_url = "https://github.com/gnosis/prediction-market-agent"
    agent.deploy_gcp(
        repository=f"git+{github_repo_url}.git@{get_current_git_commit_sha()}",
        market_type=MarketType.OMEN,
        labels={OWNER_KEY: getpass.getuser()},
        secrets={
            "OPENAI_API_KEY": "EVAN_OPENAI_API_KEY:latest",
            "TAVILY_API_KEY": "GNOSIS_AI_TAVILY_API_KEY:latest",
            "BET_FROM_PRIVATE_KEY": "0x3666DA333dAdD05083FEf9FF6dDEe588d26E4307:latest",
        },
        memory=1024,
        api_keys=APIKeys(
            BET_FROM_ADDRESS="0x3666DA333dAdD05083FEf9FF6dDEe588d26E4307",
            BET_FROM_PRIVATE_KEY=None,
            OPENAI_API_KEY=None,
            MANIFOLD_API_KEY=None,
        ),
        cron_schedule="0 */4 * * *",
        timeout=540,
    )
