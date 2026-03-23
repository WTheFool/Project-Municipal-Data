from redis import Redis
from rq import Queue

from municipal_worker.infra.settings import settings

redis_conn = Redis.from_url(settings.redis_url)

def get_queue() -> Queue:
    return Queue(settings.rq_queue_name, connection=redis_conn)