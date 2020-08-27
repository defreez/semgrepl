import argparse
import uuid
import dialogflow_v2 as dialogflow
import utils

function_map = {
    'find-calls': utils.find_function_calls,
    'all-classes': utils.all_classes,
}

target = "/home/daniel/ppa/semgrep_repl/clusterfuzz/src/appengine/server.py"
rules_dir = "../rules"

def natgrep(text):
    """Returns the result of detect intent with texts as inputs.

    Using the same `session_id` between requests allows continuation
    of the conversation."""

    session_id = uuid.uuid4()
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path("semgrepl", session_id)

    text_input = dialogflow.types.TextInput(
        text=text, language_code="en_US")

    query_input = dialogflow.types.QueryInput(text=text_input)

    response = session_client.detect_intent(
        session=session, query_input=query_input)

    params = dict()
    for p in response.query_result.parameters:
        params[p] = response.query_result.parameters[p]

    #import ipdb; ipdb.set_trace()
    try:
        result = function_map[response.query_result.intent.display_name](target, rules_dir, **params)
    except:
        return None

    return result
