import requests

def getJob(client_id, session_id, clock_time):
    """
    Description:
        This function will get the jobs available at the current clock time
    Args:
        client_id (str): The client_id
        session_id (int): The session_id
        clock_time (int): The current clock time
    Returns:
        dict: A dictionary containing the jobs available at the current clock time
    Example Response:
        "data": [
            {
            "job_id": 1,
            "session_id": 13,
            "arrival_time": 1989,
            "priority": 2
            }
        ]
    """
    route = f"http://profgriffin.com:8000/job?client_id={client_id}&session_id={session_id}&clock_time={clock_time}"
    r = requests.get(route)
    if r.status_code == 200:
        response = r.json()
        return {
            "success": True,
            "message": response
        }
    else:
        return {"success": False, "message": f"Error: {r.status_code}"}
