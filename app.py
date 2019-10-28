# -*- coding: utf-8 -*-
import logging
from concurrent import futures

import requests
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
    request = requests.get(url, stream=True)

    logging.info("entering main loop")
    leftover = ""
    for chunk in request.iter_content(32768):
        if chunk:
            logging.debug("processing chunk")
            lines = (leftover + chunk.decode("utf-8")).split("\n")
            leftover = lines[-1]

            logging.debug("sending lines to kafka")
            for line in lines:
                logging.debug("send line to kafka")
                try:
                    producer.produce(topic, line.encode("utf-8"))
                except BufferError:
                    logging.info("BufferError, flushing...")
                    producer.flush()
                    producer.produce(topic, line.encode("utf-8"))

    logging.info("reading csv finished, flushing the kafka producer...")
    producer.flush()
    logging.info("all done")
