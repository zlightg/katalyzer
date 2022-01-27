from typing import Dict, Text
import pandas as pd
import numpy as np
import tensorflow as tf

import tensorflow_datasets as tfds
import tensorflow_recommenders as tfrs

# load emotions activities data
emotion_activities = tf.data.experimental.CsvDataset(
  "datasets/emotion_activities_with_time.csv",
  [
    tf.string, #  User ID
    tf.string,  # Emotion
    tf.string,  # emotion id
     tf.string,  # activity
     tf.string,  # activity id
     tf.int32,
     tf.int32,
  ],
  header=True,
  select_cols=[0,1,2,3,4,5,6]  # parse all columns
)
# Features of all the activities
activities =tf.data.experimental.CsvDataset(
  "datasets/activity.csv",
  [tf.string,  # Required field, use dtype or empty tensor
   tf.int32,  # Required field, use dtype or empty tensor
  ],
  header=True,
  select_cols=[0,1]  # Only parse first two columns
)


emotion_activities = emotion_activities.map(lambda a,b,c,d,e,f,g: {
    "userId": a,
    "emotion": b,
    "emotionId": c,
    "activity": d,
    "activityId": e,
    "hour": f,
    "dow": g,
})

activities = activities.map(lambda x,y: x)

#Get unique activities
unique_activities = np.unique(np.concatenate(list(activities.batch(32))))

# get unique user ids
unique_user_ids = np.unique(np.concatenate(list(emotion_activities.batch(32).map(
    lambda x: x["userId"]))))

unique_feeling_ids = np.unique(np.concatenate(list(emotion_activities.batch(32).map(
    lambda x: x["emotion"]))))

# prepare time features

day_of_week = np.concatenate(list(emotion_activities.map(lambda x: x["dow"]).batch(32)))

max_day_of_week = day_of_week.max()
min_day_of_week = day_of_week.min()

day_of_week_buckets = np.linspace(
    min_day_of_week, max_day_of_week, num=7,
)

hour = np.concatenate(list(emotion_activities.map(lambda x: x["hour"]).batch(32)))

max_hour = hour.max()
min_hour = hour.min()

hour_buckets = np.linspace(
    min_hour, max_hour, num=24,
)

class UserModel(tf.keras.Model):

  def __init__(self):
    super().__init__()

    self.day_of_week_embedding = tf.keras.Sequential([
        tf.keras.layers.Discretization(day_of_week_buckets.tolist()),
        tf.keras.layers.Embedding(len(day_of_week_buckets) + 1, 32),
    ])

    self.normalized_day_of_week = tf.keras.layers.Normalization(
        axis=None
    )

    self.normalized_day_of_week.adapt(day_of_week)

    self.hour_embedding = tf.keras.Sequential([
        tf.keras.layers.Discretization(hour_buckets.tolist()),
        tf.keras.layers.Embedding(len(hour_buckets) + 1, 32),
    ])

    self.normalized_hour = tf.keras.layers.Normalization(
        axis=None
    )

    self.normalized_hour.adapt(hour)

    self.user_embedding = tf.keras.Sequential([
        tf.keras.layers.StringLookup(
            vocabulary=unique_user_ids, mask_token=None),
        tf.keras.layers.Embedding(len(unique_user_ids) + 1, 32),
    ])
    self.feelings_embedding = tf.keras.Sequential([
        tf.keras.layers.StringLookup(
            vocabulary=unique_feeling_ids, mask_token=None),
        tf.keras.layers.Embedding(len(unique_feeling_ids) + 1, 32),
    ])

  def call(self, inputs):
    # Take the input dictionary, pass it through each input layer,
    # and concatenate the result.
    return tf.concat([
        self.user_embedding(inputs["userId"]),
        self.feelings_embedding(inputs["emotion"]),
        self.day_of_week_embedding(inputs["dow"]),
        tf.reshape(self.normalized_day_of_week(inputs["dow"]), (-1, 1)),
        self.hour_embedding(inputs["hour"]),
        tf.reshape(self.normalized_hour(inputs["hour"]), (-1, 1)),
    ], axis=1)

class QueryModel(tf.keras.Model):
  """Model for encoding user queries."""

  def __init__(self, layer_sizes):
    """Model for encoding user queries.

    Args:
      layer_sizes:
        A list of integers where the i-th entry represents the number of units
        the i-th layer contains.
    """
    super().__init__()

    # We first use the user model for generating embeddings.
    self.embedding_model = UserModel()

    # Then construct the layers.
    self.dense_layers = tf.keras.Sequential()

    # Use the ReLU activation for all but the last layer.
    for layer_size in layer_sizes[:-1]:
      self.dense_layers.add(tf.keras.layers.Dense(layer_size, activation="relu"))

    # No activation for the last layer.
    for layer_size in layer_sizes[-1:]:
      self.dense_layers.add(tf.keras.layers.Dense(layer_size))

  def call(self, inputs):
    feature_embedding = self.embedding_model(inputs)
    return self.dense_layers(feature_embedding)


class ActivityModel(tf.keras.Model):

  def __init__(self):
    super().__init__()

    max_tokens = 10000

    self.activity_embedding = tf.keras.Sequential([
      tf.keras.layers.StringLookup(
          vocabulary=unique_activities,mask_token=None),
      tf.keras.layers.Embedding(len(unique_activities) + 1, 32)
    ])


  def call(self, titles):
    return tf.concat([
        self.activity_embedding(titles),
    ], axis=1)


class CandidateModel(tf.keras.Model):
  """Model for encoding movies."""

  def __init__(self, layer_sizes):
    """Model for encoding movies.

    Args:
      layer_sizes:
        A list of integers where the i-th entry represents the number of units
        the i-th layer contains.
    """
    super().__init__()

    self.embedding_model = ActivityModel()

    # Then construct the layers.
    self.dense_layers = tf.keras.Sequential()

    # Use the ReLU activation for all but the last layer.
    for layer_size in layer_sizes[:-1]:
      self.dense_layers.add(tf.keras.layers.Dense(layer_size, activation="relu"))

    # No activation for the last layer.
    for layer_size in layer_sizes[-1:]:
      self.dense_layers.add(tf.keras.layers.Dense(layer_size))

  def call(self, inputs):
    feature_embedding = self.embedding_model(inputs)
    return self.dense_layers(feature_embedding)

class FeelinglensModel(tfrs.models.Model):

  def __init__(self, layer_sizes):
    super().__init__()
    self.query_model = QueryModel(layer_sizes)
    self.candidate_model = CandidateModel(layer_sizes)
    self.task = tfrs.tasks.Retrieval(
        metrics=tfrs.metrics.FactorizedTopK(
            candidates=activities.batch(128).map(self.candidate_model),
        ),
    )

  def compute_loss(self, features, training=False):
    # We only pass the user id and timestamp features into the query model. This
    # is to ensure that the training inputs would have the same keys as the
    # query inputs. Otherwise the discrepancy in input structure would cause an
    # error when loading the query model after saving it.
    query_embeddings = self.query_model({
        "userId": features["userId"],
        "emotion": features["emotion"],
        "dow": features["dow"],
        "hour": features["hour"]
    })
    activity_embeddings = self.candidate_model(features["activity"])

    return self.task(
        query_embeddings, activity_embeddings, compute_metrics=not training)

# TODO split training and test data and measure accuracy

num_epochs = 300

model = FeelinglensModel([64, 32])
model.compile(optimizer=tf.keras.optimizers.Adagrad(0.1))
model.fit(emotion_activities.batch(4096), epochs=30)


# Use brute-force search to set up retrieval using the trained representations.
index = tfrs.layers.factorized_top_k.BruteForce(model.query_model)
## TODO REMOVE
#index.index(activities.batch(1024).map(model.candidate_model), identifiers=activities)

# recommends movies out of the entire movies dataset.
index.index_from_dataset(
  tf.data.Dataset.zip((activities.batch(100), activities.batch(100).map(model.candidate_model)))
)

# _, titles = index(np.array(["1","2"])
_, titles = index({"userId": tf.constant(["2"]),
                   "emotion": tf.constant(["Sad"]),
                   "dow":tf.constant([4]),
                   "hour": tf.constant([7])})

print(f"Top recommendations for user 1 and emotion id: Sad: {titles[0, :1]}")

tf.saved_model.save(index, "models")