import random
import uuid
import json
import redis
import time

from datetime import datetime

countries = {'IT', 'FR', 'EN', 'US', 'CH', 'RU', 'DE', 'NE', 'JP'}


def create_fake_event(clip_length=4, publisher_length=2):
    """
    Create a new random fake event.
    :param clip_length:
    :param publisher_length:
    :return: dictionary
    """
    clip_id = str(random.randint(0, 10 ** clip_length)).zfill(clip_length)
    country = random.sample(countries, 1)[0]
    event_id = str(uuid.uuid4())
    publisher_id = str(random.randint(0, 10 ** publisher_length)).zfill(publisher_length)
    viewable_time = random.randrange(0, 300) / 10.0
    ts = datetime.now().timestamp()

    event = {
        'clip': clip_id,
        'country': country,
        'event_id': event_id,
        'publisher_id': publisher_id,
        'viewable_time': viewable_time,
        'timestamp': ts
    }

    return event


"""
REDIS - Pipelines
Pipelines are a subclass of the base Redis class that provide support for buffering multiple commands to the server
in a single request. They can be used to dramatically increase the performance of groups of commands by reducing
the number of back-and-forth TCP packets between the client and server.
"""


def recursive_pipeline(pipe, fake_event_creator, pipeline_length, event_id_key):
    """
    Given an empty redis pipeline, fulfill it with a set of fake events, recursively.
    :param pipe:
    :param fake_event_creator:
    :param pipeline_length:
    :param event_id_key:
    :return:
    """
    fake_event = fake_event_creator()
    if pipeline_length == 1:
        return pipe.set(fake_event[event_id_key], json.dumps(fake_event))
    return recursive_pipeline(pipe.set(fake_event[event_id_key], json.dumps(fake_event)),
                              fake_event_creator,
                              pipeline_length - 1,
                              event_id_key)


def create_pipeline(redis_connection, fake_event_creator, pipeline_length=100, event_id_key='event_id'):
    """
    Create a redis pipeline, full with a set of fake events, ready to be published.
    :param redis_connection:
    :param fake_event_creator:
    :param pipeline_length:
    :param event_id_key:
    :return:
    """
    assert pipeline_length >= 0
    initial_pipe = redis_connection.pipeline()
    final_pipe = recursive_pipeline(initial_pipe, fake_event_creator, pipeline_length, event_id_key)
    return final_pipe


class Pipe:
    def __init__(self):
        self.diz = dict()
        pass

    def set(self, key, value):
        self.diz[key] = value
        return self

    def get(self, key):
        return self.get(key)


def main():
    rc = redis.StrictRedis(host='localhost', port=6379, db=0)
    for n in range(10):
        pipe = Pipe()
        final_pipe = recursive_pipeline(pipe, create_fake_event, pipeline_length=100, event_id_key='event_id')
        events_to_send = list(final_pipe.diz.values())
        rc.publish('events', events_to_send)
        time.sleep(5)
    return


if __name__ == '__main__':
    main()
