import json
import logging

from kafka import KafkaConsumer

logging.basicConfig(
    filename="../logs/kafka.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

consumer = KafkaConsumer(
    'task_events',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='task_manager_group'
)


def start_consumer():
    print("Kafka consumer is running...")
    logging.info("Kafka consumer is running...")
    for message in consumer:
        event = message.value
        print(f"Received event: {event}")
        logging.info(f"Received event: {event}")
        process_event(event)


def process_event(event):
    event_type = event.get('type')
    data = event.get('data')
    # Just print for now; you can expand this
    if event_type == 'created':
        print(f"Task created: {data}")
        logging.info(f"Task created: {data}")
    elif event_type == 'updated':
        print(f"Task updated: {data}")
        logging.info(f"Task updated: {data}")
    elif event_type == 'deleted':
        print(f"Task deleted: {data}")
        logging.info(f"Task deleted: {data}")
    else:
        print(f"Unknown event type: {event_type}")
        logging.info(f"Unknown event type: {event_type}")


if __name__ == "__main__":
    start_consumer()
