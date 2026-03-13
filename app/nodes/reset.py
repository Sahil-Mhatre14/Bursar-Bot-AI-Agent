from app.state import State

def reset_node(state: State) -> State:
    return {
        "result": None,
        "errors": [],
    }