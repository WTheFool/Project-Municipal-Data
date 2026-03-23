from typing import List, Dict, Callable
import pandas as pd
from municipal_core.standardize.typing_engine import Variable, VariableType

class Indicator:
    """
    Represents a computed indicator.
    """
    def __init__(self, name: str, formula: Callable[[pd.DataFrame], pd.Series], description: str = ""):
        self.name = name
        self.formula = formula
        self.description = description

    def compute(self, df: pd.DataFrame) -> pd.Series:
        """
        Compute the indicator based on the DataFrame.
        """
        try:
            result = self.formula(df)
            return result
        except Exception as e:
            raise ValueError(f"Error computing indicator '{self.name}': {e}")


class IndicatorEngine:
    """
    Engine to dynamically compute indicators based on typed variables.
    """
    def __init__(self, indicators: List[Indicator] = None):
        self.indicators = indicators or []

    def register_indicator(self, indicator: Indicator):
        self.indicators.append(indicator)

    def compute_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes all registered indicators and returns a DataFrame with new columns.
        """
        results = pd.DataFrame(index=df.index)
        for ind in self.indicators:
            results[ind.name] = ind.compute(df)
        return results

    @staticmethod
    def create_default_irrigation_indicators(variables: List[Variable]) -> List[Indicator]:
        """
        Generate default indicators for municipal irrigation dataset.
        """
        var_names = {v.var_type: v.name for v in variables}

        indicators = []

        # Water Intensity = water_volume / area
        if VariableType.RESOURCE in var_names and VariableType.AREA in var_names:
            indicators.append(
                Indicator(
                    name="water_intensity",
                    formula=lambda df: df[var_names[VariableType.RESOURCE]] / df[var_names[VariableType.AREA]],
                    description="Water usage per stremma"
                )
            )

        # Water Productivity = (payment) / water_volume
        if VariableType.ECONOMIC in var_names and VariableType.RESOURCE in var_names:
            indicators.append(
                Indicator(
                    name="water_productivity",
                    formula=lambda df: df[var_names[VariableType.ECONOMIC]] / df[var_names[VariableType.RESOURCE]],
                    description="Economic value generated per cubic meter of water"
                )
            )

        # Revenue per Area = payment / area
        if VariableType.ECONOMIC in var_names and VariableType.AREA in var_names:
            indicators.append(
                Indicator(
                    name="revenue_per_area",
                    formula=lambda df: df[var_names[VariableType.ECONOMIC]] / df[var_names[VariableType.AREA]],
                    description="Revenue generated per stremma"
                )
            )

        # Pump Load = total water per pump
        if VariableType.RESOURCE in var_names and VariableType.CATEGORICAL in var_names:
            pump_col = next((v.name for v in variables if v.name.lower() == "pump"), None)
            if pump_col:
                indicators.append(
                    Indicator(
                        name="pump_load",
                        formula=lambda df: df.groupby(pump_col)[var_names[VariableType.RESOURCE]] \
                                           .transform("sum"),
                        description="Total water pumped per pump"
                    )
                )

        # Crop Water Consumption = avg water per crop
        crop_col = next((v.name for v in variables if v.name.lower() == "crop"), None)
        if crop_col and VariableType.RESOURCE in var_names:
            indicators.append(
                Indicator(
                    name="crop_water_consumption",
                    formula=lambda df: df.groupby(crop_col)[var_names[VariableType.RESOURCE]] \
                                           .transform("mean"),
                    description="Average water consumption per crop type"
                )
            )

        return indicators