import random
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash
import logging
from db import get_db_connection
from kafka_manager.producer import send_task_event


def generate_dummy_data():
    conn = get_db_connection()
    cur = conn.cursor()

    users = [{"username": f"user{i}", "email": f"user{i}@example.com", "password": f"pass{i}"} for i in range(101, 201)]
    tasks = [
        "Write report", "Fix bug", "Refactor code", "Push to Git", "Review PR",
        "Update docs", "Create UI", "Test feature", "Deploy app", "Write tests"
    ]

    for user in users:
        hashed_password = generate_password_hash(user["password"])
        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (user["username"], user["email"], hashed_password)
        )
        logging.info(f"Signup successful for user: {user["username"]} with email: {user["email"]}")
        user_id = cur.fetchone()[0]

        for _ in range(101):
            title = random.choice(tasks)
            description = f"{title}_{_}"
            created_at = datetime.now() - timedelta(days=random.randint(0, 30))
            completed =  random.choice([True, False])
            cur.execute(
                "INSERT INTO tasks (user_id, title, description, completed, created_at) VALUES (%s, %s, %s, %s, %s)",
                (user_id, title, description, completed, created_at)
            )
            logging.info(f"Task created with title: {title} and description: {description} by user: {user_id}")
            send_task_event('created', {
                'user_id': user_id,
                'title': title,
                'description': description
            })

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Dummy data inserted.")


if __name__ == "__main__":
    generate_dummy_data()
