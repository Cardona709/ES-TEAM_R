import random
import string
import time
from os.path import dirname, join, realpath
from typing import List, Self, Tuple

import polars as pl
import psycopg as pg

#### Data classes to model the data ####


class CarbonData:
    utc_timestamp: str
    grams_per_kw: float

    def load_from_row(self, row: Tuple[str, float]) -> Self:
        self.utc_timestamp = parse_datetime(row[0])
        self.grams_per_kw = row[1]
        return self

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


def parse_datetime(datetime: str) -> str:
    date, time = datetime.split(" ")
    day, month, year = date.split("/")
    return f"{year}-{month}-{day} {time}"


def process_data(
    carbon_df: pl.DataFrame, energy_df: pl.DataFrame
) -> Tuple[List[CarbonData], List[EnergyUsage], List[str]]:
    locations = energy_df.columns[2:]
    carbon_data = [CarbonData().load_from_row(row) for row in carbon_df.rows()]
    energy_data = [
        EnergyUsage().init(location, row[0], row[idx + 2])
        for row in energy_df.rows()
        for idx, location in enumerate(locations)
    ]
    return carbon_data, energy_data, locations


#### Database initialization ####

PASSWORD = "postgrespw"
DB = "carbono_feup"
USER = "postgres"
HOST = "postgres"
PORT = "5432"

DB_INIT_FILE_PATH = realpath(join(dirname(realpath(__file__)), "tables.sql"))


def connect(max_retries: int = 5, timeout_ms: int = 1000) -> pg.Connection:
    for _ in range(max_retries):
        try:
            con = pg.connect(
                dbname=DB,
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
            )
            return con
        except Exception as e:
            print(f"Connection failed: {e}")
            print(f"Retrying in {timeout_ms}ms...")
            time.sleep(timeout_ms / 1000)

    raise Exception("Failed to connect to database")


def generate_random_schema_name() -> str:
    random_alphanum = "".join(random.choice(string.ascii_lowercase) for _ in range(8))
    return f"temp_{random_alphanum}"


def create_schema(conn: pg.Connection, schema_name: str):
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}".encode("utf-8"))


def set_schema(conn: pg.Connection, schema_name: str):
    conn.execute(f"SET search_path TO {schema_name}".encode("utf-8"))


def drop_schema(conn: pg.Connection, schema_name: str):
    conn.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE".encode("utf-8"))


def test_init_query(query: bytes):
    conn = connect()
    conn.autocommit = True

    temp_schema = generate_random_schema_name()

    create_schema(conn, temp_schema)
    conn.close()
    conn = connect()
    set_schema(conn, temp_schema)

    try:
        conn.execute(query)
        conn.close()
    finally:
        conn = connect()
        drop_schema(conn, temp_schema)
        conn.close()


def init_db(
    schema: str,
    carbon_data: List[CarbonData],
    energy_data: List[EnergyUsage],
    locations: List[str],
):
    with open(DB_INIT_FILE_PATH, "r") as f:
        sql_commands = f.read()
    init_commands = sql_commands.encode("utf-8")
    test_init_query(init_commands)
    conn = connect()
    con.autocommit = False

    print("Schema test passed. Initializing database...")
    create_schema(conn, schema)
    set_schema(conn, schema)
    conn.execute(init_commands)
    print("Schema created")

    try:
        print("Uploading data...")
        for carbon in carbon_data:
            conn.execute(
                "INSERT INTO carbon_data (datetime, grams_per_kw) VALUES (%s, %s)",
                [carbon.utc_timestamp, carbon.grams_per_kw],
            )

        print("Carbon data uploaded")

        loc_id_map = {}
        for location in locations:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO locations (name) VALUES (%s) RETURNING id",
                [location],
            )
            res = cur.fetchone()
            if res:
                id = res[0]
                loc_id_map[location] = id

        print("Locations uploaded")

        for energy in energy_data:
            conn.execute(
                "INSERT INTO energy_usage (datetime, location_id, kw) VALUES (%s, %s, %s)",
                [
                    energy.utc_timestamp,
                    loc_id_map[energy.location],
                    energy.energy_usage,
                ],
            )

        print("Energy usage uploaded")

    finally:
        conn.commit()
        conn.close()


if __name__ == "__main__":
    print("Connecting to database...")
    con = connect()
    print("Connected to database")

    carbon_df = pl.read_csv("data/Dados_Carbono_CSV.csv")
    energy_df = pl.read_csv("data/Dados_Janeiro_Horario_CSV.csv")

    carbon_data, energy_data, locations = process_data(carbon_df, energy_df)

    print("Data loaded. Uploading to database...")

    init_db("carbono_feup", carbon_data, energy_data, locations)
