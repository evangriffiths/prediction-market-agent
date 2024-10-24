from datetime import timedelta
from functools import partial

from prediction_market_agent_tooling.config import APIKeys
from prediction_market_agent_tooling.gtypes import (
    ChecksumAddress,
    HexAddress,
    HexBytes,
    xDai,
    xdai_type,
)
from prediction_market_agent_tooling.loggers import logger
from prediction_market_agent_tooling.markets.omen.data_models import (
    OmenMarket,
    RealityQuestion,
    RealityResponse,
)
from prediction_market_agent_tooling.markets.omen.omen_resolving import (
    Resolution,
    claim_bonds_on_realitio_questions,
    finalize_markets,
    find_resolution_on_other_markets,
    resolve_markets,
)
from prediction_market_agent_tooling.markets.omen.omen_subgraph_handler import (
    OmenSubgraphHandler,
)
from prediction_market_agent_tooling.tools.balances import get_balances
from prediction_market_agent_tooling.tools.is_invalid import is_invalid
from prediction_market_agent_tooling.tools.langfuse_ import observe
from prediction_market_agent_tooling.tools.utils import DatetimeUTC, utcnow
from pydantic import BaseModel


class ClaimResult(BaseModel):
    claimed_question_ids: list[HexBytes]
    claimed: xDai


class FinalizeAndResolveResult(BaseModel):
    finalized: list[HexAddress]
    resolved: list[HexAddress]
    claimed: ClaimResult


@observe()
def omen_finalize_and_resolve_and_claim_back_all_markets_based_on_others_tx(
    api_keys: APIKeys,
    realitio_bond: xDai,
) -> FinalizeAndResolveResult:
    public_key = api_keys.bet_from_address
    balances_start = get_balances(public_key)
    logger.info(f"{balances_start=}")

    now = utcnow()

    # Fetch markets created by us that are already open, but no answer was submitted yet or they are challengable.
    get_omen_binary_markets_common_filters = partial(
        OmenSubgraphHandler().get_omen_binary_markets,
        limit=None,
        creator=public_key,
        # We need markets already opened for answers.
        question_opened_before=now,
    )
    created_opened_markets = get_omen_binary_markets_common_filters(
        # Markets with a little bandwidth for the market to be finalized,
        # so we have time for processing it without erroring out at the end.
        question_finalized_after=now
        + timedelta(minutes=30),
    ) + get_omen_binary_markets_common_filters(
        # And markets without any answer at all.
        question_with_answers=False,
    )
    logger.info(f"Found {len(created_opened_markets)} markets to answer.")
    # Finalize them (set answer on Realitio).
    created_opened_markets_with_resolutions = [
        (
            m,
            (
                find_resolution_on_other_markets(m)
                if not is_invalid(m.question_title)
                else Resolution.CANCEL
            ),
        )
        for m in created_opened_markets
    ]
    created_opened_markets_with_resolutions_to_answer = (
        filter_replicated_markets_to_answer(
            created_opened_markets_with_resolutions,
            creator=public_key,
            realitio_bond=realitio_bond,
        )
    )
    logger.info(
        f"Filtered for {len(created_opened_markets_with_resolutions_to_answer)} markets to answer."
    )
    finalized_markets = finalize_markets(
        api_keys,
        created_opened_markets_with_resolutions_to_answer,
        realitio_bond=realitio_bond,
    )
    balances_after_finalization = get_balances(public_key)
    logger.info(f"{balances_after_finalization=}")

    # Fetch markets that are finalized, but we didn't call `resolve` on them yet.
    created_finalized_markets = OmenSubgraphHandler().get_omen_binary_markets(
        limit=None,
        creator=public_key,
        question_finalized_before=now,
        resolved=False,
    )
    # Resolve them (resolve them on Oracle).
    resolved_markets = resolve_markets(
        api_keys,
        created_finalized_markets,
    )
    balances_after_resolution = get_balances(public_key)
    logger.info(f"{balances_after_resolution=}")

    claimed = claim_all_bonds_on_reality(api_keys, finalized_before=now)

    return FinalizeAndResolveResult(
        finalized=finalized_markets,
        resolved=resolved_markets,
        claimed=claimed,
    )


@observe()
def filter_replicated_markets_to_answer(
    markets: list[tuple[OmenMarket, Resolution | None]],
    creator: ChecksumAddress,
    realitio_bond: xDai,
) -> list[tuple[OmenMarket, Resolution | None]]:
    filtered: list[tuple[OmenMarket, Resolution | None]] = []

    for market, possible_resolution in markets:
        existing_responses = OmenSubgraphHandler().get_responses(
            limit=None, question_id=market.question.id
        )
        latest_response = (
            max(existing_responses, key=lambda r: r.timestamp)
            if existing_responses
            else None
        )

        if any(response.user_checksummed == creator for response in existing_responses):
            logger.info(
                f"Market {market.url=} already answered by Replicator. Skipping."
            )
            continue

        if (
            latest_response
            and market.get_resolution_enum_from_answer(latest_response.answer)
            == possible_resolution
        ):
            logger.info(
                f"Market {market.url=} already answered with {possible_resolution=}. Skipping."
            )
            continue

        if any(
            response.bond_xdai >= realitio_bond / 2 for response in existing_responses
        ):
            logger.info(
                f"Market {market.url=} already answered with bond >= {realitio_bond} / 2. Skipping."
            )
            continue

        logger.info(
            f"Market {market.url=} added to finalisation list with {possible_resolution=}."
        )
        filtered.append((market, possible_resolution))

    return filtered


@observe()
def claim_all_bonds_on_reality(
    api_keys: APIKeys, finalized_before: DatetimeUTC | None = None
) -> ClaimResult:
    # Just to be friendly with time differences.
    finalized_before = finalized_before or utcnow()
    public_key = api_keys.bet_from_address

    balances_before_claiming = get_balances(public_key)
    logger.info(f"{balances_before_claiming=}")

    # Fetch our responses that are on already finalised questions, but we didn't claim the bonded xDai yet.
    responses: list[RealityResponse] = OmenSubgraphHandler().get_responses(
        limit=None,
        user=public_key,
        question_claimed=False,
        question_finalized_before=finalized_before,
    )
    # Extract only the unique questions out of responses (there could be multiple responses for the same question, but only the whole question can be claimed once).
    questions: list[RealityQuestion] = list(
        {r.question.questionId: r.question for r in responses}.values()
    )
    claimed_question_ids = claim_bonds_on_realitio_questions(
        api_keys,
        questions,
        auto_withdraw=True,
    )
    balances_after_claiming = get_balances(public_key)
    logger.info(f"{balances_after_claiming=}")

    return ClaimResult(
        claimed_question_ids=claimed_question_ids,
        claimed=xdai_type(balances_after_claiming.xdai - balances_before_claiming.xdai),
    )
