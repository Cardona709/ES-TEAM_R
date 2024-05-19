from typing import List, Self, Tuple

import polars as pl
import psycopg as pg


class PostgresConfig:
    user: str
    password: str
    host: str
    port: str
    db_name: str
    schema_name: str
    connect_timeout_ms: int
    connection_retries: int

    def __init__(
        self,
        user: str,
        password: str,
        host: str,
        port: str,
        db_name: str,
        schema_name: str,
        connect_timeout_ms: int = 5000,
        connection_retries: int = 3,
    ):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.db_name = db_name
        self.schema_name = schema_name
        self.connect_timeout_ms = connect_timeout_ms
        self.connection_retries = connection_retries


#### Data classes to model the data ####


class CarbonData:
    utc_timestamp: str = ""
    grams_per_kw: float = 0

    def set_attributes(self, utc_timestamp: str, grams_per_kw: float) -> Self:
        self.utc_timestamp = utc_timestamp
        self.grams_per_kw = grams_per_kw
        return self

    def load_from_row(self, row: Tuple[str, float]) -> Self:
        self.utc_timestamp = parse_datetime(row[0])
        self.grams_per_kw = row[1]
        return self

    def insert_into_db(self, conn: pg.Connection):
        if self.utc_timestamp == "":
            raise ValueError("timestamp is empty")
        if self.grams_per_kw is None:
            raise ValueError("grams_per_kw is None")

        res = conn.execute(
            """
                INSERT INTO carbon_data (datetime, grams_per_kw)
                VALUES (%s, %s)
                """,
            [self.utc_timestamp, self.grams_per_kw],
        )


    def __repr__(self):
        return f"UTC Timestamp: {self.utc_timestamp}, Grams per KW: {self.grams_per_kw}"


class EnergyUsage:
    utc_timestamp: str
    location: str
    energy_usage: float

    def init(self, location: str, timestamp: str, energy_usage: float) -> Self:
        self.location = location
        self.utc_timestamp = parse_datetime(timestamp)
        self.energy_usage = energy_usage
        return self

    def __repr__(self):
        return f"UTC Timestamp: {self.utc_timestamp}, Location: {self.location}, Energy Usage (KW): {self.energy_usage}"

class GasConsumption:
    timestamp: str
    location: str
    gas_consumption: float

    #def init(self, location: str, time: str, gas_usage: float) -> Self:
    def init(self, location:str, timestamp: str, gas_consumption: float) -> Self:
        self.location = location
        self.timestamp = parse_datetime(timestamp)
        self.gas_consumption = gas_consumption
        return self

    def __repr__(self):
        return f"Timestamp: {self.timestamp}, Location: {self.location}, Gas Consumption (KW): {self.gas_usage}"

def parse_datetime(datetime: str) -> str:
    if datetime == "" or datetime is None:
        return ""
    date, time = datetime.split(" ")
    day, month, year = date.split("/")
    return f"{year}-{month}-{day} {time}"


def process_data(
    carbon_df: pl.DataFrame, energy_df: pl.DataFrame, gas_df: pl.DataFrame
) -> Tuple[List[CarbonData], List[EnergyUsage], List[str]]:
    locations_energy = energy_df.columns[2:]
    carbon_data = [CarbonData().load_from_row(row) for row in carbon_df.rows()]
    energy_data = [
        EnergyUsage().init(location, row[0], row[idx + 2])
        for row in energy_df.rows()
        for idx, location in enumerate(locations_energy)
    ]
    locations_gas = gas_df.columns[2:]
    gas_data = [
        GasConsumption().init(location, row[0], row[idx + 2])
        for row in gas_df.rows()
        for idx, location in enumerate(locations_gas)
    ]
    
    locations = list(set(locations_energy + locations_gas))
    return carbon_data, energy_data, gas_data, locations
