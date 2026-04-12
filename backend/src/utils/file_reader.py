import yaml

def read_yaml(file_path: str) -> dict:
    """Read a yaml file and return the content as a dictionary

    Args:
        file_path (str): path to the yaml file

    Returns:
        dict: content of the yaml file as a dictionary
    """
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)