import time

import queries
from queries import Query
from templateParser import resultProcessor
import tensorflow as tf
import json
path = "models"
# Load it back; can also be done in TensorFlow Serving.
loaded = tf.saved_model.load(path)
import csv


## TODO MOVE TO DB CALL BELOW

def readFileToDict(filename):
    dict = {}
    with open (filename, "r") as csv_file:
      csv_reader = csv.DictReader(csv_file, delimiter=',')
      for line in csv_reader:
          dict[line["name"]] = line["id"]
    return dict
activities = readFileToDict("datasets/activity.csv")
feelings = readFileToDict("datasets/feelings.csv")

## TODO move to DB call above

class Processor:
    q = Query()

    ## TODO move test functions to test file below ##
    def add(self, x, y):
        return x + y

    def subtract(self, x, y):
        return x - y

    ## TODO move test functions to test file above ##

    def getConversationId(self, user_id):
        ### TODO init conversation if it does not exist
        result = self.q.execute("SELECT id from conversation where human_user_id = {} LIMIT 1".format(user_id))
        return result[0].id

    def getUserId(self):
        # Kick back to user auth if we can't find the user
        return -1

    def getLastMessageStateId(self, state, conversation_id):
        ### TODO init first message if it does not exist
        query = "SELECT state_id, persisted_state from message where conversation_id = {} AND sender_id = 0" \
                "AND state_id not in (SELECT id from message_state where is_followup) ORDER BY sent_at desc limit 1".format(
            conversation_id)
        result = self.q.execute(query)
        ## TODO MOVE TO IT's OWN CALL
        state['persisted'] = json.loads(result[0]["persisted_state"])
        return result[0].state_id

    def getLastMessageState(self, last_message_state_id):
        result = self.q.execute("SELECT * FROM message_state where id = {} LIMIT 1".format(last_message_state_id))
        return dict(result[0])

    def getNextMessageState(self, last_message_state, state):
        # TODO CLEAN UP
        if 'next_state_id_func' in state:
          next_message_state_id = resultProcessor(state['next_state_id_func'], state, self)
        else:
          next_message_state_id = resultProcessor(last_message_state['next_state_id_func'], state, self)
        result = self.q.execute("SELECT * FROM message_state where id = {} LIMIT 1".format(next_message_state_id))
        return dict(result[0])

    def getSenderID(self, state):
        return state.model_user_id

    def getTime(self, state):
        return int(time.time())

    def getCategories(self, category):
        result = self.q.execute("SELECT name from {}".format(category))
        return [row["name"] for row in result]

    def getFeelings(self, state):
        result = self.q.execute("SELECT name from feeling")
        return ", ".join([row["name"] for row in result])

    def getActivities(self, state):
        result = self.q.execute("SELECT name from activity")
        return ", ".join([row["name"] for row in result])

    def getCategory(self, conversation_id):
        query = "SELECT category FROM message_state where id in (SELECT state_id from message where conversation_id = {} AND sender_id = 0 ORDER BY sent_at desc limit 1)".format(conversation_id)
        result = self.q.execute(query)
        return result[0]["category"]

    def getRankedActivities(self, user_id, message, context):
        _, activities = loaded({"userId": tf.constant([user_id]),
                                "emotion": tf.constant([message]),
                                "dow": tf.constant([context["dow"]]),
                                "hour": tf.constant([context["hour"]])
                                })
        activity_list = [x.decode('utf-8') for x in activities[0].numpy().tolist()]
        return ", ".join(activity_list[:3])

    def persistState(self, state, key, val):
        if 'persisted' in state:
            state['persisted'][key.lower()] = val
        elif 'persisted' not in state:
            state['persisted'] = {key: val}

    def unpersistState(self, state, key):
        if 'persisted' in state and key.lower() in state['persisted']:
            state['persisted'].pop(key.lower())

    def addEntry(self, user_id, feeling, last_activity, context):
        with open('datasets/emotion_activities_with_time.csv', 'a') as fd:
            activityID = activities[last_activity]
            feelingID = feelings[feeling]
            row = "\n" + ",".join([str(user_id), feeling, feelingID, last_activity, activityID, str(context["hour"]), str(context["dow"])])
            fd.write(row)
        return "success"

    ## TODO MOVE next state funcs to another class
    def getInitMessageState(self, state, conversation_id):
        # TODO get sender id from conversation id non human entity
        if "next_message_state_id" in state and state["next_message_state_id"] is not None:
            value = state["next_message_state_id"]
            state["next_message_state_id"] = None
            return value
        else:
            query = "SELECT state_id, persisted_state from message where conversation_id = {} AND sender_id = 0" \
                    "AND state_id not in (SELECT id from message_state where is_followup) ORDER BY sent_at desc limit 1".format(conversation_id)
            result = self.q.execute(query)
            state['persisted'] = json.loads(result[0]["persisted_state"])
            return result[0]["state_id"]

    def getNextMessageStateIDIfAccepted(self, state, message, categories, next_message_state_id,
                                        other_next_message_state_id):
        state['planned_id'] = next_message_state_id
        if message in categories:
            return next_message_state_id
        else:
            return other_next_message_state_id

    def getIsCooledDown(self, conversation_id, message_state_id):
        query = "SELECT cool_down_interval < NOW() - sent_at as is_true FROM " \
                "(SELECT cool_down_interval FROM cool_down WHERE message_state = {}) q1," \
                "(SELECT sent_at FROM message WHERE conversation_id = {} AND state_id = {} " \
                "ORDER BY sent_at DESC limit 1) q2".format(message_state_id, conversation_id, message_state_id)
        result = self.q.execute(query)
        return bool(result[0]["is_true"])

    def getNextMessageIfTrue(self, expression, next_message_state_id, other_message_state_id):
        if expression:
            return next_message_state_id
        else:
            return other_message_state_id

    def isEqual(self, message, expression):
        return message.lower() == expression.lower()

    def getUserIdFromCode(self, state, user_code):
        query = "SELECT id from user_info where hash_lookup = '{}'".format(user_code)
        ## TODO make this less ugly
        try:
            result = self.q.execute(query)
            state["user_id"] = result[0]["id"]
            result = self.q.execute("SELECT id from conversation where human_user_id = {} LIMIT 1".format(state["user_id"]))
            state["conversation_id"] = result[0]["id"]
            return result[0]["id"]
        except:
            print("No user code found")
            return False

    def getUserCode(self, state):
        query = "SELECT uuid_generate_v1() as user_code"
        result = self.q.execute(query)
        user_code = result[0]["user_code"]
        insert_stmt = "INSERT INTO user_info (id, hash_lookup) VALUES (nextval('user_info_id_seq'),'{}')".format(user_code)
        self.q.insert(insert_stmt)
        user_query = "SELECT id FROM user_info WHERE hash_lookup = '{}'".format(user_code)
        result = self.q.execute(user_query)
        state["user_id"] = result[0]["id"]
        insert_stmt = "INSERT INTO conversation (id, human_user_id, model_user_id) VALUES (nextval('conversation_id_seq'),{},0)".format(state["user_id"])
        self.q.insert(insert_stmt)
        result = self.q.execute("SELECT id from conversation where human_user_id = {} LIMIT 1".format(state["user_id"]))
        state["conversation_id"] = result[0]["id"]
        state["next_message_state_id"] = 2
        return user_code

