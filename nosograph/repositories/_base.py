from neo4j import Driver


class BaseRepository:
    def __init__(self, driver: Driver) -> None:
        self._driver = driver
