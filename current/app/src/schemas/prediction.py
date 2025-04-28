"""
Module: schemas.prediction

Contains Pydantic models for prediction requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Any, List, Dict


class PredictionRequest(BaseModel):
    """
    Schema for submitting data to ML prediction endpoint.

    Attributes:
      data: list of records, each record is a dict mapping feature names to values
    """
    data : List[Dict[str, Any]] = Field(..., description="List of records, each record is a dict mapping feature names to values")


class PredictionResponse(BaseModel):
    """
    Schema for returning ML prediction results.

    Attributes:
      predictions: list of predicted values (Any)
      credits_spent: float amount of credits charged
    """
    predictions : List[Any] = Field(..., description="List of predicted values")
    credits_spent : float = Field(..., description="Amount of credits charged")


class DataValidationError(BaseModel):
    """
    Schema for reporting validation errors in input data.

    Attributes:
      invalid_rows: list of indices or records that failed validation
      errors: list of error messages corresponding to invalid rows
    """
    invalid_rows : List[int] = Field(..., description= "List of indices or records that failed validation")
    errors: List[str] = Field(..., description= "List of error messages corresponding to invalid rows") 
    