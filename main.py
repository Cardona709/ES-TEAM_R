import time
from os.path import dirname, join, realpath

import Database.db_ops as db
import polars as pl
from Database.data_classes import process_data
from WebScrapping.get_carbon import get_carbon

# url of the page we want to scrape
URL = "https://app.electricitymaps.com/zone/PT"

PASSWORD = "postgrespw"
DB = "carbono_feup"
USER = "postgres"
HOST = "postgres"
PORT = "5432"

DB_INIT_FILE_PATH = realpath(
    join(dirname(realpath(__file__)), "Database", "tables.sql")
)


if __name__ == "__main__":
    print("[MAIN] Starting...")
    config = db.PostgresConfig(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        db_name=DB,
        schema_name="carbono_feup",
        connect_timeout_ms=1000,
        connection_retries=5,
    )

    conn = db.connect(config)

    carbon_df = pl.read_csv("data/Dados_Carbono_CSV.csv")
    energy_df = pl.read_csv("data/Dados_Janeiro_Horario_CSV.csv")
    gas_df = pl.read_csv("data/Dados_Gas_CSV.csv")

    carbon_data, energy_data, gas_data, locations = process_data(carbon_df, energy_df, gas_df)

    # TODO: custom exception handling
    if db.init_db(conn, config.schema_name, DB_INIT_FILE_PATH) is False:
        print("[MAIN] Failed to initialize database")
        exit(1)

    try:
        db.upload_data(conn, carbon_data, energy_data, gas_data, locations)
    except Exception as e:
        print(f"[MAIN] Failed to upload data: {e}")

    try:
        while True:
            print("[MAIN] Scraping data...")
            carbon = get_carbon(URL)
            date = time.strftime("%Y-%m-%d %H:%M")
            
            print(
                "[MAIN] Carbon emmission",
                carbon,
                "gCO2eq/kWh at day",
                date,
            )

            carbon_data = db.CarbonData().set_attributes(date, carbon)
            carbon_data.insert_into_db(conn)
            conn.commit()

            print("[MAIN] Data uploaded successfully")
            print("[MAIN] Sleeping for 1 hour...")
            time.sleep(3600)
    finally:
        conn.close()
