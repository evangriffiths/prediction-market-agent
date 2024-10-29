"""
Entrypoint for running the agent in GKE.
If the agent adheres to PMAT standard (subclasses deployable agent), 
simply add the agent to the `RunnableAgent` enum and then `RUNNABLE_AGENTS` dict.

Can also be executed locally, simply by running `python prediction_market_agent/run_agent.py <agent> <market_type>`.
"""

from enum import Enum

import typer
from prediction_market_agent_tooling.deploy.agent import DeployableAgent
from prediction_market_agent_tooling.markets.markets import MarketType

from prediction_market_agent.agents.coinflip_agent.deploy import DeployableCoinFlipAgent
from prediction_market_agent.agents.invalid_agent.deploy import InvalidAgent
from prediction_market_agent.agents.known_outcome_agent.deploy import (
    DeployableKnownOutcomeAgent,
)
from prediction_market_agent.agents.metaculus_agent.deploy import (
    DeployableMetaculusBotTournamentAgent,
)
from prediction_market_agent.agents.microchain_agent.deploy import (
    DeployableMicrochainAgent,
    DeployableMicrochainModifiableSystemPromptAgent0,
    DeployableMicrochainModifiableSystemPromptAgent1,
    DeployableMicrochainModifiableSystemPromptAgent2,
    DeployableMicrochainModifiableSystemPromptAgent3,
    DeployableMicrochainWithGoalManagerAgent0,
)
from prediction_market_agent.agents.ofvchallenger_agent.deploy import OFVChallengerAgent
from prediction_market_agent.agents.omen_cleaner_agent.deploy import OmenCleanerAgent
from prediction_market_agent.agents.prophet_agent.deploy import (
    DeployableOlasEmbeddingOAAgent,
    DeployablePredictionProphetGPT4oAgent,
    DeployablePredictionProphetGPT4TurboFinalAgent,
    DeployablePredictionProphetGPT4TurboPreviewAgent,
    DeployablePredictionProphetGPTo1MiniAgent,
    DeployablePredictionProphetGPTo1PreviewAgent,
)
from prediction_market_agent.agents.replicate_to_omen_agent.deploy import (
    DeployableReplicateToOmenAgent,
)
from prediction_market_agent.agents.social_media_agent.deploy import (
    DeployableSocialMediaAgent,
)
from prediction_market_agent.agents.specialized_agent.deploy import (
    MarketCreatorsStalkerAgent1,
    MarketCreatorsStalkerAgent2,
)
from prediction_market_agent.agents.think_thoroughly_agent.deploy import (
    DeployableThinkThoroughlyAgent,
    DeployableThinkThoroughlyProphetResearchAgent,
)


class RunnableAgent(str, Enum):
    coinflip = "coinflip"
    replicate_to_omen = "replicate_to_omen"
    think_thoroughly = "think_thoroughly"
    think_thoroughly_prophet = "think_thoroughly_prophet"
    knownoutcome = "knownoutcome"
    microchain = "microchain"
    microchain_modifiable_system_prompt_0 = "microchain_modifiable_system_prompt_0"
    microchain_modifiable_system_prompt_1 = "microchain_modifiable_system_prompt_1"
    microchain_modifiable_system_prompt_2 = "microchain_modifiable_system_prompt_2"
    microchain_modifiable_system_prompt_3 = "microchain_modifiable_system_prompt_3"
    microchain_with_goal_manager_agent_0 = "microchain_with_goal_manager_agent_0"
    metaculus_bot_tournament_agent = "metaculus_bot_tournament_agent"
    prophet_gpt4o = "prophet_gpt4o"
    prophet_gpt4 = "prophet_gpt4"
    prophet_gpt4_final = "prophet_gpt4_final"
    prophet_gpt4_kelly = "prophet_gpt4_kelly"
    prophet_o1preview = "prophet_o1preview"
    prophet_o1mini = "prophet_o1mini"
    olas_embedding_oa = "olas_embedding_oa"
    # Social media (Farcaster + Twitter)
    social_media = "social_media"
    omen_cleaner = "omen_cleaner"
    ofv_challenger = "ofv_challenger"
    market_creators_stalker1 = "market_creators_stalker1"
    market_creators_stalker2 = "market_creators_stalker2"
    invalid = "invalid"


RUNNABLE_AGENTS: dict[RunnableAgent, type[DeployableAgent]] = {
    RunnableAgent.coinflip: DeployableCoinFlipAgent,
    RunnableAgent.replicate_to_omen: DeployableReplicateToOmenAgent,
    RunnableAgent.think_thoroughly: DeployableThinkThoroughlyAgent,
    RunnableAgent.think_thoroughly_prophet: DeployableThinkThoroughlyProphetResearchAgent,
    RunnableAgent.knownoutcome: DeployableKnownOutcomeAgent,
    RunnableAgent.microchain: DeployableMicrochainAgent,
    RunnableAgent.microchain_modifiable_system_prompt_0: DeployableMicrochainModifiableSystemPromptAgent0,
    RunnableAgent.microchain_modifiable_system_prompt_1: DeployableMicrochainModifiableSystemPromptAgent1,
    RunnableAgent.microchain_modifiable_system_prompt_2: DeployableMicrochainModifiableSystemPromptAgent2,
    RunnableAgent.microchain_modifiable_system_prompt_3: DeployableMicrochainModifiableSystemPromptAgent3,
    RunnableAgent.microchain_with_goal_manager_agent_0: DeployableMicrochainWithGoalManagerAgent0,
    RunnableAgent.social_media: DeployableSocialMediaAgent,
    RunnableAgent.metaculus_bot_tournament_agent: DeployableMetaculusBotTournamentAgent,
    RunnableAgent.prophet_gpt4o: DeployablePredictionProphetGPT4oAgent,
    RunnableAgent.prophet_gpt4: DeployablePredictionProphetGPT4TurboPreviewAgent,
    RunnableAgent.prophet_gpt4_final: DeployablePredictionProphetGPT4TurboFinalAgent,
    RunnableAgent.olas_embedding_oa: DeployableOlasEmbeddingOAAgent,
    RunnableAgent.omen_cleaner: OmenCleanerAgent,
    RunnableAgent.ofv_challenger: OFVChallengerAgent,
    RunnableAgent.prophet_o1preview: DeployablePredictionProphetGPTo1PreviewAgent,
    RunnableAgent.prophet_o1mini: DeployablePredictionProphetGPTo1MiniAgent,
    RunnableAgent.market_creators_stalker1: MarketCreatorsStalkerAgent1,
    RunnableAgent.market_creators_stalker2: MarketCreatorsStalkerAgent2,
    RunnableAgent.invalid: InvalidAgent,
}

APP = typer.Typer(pretty_exceptions_enable=False)


@APP.command()
def main(
    agent: RunnableAgent,
    market_type: MarketType,
) -> None:
    RUNNABLE_AGENTS[agent]().run(market_type=market_type)


if __name__ == "__main__":
    APP()
