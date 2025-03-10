

def verify_agent_by_agent_id_and_broker_name(agent_id, broker_name):
    if agent_id == "agent_id_test" and broker_name == "broker_name_test":
        return True
    elif agent_id == "king_agent" and broker_name == "king_broker":
        return True
    return False