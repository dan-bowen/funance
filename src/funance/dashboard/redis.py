import hashlib
import io
import json
import os
import warnings

import fakeredis
import pandas as pd
import plotly
import redis


class RedisStore:
    """Save data to Redis using the hashed contents as the key.
    Serialize Pandas DataFrames as memory-efficient Parquet files.

    Otherwise, attempt to serialize the data as JSON, which may have a
    lossy conversion back to its original type. For example, numpy arrays will
    be deserialized as regular Python lists.

    Connect to Redis with the environment variable `REDIS_URL` if available.
    Otherwise, use FakeRedis, which is only suitable for development and
    will not scale across multiple processes.
    """
    if 'REDIS_URL' in os.environ:
        r = redis.StrictRedis.from_url(os.environ["REDIS_URL"])
    else:
        warnings.warn('Using FakeRedis - Not suitable for Production Use.')
        r = fakeredis.FakeStrictRedis()

    @staticmethod
    def _hash(serialized_obj):
        return hashlib.sha512(serialized_obj).hexdigest()

    @staticmethod
    def save(value):
        if isinstance(value, pd.DataFrame):
            buffer = io.BytesIO()
            value.to_parquet(buffer, compression='gzip')
            buffer.seek(0)
            df_as_bytes = buffer.read()
            hash_key = RedisStore._hash(df_as_bytes)
            type = 'pd.DataFrame'
            serialized_value = df_as_bytes
        else:
            serialized_value = json.dumps(value, cls=plotly.utils.PlotlyJSONEncoder).encode('utf-8')
            hash_key = RedisStore._hash(serialized_value)
            type = 'json-serialized'

        RedisStore.r.set(
            f'_dash_aio_components_value_{hash_key}',
            serialized_value
        )
        RedisStore.r.set(
            f'_dash_aio_components_type_{hash_key}',
            type
        )
        return hash_key

    @staticmethod
    def load(hash_key):
        data_type = RedisStore.r.get(f'_dash_aio_components_type_{hash_key}')
        serialized_value = RedisStore.r.get(f'_dash_aio_components_value_{hash_key}')
        try:
            if data_type == b'pd.DataFrame':
                value = pd.read_parquet(io.BytesIO(serialized_value))
            else:
                value = json.loads(serialized_value)
        except Exception as e:
            print(e)
            print(f'ERROR LOADING {data_type - hash_key}')
            raise e
        return value