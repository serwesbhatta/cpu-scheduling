import requests

def init(config):
    """
    Description:
        This function will initialize the client and return the `session_id` (next integer used by your client_id) and `clock_start`
    Args:
        config (dict): A dictionary containing the configuration for the client
    Returns:
        dict: A dictionary containing the session_id and clock_start
    """
    route = f"http://profgriffin.com:8000/init"
    r = requests.post(route, json=config)
    if r.status_code == 200:
        response = r.json()
        return response
    else:
        print(f"Error: {r.status_code}")
        return None
