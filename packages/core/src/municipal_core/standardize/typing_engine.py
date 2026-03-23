from enum import Enum
from typing import List, Optional
import pandas as pd


class VariableType(str, Enum):
    RESOURCE = "resource"
    AREA = "area"
    ECONOMIC = "economic"
    TEMPORAL = "temporal"
    CATEGORICAL = "categorical"
    OTHER = "other"


class Variable:
    """Represents a dataset variable with type and metadata."""

    def __init__(self, name: str, dtype: str, description: Optional[str] = None):
        self.name = name
        self.dtype = dtype
        self.description = description
        self.var_type: VariableType = VariableType.OTHER

    def set_type(self, var_type: VariableType):
        self.var_type = var_type

    def to_dict(self):
        return {
            "name": self.name,
            "dtype": self.dtype,
            "description": self.description,
            "var_type": self.var_type.value,
        }


class TypingEngine:
    """Engine to classify variables in a DataFrame."""

    def __init__(self, rules: Optional[dict] = None):
        """
        rules: Optional dict mapping column patterns or names to VariableType.
        Example:
        {
            "area": "AREA",
            "water_volume": "RESOURCE",
            "payment": "ECONOMIC"
        }
        """
        self.rules = rules or {}

    def infer_variables(self, df: pd.DataFrame) -> List[Variable]:
        variables = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            var = Variable(name=col, dtype=dtype)
            var_type = self._infer_type(col, dtype)
            var.set_type(var_type)
            variables.append(var)
        return variables

    def _infer_type(self, col_name: str, dtype: str) -> VariableType:
        # Check user-defined rules first
        for pattern, vtype_str in self.rules.items():
            if pattern.lower() in col_name.lower():
                return VariableType(vtype_str)

        # Basic heuristics
        if "area" in col_name.lower():
            return VariableType.AREA
        elif "water" in col_name.lower() or "volume" in col_name.lower():
            return VariableType.RESOURCE
        elif "price" in col_name.lower() or "payment" in col_name.lower():
            return VariableType.ECONOMIC
        elif "date" in col_name.lower() or "time" in col_name.lower():
            return VariableType.TEMPORAL
        elif dtype in ["object", "string"]:
            return VariableType.CATEGORICAL
        else:
            return VariableType.OTHER