from dotenv import load_dotenv
from config import *

load_dotenv()

def get_env_value(key: str) -> str:
    """
    Retrieves the value of an environment variable.

    Args:
        key (str): The key of the environment variable to retrieve.

    Returns:
        str: The value of the environment variable.
    """
    try:
        value = os.environ.get(key)
        if value == None or value == "":
            if key in PREDEFINED_ENV_VALUES:
                value = PREDEFINED_ENV_VALUES[key]
            else:
                print("Unexpected environment variable requested! Exiting now....")
                logging.error(f"Unexpected environment variable requested - {key}! Exiting now....")
                sys.exit(1)
            os.environ.setdefault(key, str(value))
        return value
    except:
        logging.error("[ENVIRONMENT] Error while getting environment variable: %s - %s" % (key, '; '.join(str(traceback.format_exc()).split('\n'))))
    return ""
        
def set_env_value(key: str, value: str) -> None:
    """
    Sets the value of an environment variable.

    Args:
        key (str): The key of the environment variable to set.
        value (str): The value to set for the environment variable.
    """
    try:
        existing_value = os.environ.get(key)
        if existing_value not in [None, ""]:
            logging.warning("[ENVIRONMENT] Warning! Overwriting previous value: %s for key: %s." % (existing_value, key))
        os.environ.setdefault(key, str(value))
    except:
        logging.error("[ENVIRONMENT] Error while setting environment variable: '%s=%s' - %s" % (key, value, '; '.join(str(traceback.format_exc()).split('\n'))))
