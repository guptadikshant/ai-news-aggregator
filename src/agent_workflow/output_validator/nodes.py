from langchain_core.messages import HumanMessage, SystemMessage

from src.agent_workflow.core.models import ValidateOutput
from src.agent_workflow.core.state import NewsAggregatorState
from src.agent_workflow.prompts.output_validation import SYSTEM_PROMPT
from src.utils.llm_client import get_openai_client
from src.utils.logger import init_logging

logger = init_logging(__name__)


async def model_completion(system_prompt: str, user_prompt: str) -> dict | None:
    """
    Generate a model completion based on the provided system and user prompts.
    Args:
        system_prompt (str): The system prompt to guide the model's behavior.
        user_prompt (str): The user prompt containing the query or input.

    Returns:
        dict | None: The model's response as a dictionary, or None if an error occurs.
    """
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        llm = get_openai_client()
        structured_llm = llm.with_structured_output(ValidateOutput)
        response = await structured_llm.ainvoke(messages)
        if isinstance(response, ValidateOutput):
            validated_output = response
        else:
            validated_output = ValidateOutput.model_validate(response)
        logger.info("Model completion successful")
        return validated_output.model_dump()
    except Exception as e:
        logger.error(f"Error in model completion: {e}")
        return None


async def validate_output_node(state: NewsAggregatorState) -> dict:
    """
    Validate the output generated from the scraping tools against the user's query.
    Iterates through each platform's scraped data individually.

    Args:
        state (NewsAggregatorState): The current state of the news aggregator.

    Returns:
        dict: Updated state fields based on validation result.
    """
    user_query = state.messages[-1].content
    scraped_data = state.scraped_results
    analysis = state.analyse_output

    platforms_to_retry = []

    for platform, data in scraped_data.items():
        if not data:
            logger.warning(f"No data for platform: {platform}, marking for retry")
            platforms_to_retry.append(platform)
            continue

        validation_input = (
            f"User Query: {user_query}\n"
            f"Analysis Output: {analysis}\n"
            f"Platform: {platform}\n"
            f"Scraped Data: {data}\n"
            f"Validate whether the scraped data from {platform} is relevant "
            f"to the user query and provide feedback if it is not."
        )

        result = await model_completion(
            system_prompt=SYSTEM_PROMPT, user_prompt=validation_input
        )

        if not result:
            logger.warning(f"Validation call failed for {platform}, skipping")
            continue

        logger.info(
            f"Validation for {platform} — is_valid: {result['is_valid']}, "
            f"retry: {result['retry']}, feedback: {result['feedback']}"
        )

        if not result["is_valid"] and result["retry"]:
            platforms_to_retry.append(platform)

    needs_retry = len(platforms_to_retry) > 0
    logger.info(
        f"Validation complete — needs_retry: {needs_retry}, "
        f"platforms_to_retry: {platforms_to_retry}"
    )

    return {
        "retry": needs_retry,
        "retry_count": state.retry_count + (1 if needs_retry else 0),
        "selected_platforms": platforms_to_retry
        if needs_retry
        else state.selected_platforms,
        "current_step": "validator",
    }


def should_retry(state: NewsAggregatorState) -> str:
    """
    Decide whether to retry scraping or proceed to end.

    Returns:
        "call_tools" if retry is needed and under max retries, else "end".
    """
    if state.retry and state.retry_count <= state.max_retry:
        logger.info(
            f"Retrying scraping (attempt {state.retry_count}/{state.max_retry})"
        )
        return "call_tools"
    logger.info("Validation passed or max retries reached, proceeding to end")
    return "end"
