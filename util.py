import csv
from templateParser import processTemplate, messageStateProcessor, resultProcessor
from processor import Processor

p = Processor()
def readFileToDict(filename):
    dict = {}
    with open (filename, "r") as csv_file:
      csv_reader = csv.DictReader(csv_file, delimiter=',')
      for line in csv_reader:
          dict[line["name"]] = line["id"]
    return dict

def saveMessage(state, proccesor):
    if state["conversation_id"] == -1:
        return False
    if 'persisted' in state:
        persisted = str(state['persisted'])
    else:
        persisted = '{}'
    insert_statement = "INSERT INTO message (conversation_id, sender_id, state_id, message, persisted_state) VALUES ({},{},{},'{}','{}')".format(
        state["conversation_id"],
        state["sender_id"],
        state["id"],
        state["message"].replace("'","''"),
        persisted.replace("'",'"')
    )
    proccesor.q.insert(insert_statement)

def produceMessage(state, proccesor):
    if state["next_message_state"]["message_template"] is not None:
        message = processTemplate(state["next_message_state"]["message_template"], state, proccesor)
    else:
        message = ""
    next_message_state = state["next_message_state"]
    next_message_state["user_id"] = state["user_id"]
    # TODO select from robo id
    next_message_state["sender_id"] = 0
    next_message_state["conversation_id"] = state["conversation_id"]
    if "next_message_state_id" in state:
        next_message_state["next_message_state_id"] = state["next_message_state_id"]
    next_message_state["message"] = message
    if 'persisted' in state:
        next_message_state['persisted'] = state['persisted']
    else:
        next_message_state['persisted'] = {}
    saveMessage(next_message_state,proccesor)
    message = {
      "conversation_id": state["conversation_id"],
      # TODO populate
      "sender_id": 0,
      "state": next_message_state,
      "message": message,
      "category": next_message_state["category"],
      "sent_at":   proccesor.getTime(next_message_state),
      "pre_message_processor": next_message_state["pre_message_processor"],
      "post_message_processor": next_message_state["post_message_processor"]
    }

    return message

def processMessage(message):
    print("request below")
    print(message)
    if "message" in message:
        message["state"]["message"] = message["message"]
    if "pre_message_processor" in message and message["pre_message_processor"] is not None:
       funcs = message['pre_message_processor'].split("/n")
       [resultProcessor(func, message['state'], p) for func in funcs]

    # calc next message state
    message['state']['next_message_state'] = resultProcessor("$next_message_state", message['state'], p)


    if "post_message_processor" in message['state']['next_message_state'] and message['state']['next_message_state']['post_message_processor'] is not None:
       funcs = message['state']['next_message_state']['post_message_processor'].split("\n")
       [resultProcessor(func, message['state'], p) for func in funcs]

    ## TODO move to it's own function and share call with produce message
    message["state"]["sender_id"] = message["state"]["user_id"]
    if "id" not in message["state"]:
        message["state"]["id"] = message["state"]["next_message_state"]["id"]
    if "message" not in message["state"]:
        message["state"]["message"] = ""
    saveMessage(message["state"], p)
    ## TODO REFACTOR ABOVE

    message = produceMessage(message['state'], p)
    print("response below")
    print(message)
    return message
