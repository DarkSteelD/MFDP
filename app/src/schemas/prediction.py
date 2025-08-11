"""
Module: schemas.prediction

Contains Pydantic models for prediction requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class PredictionRequest(BaseModel):
    """
    Schema for submitting data to ML prediction endpoint.

    Attributes:
      image (str): base64-encoded image input for prediction.
    """
    image: str = Field(
        ..., description="Image input for prediction (base64-encoded string)"
    )


class PredictionResponse(BaseModel):
    """
    Schema for returning ML prediction results.

    Attributes:
      image_prediction (Optional[str]): image output from the prediction model (base64 or URL).
      credits_spent (float): amount of credits charged for this prediction.
    """
    image_prediction: Optional[str] = Field(
        None, description="Image output from the prediction model (base64 or URL)"
    )
    credits_spent : float = Field(..., description="Amount of credits charged")


class Scan3DRequest(BaseModel):
    """
    Schema for submitting 3D scan data for analysis.
    
    Attributes:
      scan_filename (str): name of the uploaded scan file
    """
    scan_filename: str = Field(..., description="Name of the uploaded scan file")


class Scan3DResponse(BaseModel):
    """
    Schema for returning 3D scan analysis results.
    
    Attributes:
      brain_mask_url (str): URL to download the brain mask
      aneurysm_mask_url (str): URL to download the aneurysm mask
      original_scan_url (str): URL to access the original scan
      credits_spent (float): amount of credits charged for this analysis
    """
    brain_mask_url: str = Field(..., description="URL to download the brain mask")
    aneurysm_mask_url: str = Field(..., description="URL to download the aneurysm mask")
    original_scan_url: str = Field(..., description="URL to access the original scan")
    credits_spent: float = Field(..., description="Amount of credits charged")


class DataValidationError(BaseModel):
    """
    Schema for reporting validation errors in input data.

    Attributes:
      invalid_rows: list of indices or records that failed validation
      errors: list of error messages corresponding to invalid rows
    """
    invalid_rows : List[int] = Field(..., description= "List of indices or records that failed validation")
    errors: List[str] = Field(..., description= "List of error messages corresponding to invalid rows") 
    