import uuid


def validate_context_key(key: str) -> tuple[str, str]:
    """
    Validate the format of a key.

    Args:
        key (str): The key to validate.

    Returns:
        tuple[str, str]: A tuple containing the plan ID and file path or URL.

    Raises:
        ValueError: If the key is not in the correct format.
    """
    if not key.startswith("context|"):
        raise ValueError(
            "Key must be in the format 'context|<plan_id>|<file_path_or_url>'"
        )
    if key.count("|") != 2:
        raise ValueError(
            "Key must be in the format 'context|<plan_id>|<file_path_or_url>'"
        )

    _, plan_id, file_path_or_url = key.split("|")
    if not plan_id or not file_path_or_url:
        raise ValueError(
            "Key must be in the format 'context|<plan_id>|<file_path_or_url>'"
        )
    try:
        uuid.UUID(plan_id)
    except ValueError:
        message = (
            "Plan ID must be a valid UUID. Key must be in the format "
            "'context|<plan_id>|<file_path_or_url>'"
        )
        raise ValueError(message) from None

    return plan_id, file_path_or_url


def validate_blackboard_key(key: str) -> tuple[str, None, None]:
    """
    Validate the format of a key.

    Args:
        key (str): The key to validate.

    Returns:
        tuple[str, None, None]: A tuple containing the plan ID and None values.

    Raises:
        ValueError: If the key is not in the correct format.
    """
    if not key.startswith("blackboard|"):
        raise ValueError("Key must be in the format 'blackboard|<plan_id>'")
    if key.count("|") != 1:
        raise ValueError("Key must be in the format 'blackboard|<plan_id>'")

    _, plan_id = key.split("|")
    if not plan_id:
        raise ValueError("Key must be in the format 'blackboard|<plan_id>'")
    try:
        uuid.UUID(plan_id)
    except ValueError:
        message = (
            "Plan ID must be a valid UUID. Key must be in the format "
            "'blackboard|<plan_id>'"
        )
        raise ValueError(message) from None

    return plan_id, None, None


def validate_plan_key(key: str) -> tuple[str, None, None]:
    """
    Validate the format of a key.

    Args:
        key (str): The key to validate.

    Returns:
        tuple[str, None, None]: A tuple containing the plan ID and None values.

    Raises:
        ValueError: If the key is not in the correct format.
    """
    if not key.startswith("plan|"):
        raise ValueError("Key must be in the format 'plan|<plan_id>'")
    if key.count("|") != 1:
        raise ValueError("Key must be in the format 'plan|<plan_id>'")

    _, plan_id = key.split("|")
    if not plan_id:
        raise ValueError("Key must be in the format 'plan|<plan_id>'")
    try:
        uuid.UUID(plan_id)
    except ValueError:
        message = (
            "Plan ID must be a valid UUID. Key must be in the format "
            "'plan|<plan_id>'"
        )
        raise ValueError(message) from None

    return plan_id, None, None


def validate_result_key(key: str) -> tuple[str, str, str]:
    """
    Validate the format of a key.

    Args:
        key (str): The key to validate.

    Returns:
        tuple[str, str, str]: A tuple containing the plan ID, agent name, and step ID.

    Raises:
        ValueError: If the key is not in the correct format.
    """
    if not key.startswith("result|"):
        raise ValueError(
            "Key must be in the format 'result|<plan_id>|<agent_name>|<step_id>'"
        )
    if key.count("|") != 3:
        raise ValueError(
            "Key must be in the format 'result|<plan_id>|<agent_name>|<step_id>'"
        )
    _, plan_id, agent_name, step_id = key.split("|")
    if not plan_id or not agent_name or not step_id:
        raise ValueError(
            "Key must be in the format 'result|<plan_id>|<agent_name>|<step_id>'"
        )
    if not agent_name.isalpha():
        raise ValueError(
            "Key must be in the format 'result|<plan_id>|<agent_name>|<step_id>'"
        )
    try:
        uuid.UUID(plan_id)
    except ValueError:
        message = (
            "Plan ID must be a valid UUID. Key must be in the format "
            "'result|<plan_id>|<agent_name>|<step_id>'"
        )
        raise ValueError(message) from None

    if not step_id.isdigit():
        message = (
            "Step ID must be a digit. Key must be in the format "
            "'result|<plan_id>|<agent_name>|<step_id>'"
        )
        raise ValueError(message)

    return plan_id, agent_name, step_id


def validate_memory_key(key: str) -> tuple[str, str | None, str | None]:
    """
    Validate the format of a key.

    Args:
        key (str): The key to validate.

    Returns:
        tuple[str, str | None, str | None]: A tuple containing the plan ID,
            agent name, and step ID.

    Raises:
        ValueError: If the key is not in the correct format.
    """
    if key.startswith("plan|"):
        return validate_plan_key(key)

    if key.startswith("blackboard|"):
        return validate_blackboard_key(key)

    if key.startswith("result|"):
        return validate_result_key(key)

    message = (
        "Key must be in the format 'plan|<plan_id>', 'blackboard|<plan_id>' "
        "or 'result|<plan_id>|<agent_name>|<step_id>'"
    )
    raise ValueError(message) from None
