import os
from pathlib import Path
from typing import Any

import yaml  # type: ignore
from jinja2 import Environment, FileSystemLoader


def load_config_file(file_path: str) -> dict[str, Any]:
    """
    Load a YAML file with Jinja2 templating.

    Args:
        file_path (str): The path to the YAML file.

    Returns:
        dict: The loaded YAML content as a dictionary.
    """
    path = Path(file_path)
    env = Environment(loader=FileSystemLoader(str(path.parent)))
    template = env.get_template(path.name)

    rendered_yaml: str = template.render(env=os.environ)

    return yaml.safe_load(rendered_yaml)
