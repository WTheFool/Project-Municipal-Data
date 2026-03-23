import os
import time
from rq import Worker, Queue, Connection
from worker.src.municipal_worker.infra.queue_rq import redis_conn

listen = ["analysis"]  # queue name

if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker(map(Queue, listen))
        print("Worker started, listening on queues:", listen)
        worker.work()