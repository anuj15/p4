import json
import logging

from kafka import KafkaProducer

logging.basicConfig(
    filename="logs/kafka.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)


def send_task_event(event_type, task_data):
    event = {
        'type': event_type,
        'data': task_data
    }
    producer.send('task_events', value=event)
    producer.flush()
