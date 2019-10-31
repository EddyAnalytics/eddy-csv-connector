# -*- coding: utf-8 -*-
import codecs
import csv
import logging
from concurrent import futures
from urllib.request import urlopen

from celery import Celery
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient

import config


app = Celery("app", broker="redis://{}:6379".format(config.REDIS_HOST))


logging.basicConfig()
if config.DEBUG:
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.getLogger().setLevel(logging.INFO)


@app.task
def csv_to_kafka(url, topic):
    logging.info("starting kafka producer and admin client")
    logging.info("streaming csv: {} into kafka topic: {}".format(url, topic))
    kafka_config = {"bootstrap.servers": config.BOOTSTRAP_SERVERS}
    producer = Producer(kafka_config)
    admin = AdminClient(kafka_config)

    logging.info("deleting the topic if it exists")
    delete_futures = admin.delete_topics([topic], operation_timeout=1000).values()
    logging.info("waiting for the deletion to complete")
    futures.wait(delete_futures)
    logging.info("deletion completed")

    logging.info("getting csv from url")

    response = urlopen(url)
    csv_reader = csv.reader(codecs.iterdecode(response, "utf-8"))

    logging.info("entering main loop")
    leftover = ""
    for line in csv_reader:
        logging.debug("send line to kafka")
        try:
            producer.produce(topic, ",".join(line).encode("utf-8"))
        except BufferError:
            logging.info("BufferError, flushing...")
            producer.flush()
            producer.produce(topic, ",".join(line).encode("utf-8"))

    logging.info("reading csv finished, flushing the kafka producer...")
    producer.flush()
    logging.info("all done")
