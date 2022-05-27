import json
import os

import attr
from funance.scrape.common import Paths

SESSION_FILE = os.path.join(Paths.TMP_DIR, 'session.json')


@attr.define(kw_only=True)
class Session:
    executor_url: str = attr.ib()
    session_id: str = attr.ib()
    chromedriver_version: str = attr.ib()

    @classmethod
    def init(cls):
        session = Session.from_spec({
            'chromedriver_version': '',
            'executor_url':         '',
            'session_id':           ''
        })
        with open(SESSION_FILE, 'w') as fp:
            json.dump(attr.asdict(session), fp)

    @classmethod
    def from_spec(cls, spec):
        return Session(executor_url=spec['executor_url'], session_id=spec['session_id'],
                       chromedriver_version=spec['chromedriver_version'])

    @classmethod
    def from_file(cls):
        if not os.path.exists(SESSION_FILE):
            Session.init()
        with open(SESSION_FILE) as f:
            session_data = json.load(f)
        return Session.from_spec(session_data)

    def close(self):
        with open(SESSION_FILE, 'w') as fp:
            json.dump(attr.asdict(self), fp)
