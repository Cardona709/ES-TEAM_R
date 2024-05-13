import random
import string
import time
from typing import List

import psycopg as pg
from Database.data_classes import CarbonData, EnergyUsage, GasConsumption, PostgresConfig

#### Database initialization ####


def connect(config: PostgresConfig) -> pg.Connection:
    for _ in range(config.connection_retries):
        try:
            con = pg.connect(
                dbname=config.db_name,
                user=config.user,
                password=config.password,
                host=config.host,
                port=config.port,
            )
            return con
        except Exception as e:
            print(f"[DB] Connection failed: {e}")
            print(f"[DB] Retrying in {config.connect_timeout_ms}ms...")
            time.sleep(config.connect_timeout_ms / 1000)

    raise Exception("[DB] Failed to connect to database")


def generate_random_schema_name() -> str:
    random_alphanum = "".join(random.choice(string.ascii_lowercase) for _ in range(8))
    return f"temp_{random_alphanum}"


def create_schema(conn: pg.Connection, schema_name: str):
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}".encode("utf-8"))


def set_schema(conn: pg.Connection, schema_name: str):
    conn.execute(f"SET search_path TO {schema_name}".encode("utf-8"))


def drop_schema(conn: pg.Connection, schema_name: str):
    conn.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE".encode("utf-8"))


def test_init_query(conn: pg.Connection, query: bytes):
    temp_schema = generate_random_schema_name()

    create_schema(conn, temp_schema)
    set_schema(conn, temp_schema)

    try:
        conn.execute(query)
    finally:
        drop_schema(conn, temp_schema)


def init_db(
    conn: pg.Connection,
    schema_name: str,
    init_file_path: str,
) -> bool:
    with open(init_file_path, "r") as f:
        sql_commands = f.read()
        init_commands = sql_commands.encode("utf-8")
        try:
            test_init_query(conn, init_commands)
        except Exception as e:
            print(f"[DB] Schema failed: {e}")
            return False

        print("[DB] Schema test passed. Initializing database...")
        create_schema(conn, schema_name)
        set_schema(conn, schema_name)
        conn.execute(init_commands)
        conn.commit()
        print("[DB] Schema created")
        return True


def upload_data(
    conn: pg.Connection,
    carbon_data: List[CarbonData],
    energy_data: List[EnergyUsage],
    gas_data: List[GasConsumption],
    locations: List[str],
):
    try:
        print("[DB] Uploading data...")
        for carbon in carbon_data:
            carbon.insert_into_db(conn)

        print("[DB] Carbon data uploaded")

        loc_id_map = {}
        for location in locations:
            cur = conn.cursor()
            cur.execute(
                """
                    INSERT INTO locations (name)
                    VALUES (%s)
                    RETURNING id
                    """,
                [location],
            )
            res = cur.fetchone()
            if res:
                id = res[0]
                loc_id_map[location] = id
        print("[DB] Locations uploaded")

        for energy in energy_data:
            conn.execute(
                """
                    INSERT INTO energy_usage (datetime, location_id, kw)
                    VALUES (%s, %s, %s)
                    """,
                [
                    energy.utc_timestamp,
                    loc_id_map[energy.location],
                    energy.energy_usage,
                ],
            )
        print("[DB] Energy usage uploaded")
        
        for gas in gas_data:
            conn.execute(
                """
                    INSERT INTO gas_consumption (time, location_id, kw)
                    VALUES (%s, %s, %s)
                    """,
                [
                    gas.time,
                    loc_id_map[gas.location],
                    gas.gas_consumption,
                ],
            )
        print("[DB] Gas consumption uploaded")
    except Exception as e:
        print(f"[DB] Data upload failed: {e}")
        conn.rollback()
        return

    finally:
        conn.commit()
        print("[DB] Data upload complete - database initialized!")
