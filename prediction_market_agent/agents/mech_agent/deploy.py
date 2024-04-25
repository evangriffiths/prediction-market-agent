import random
import typing as t

from prediction_market_agent_tooling.benchmark.utils import OutcomePrediction
from prediction_market_agent_tooling.deploy.agent import DeployableAgent
from prediction_market_agent_tooling.markets.agent_market import AgentMarket

from prediction_market_agent.tools.mech.utils import (
    MechTool,
    mech_request,
    mech_request_local,
)


class DeployableMechAgentBase(DeployableAgent):
    def load(self) -> None:
        self.tool: MechTool | None = None
        self.local: bool | None = None

    @property
    def prediction_fn(self) -> t.Callable[[str, MechTool], OutcomePrediction]:
        if self.local is None:
            raise ValueError("Local mode not set")

        return mech_request_local if self.local else mech_request

    def pick_markets(self, markets: t.Sequence[AgentMarket]) -> t.Sequence[AgentMarket]:
        # We simply pick 5 random markets to bet on
        markets = list(markets)
        random.shuffle(markets)
        return markets[:5]

    def answer_binary_market(self, market: AgentMarket) -> OutcomePrediction:
        if self.tool is None:
            raise ValueError("Tool not set")

        result: OutcomePrediction = self.prediction_fn(market.question, self.tool)
        return result


class DeployablePredictionOnlineAgent(DeployableMechAgentBase):
    def load(self) -> None:
        self.local = True
        self.tool = MechTool.PREDICTION_ONLINE


class DeployablePredictionOfflineAgent(DeployableMechAgentBase):
    def load(self) -> None:
        self.local = True
        self.tool = MechTool.PREDICTION_OFFLINE


class DeployablePredictionOnlineSMEAgent(DeployableMechAgentBase):
    def load(self) -> None:
        self.local = True
        self.tool = MechTool.PREDICTION_ONLINE_SME


class DeployablePredictionOfflineSMEAgent(DeployableMechAgentBase):
    def load(self) -> None:
        self.local = True
        self.tool = MechTool.PREDICTION_OFFLINE_SME


class DeployablePredictionRequestRAGAgent(DeployableMechAgentBase):
    def load(self) -> None:
        self.local = True
        self.tool = MechTool.PREDICTION_REQUEST_RAG


class DeployablePredictionRequestReasoningAgent(DeployableMechAgentBase):
    def load(self) -> None:
        self.local = True
        self.tool = MechTool.PREDICTION_REQUEST_REASONING
