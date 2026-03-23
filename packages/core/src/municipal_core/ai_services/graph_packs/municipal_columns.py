from __future__ import annotations

import pandas as pd

from .base import find_col


def detect_municipal_columns(df: pd.DataFrame) -> dict[str, str | None]:
    crop_col = find_col(df, ["cultivation", "crop", "καλλιεργ", "καλλιέργ", "ειδοσ", "είδος", "προϊον", "προϊόν"])
    area_col = find_col(df, ["area", "strem", "στρεμ", "στρέμ", "σ τ ρ ε μ", "εκταση", "έκταση", "εμβαδ", "εμβαδό"])
    water_col = find_col(df, ["water", "volume", "καταναλ", "κατανάλ", "ποσοτητ", "ποσότητ", "ογκο", "όγκο", "m3", "m^3"])
    payment_col = find_col(df, ["payment", "price", "revenue", "τιμη", "τιμή", "κοστο", "κόστος", "εσοδ", "έσοδ", "ευρω", "€"])
    region_col = find_col(
        df,
        [
            "region",
            "prefecture",
            "municip",
            "county",
            "district",
            "area_name",
            "town",
            "village",
            "περιοχ",
            "δημοσ",
            "δήμοσ",
            "δημος",
            "δήμος",
            "κοινοτ",
            "κοινότητ",
            "περιφερ",
        ],
    )
    pump_col = find_col(df, ["pump", "αντλ", "αντλία", "γεωτρη", "γεώτρη", "pump_id", "id αντλ"])
    lat_col = find_col(df, ["lat", "latitude", "πλατ", "πλάτ", "γεωγραφ", "γεωγρ", "y_coord", "y coordinate"])
    lon_col = find_col(df, ["lon", "lng", "long", "longitude", "μηκ", "μήκ", "x_coord", "x coordinate"])
    year_col = find_col(df, ["__upload_year", "year", "ετος", "έτος"])

    return {
        "crop_col": crop_col,
        "area_col": area_col,
        "water_col": water_col,
        "payment_col": payment_col,
        "region_col": region_col,
        "pump_col": pump_col,
        "lat_col": lat_col,
        "lon_col": lon_col,
        "year_col": year_col,
    }

