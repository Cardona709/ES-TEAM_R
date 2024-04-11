from typing import List, Self, Tuple
import polars as pl

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
