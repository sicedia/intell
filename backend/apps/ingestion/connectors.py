"""
Data source connectors for ingestion.
Supports Lens API (mock) and Espacenet Excel files.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
import json


class LensConnector:
    """
    Connector for Lens API.
    Currently implements mock for MVP, prepared for real API integration.
    """
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initialize Lens connector.
        
        Args:
            api_key: API key for Lens (not used in mock)
            base_url: Base URL for Lens API (not used in mock)
        """
        self.api_key = api_key
        self.base_url = base_url or "https://api.lens.org"
    
    def fetch(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data from Lens API.
        
        Currently returns mock data structured like Lens API response.
        In production, this would make actual HTTP requests.
        
        Args:
            query_params: Query parameters for Lens API
            
        Returns:
            Dictionary with structured data similar to Lens API response
        """
        # Mock response structure
        return {
            "data": [
                {
                    "lens_id": "12345678",
                    "title": "Sample Patent",
                    "abstract": "Sample abstract text",
                    "applicants": ["Company A", "Company B"],
                    "jurisdictions": ["US", "EP"],
                    "publication_date": "2024-01-01",
                }
            ],
            "total": 1,
            "query": query_params
        }
    
    def parse(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Lens API response into raw data format.
        
        Args:
            response: Response from Lens API
            
        Returns:
            List of dictionaries with normalized patent data
        """
        raw_data = []
        for item in response.get("data", []):
            raw_data.append({
                "lens_id": item.get("lens_id"),
                "title": item.get("title"),
                "abstract": item.get("abstract"),
                "applicants": item.get("applicants", []),
                "jurisdictions": item.get("jurisdictions", []),
                "publication_date": item.get("publication_date"),
            })
        return raw_data


class EspacenetExcelParser:
    """
    Parser for Espacenet Excel files.
    Reads Excel files and extracts patent data.
    """
    
    def __init__(self):
        """Initialize Excel parser."""
        pass
    
    def parse(self, file_path: str, sheet_name: str = "Countries (family)") -> List[Dict[str, Any]]:
        """
        Parse Excel file and return raw data.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of the sheet to read (default: "Countries (family)")
            
        Returns:
            List of dictionaries with patent data
        """
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {e}")
        
        # Convert DataFrame to list of dictionaries
        raw_data = df.to_dict('records')
        
        return raw_data
    
    def parse_multiple_sheets(self, file_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse all sheets from Excel file.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Dictionary mapping sheet names to data lists
        """
        try:
            excel_file = pd.ExcelFile(file_path)
            result = {}
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                result[sheet_name] = df.to_dict('records')
            return result
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {e}")

