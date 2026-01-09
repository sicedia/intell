"""
Script to analyze Excel files used for patent algorithms.
This script examines all sheets, columns, and data types to understand
the structure of the input data.
"""
import pandas as pd
from pathlib import Path
import json

def analyze_excel(file_path: str) -> dict:
    """
    Analyze an Excel file and return detailed information about its structure.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        Dictionary with analysis results
    """
    print(f"\n{'='*80}")
    print(f"ANALYZING: {file_path}")
    print(f"{'='*80}\n")
    
    # Load all sheets
    xlsx = pd.ExcelFile(file_path)
    sheet_names = xlsx.sheet_names
    
    result = {
        'file_path': str(file_path),
        'sheet_count': len(sheet_names),
        'sheets': {}
    }
    
    print(f"Total sheets found: {len(sheet_names)}")
    print(f"Sheet names: {sheet_names}\n")
    
    for sheet_name in sheet_names:
        print(f"\n{'-'*60}")
        print(f"SHEET: '{sheet_name}'")
        print(f"{'-'*60}")
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        sheet_info = {
            'name': sheet_name,
            'rows': len(df),
            'columns': list(df.columns),
            'column_count': len(df.columns),
            'column_details': {},
            'sample_data': [],
            'potential_use': None
        }
        
        print(f"Rows: {len(df)}")
        print(f"Columns ({len(df.columns)}): {list(df.columns)}")
        
        # Analyze each column
        for col in df.columns:
            col_info = {
                'name': col,
                'dtype': str(df[col].dtype),
                'non_null_count': int(df[col].notna().sum()),
                'null_count': int(df[col].isna().sum()),
                'unique_values': int(df[col].nunique()),
                'sample_values': []
            }
            
            # Get sample values (first 5 non-null)
            sample = df[col].dropna().head(5).tolist()
            col_info['sample_values'] = [str(v) for v in sample]
            
            # Check if it looks like year data
            if df[col].dtype in ['int64', 'float64']:
                numeric_vals = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(numeric_vals) > 0:
                    col_info['min'] = float(numeric_vals.min())
                    col_info['max'] = float(numeric_vals.max())
                    col_info['mean'] = float(numeric_vals.mean())
                    
                    # Check if values look like years
                    if 1900 <= numeric_vals.min() <= 2100 and 1900 <= numeric_vals.max() <= 2100:
                        col_info['looks_like_year'] = True
            
            sheet_info['column_details'][col] = col_info
            
            print(f"\n  Column: '{col}'")
            print(f"    Type: {col_info['dtype']}")
            print(f"    Non-null: {col_info['non_null_count']}, Null: {col_info['null_count']}")
            print(f"    Unique values: {col_info['unique_values']}")
            print(f"    Sample: {col_info['sample_values'][:3]}")
            if 'min' in col_info:
                print(f"    Range: {col_info['min']} - {col_info['max']}")
            if col_info.get('looks_like_year'):
                print(f"    *** LOOKS LIKE YEAR DATA ***")
        
        # Show first few rows
        print(f"\n  First 5 rows:")
        print(df.head().to_string(index=False))
        
        # Store sample data
        sheet_info['sample_data'] = df.head(10).to_dict(orient='records')
        
        # Try to determine potential use
        col_names_lower = [str(c).lower() for c in df.columns]
        
        if any('year' in c or 'año' in c or 'date' in c or 'fecha' in c for c in col_names_lower):
            if len(df.columns) == 2:
                sheet_info['potential_use'] = 'YEAR_COUNT_DATA (evolution/cumulative charts)'
            else:
                sheet_info['potential_use'] = 'TIME_SERIES_DATA'
        elif any('applicant' in c or 'solicitante' in c for c in col_names_lower):
            sheet_info['potential_use'] = 'TOP_APPLICANTS'
        elif any('inventor' in c for c in col_names_lower):
            sheet_info['potential_use'] = 'TOP_INVENTORS'
        elif any('country' in c or 'país' in c for c in col_names_lower):
            sheet_info['potential_use'] = 'TOP_COUNTRIES'
        elif any('cpc' in c or 'ipc' in c for c in col_names_lower):
            sheet_info['potential_use'] = 'CPC_CLASSIFICATION'
        
        if sheet_info['potential_use']:
            print(f"\n  *** POTENTIAL USE: {sheet_info['potential_use']} ***")
        
        result['sheets'][sheet_name] = sheet_info
    
    return result


def main():
    """Main function to analyze all Excel files in the context/excels folder."""
    excels_folder = Path(__file__).parent.parent / 'context' / 'excels'
    
    if not excels_folder.exists():
        print(f"Error: Folder not found: {excels_folder}")
        return
    
    excel_files = list(excels_folder.glob('*.xlsx'))
    
    if not excel_files:
        print(f"No Excel files found in {excels_folder}")
        return
    
    print(f"Found {len(excel_files)} Excel file(s)")
    
    all_results = {}
    
    for excel_file in excel_files:
        result = analyze_excel(str(excel_file))
        all_results[excel_file.name] = result
    
    # Save analysis to JSON
    output_path = excels_folder / 'analysis_result.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n\n{'='*80}")
    print(f"Analysis complete! Results saved to: {output_path}")
    print(f"{'='*80}")
    
    # Summary
    print("\n\nSUMMARY OF SHEETS AND THEIR POTENTIAL USES:")
    print("-" * 60)
    for file_name, file_data in all_results.items():
        print(f"\nFile: {file_name}")
        for sheet_name, sheet_data in file_data['sheets'].items():
            use = sheet_data.get('potential_use', 'UNKNOWN')
            cols = sheet_data['columns']
            print(f"  - {sheet_name}: {use}")
            print(f"    Columns: {cols}")


if __name__ == '__main__':
    main()
