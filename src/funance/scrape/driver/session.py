import typing as t
import json
import os
import dataclasses as dc


@dc.dataclass
class SessionData:
    """Holds session data"""
    session_id: str = None
    executor_url: str = None
    # TODO set chromedriver version a different way. It's not relevant to the session
    chromedriver_version: str = None


class Session:
    """Manages a session file and data for a ChromeDriver session"""
    session_filename = 'session.json'

    def __init__(self, session_file: t.Union[str, bytes, os.PathLike], session_data: dict):
        self._session_file = session_file
        self.session = SessionData(**session_data)

    def close(self):
        """Write the session file"""
        with open(self._session_file, 'w') as fp:
            json.dump(dc.asdict(self.session), fp)

    @classmethod
    def from_file(cls, save_path: t.Union[str, bytes, os.PathLike]):
        """Create a session instance from file"""
        session_file = os.path.join(save_path, cls.session_filename)

        try:
            with open(session_file) as f:
                session_data = json.load(f)
        except FileNotFoundError as e:
            session_data = dc.asdict(SessionData())
        return Session(session_file, session_data)
