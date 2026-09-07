import json
import sqlite3
import os
from typing import List, Dict, Any

def ingest_sqlite(db_path: str, table_name: str) -> List[Dict[str, Any]]:
    """
    Reads data from a SQLite table and converts each row into a text chunk with metadata.
    """
    chunks = []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # to get dict-like rows
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        for row in rows:
            row_dict = dict(row)
            # Create a string representation for the chunk text
            # Depending on use case, this could be customized to only include specific fields
            text_content = json.dumps(row_dict, ensure_ascii=False)
            
            chunk = {
                "text": text_content,
                "metadata": {
                    "source": f"sqlite_{table_name}",
                    "id": row_dict.get("id", None)
                }
            }
            chunks.append(chunk)
            
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            
    return chunks

def ingest_json(json_path: str) -> List[Dict[str, Any]]:
    """
    Reads data from a JSON file and converts it into text chunks with metadata.
    """
    chunks = []
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if isinstance(data, list):
            for idx, item in enumerate(data):
                text_content = json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else str(item)
                
                chunk = {
                    "text": text_content,
                    "metadata": {
                        "source": os.path.basename(json_path),
                        "id": item.get("id", idx) if isinstance(item, dict) else idx
                    }
                }
                chunks.append(chunk)
                
        elif isinstance(data, dict):
            for key, value in data.items():
                text_content = f"{key}: {json.dumps(value, ensure_ascii=False)}"
                
                chunk = {
                    "text": text_content,
                    "metadata": {
                        "source": os.path.basename(json_path),
                        "id": key
                    }
                }
                chunks.append(chunk)
        else:
            print(f"Unsupported JSON structure in {json_path}")
            
    except Exception as e:
        print(f"Error reading JSON: {e}")
        
    return chunks

def get_all_chunks(db_configs: List[Dict[str, str]] = None, json_files: List[str] = None) -> List[Dict[str, Any]]:
    """
    Master function to get all chunks from both SQLite and JSON files.
    db_configs: [{"db_path": "path/to.db", "table_name": "my_table"}]
    json_files: ["path/to.json"]
    """
    all_chunks = []
    
    if db_configs:
        for config in db_configs:
            db_path = config.get("db_path")
            table = config.get("table_name")
            if db_path and table and os.path.exists(db_path):
                print(f"Ingesting SQLite: {db_path} -> {table}")
                all_chunks.extend(ingest_sqlite(db_path, table))
            else:
                print(f"Invalid DB config or file not found: {config}")
                
    if json_files:
        for json_path in json_files:
            if os.path.exists(json_path):
                print(f"Ingesting JSON: {json_path}")
                all_chunks.extend(ingest_json(json_path))
            else:
                print(f"JSON file not found: {json_path}")
                
    return all_chunks

def save_chunks_to_file(chunks: List[Dict[str, Any]], output_path: str):
    """
    Saves the generated text chunks to a JSON file so that build_index.py can process them.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(chunks)} chunks to {output_path}")

if __name__ == "__main__":
    # Example usage:
    # Please update the paths to match your actual files
    db_configs = [{"db_path": "../../pantry.db", "table_name": "recipes"}] # Update path
    json_files = ["../../ingredients.json"] # Update path
    
    # chunks = get_all_chunks(db_configs=db_configs, json_files=json_files)
    # if chunks:
    #    save_chunks_to_file(chunks, "../../data/processed/my_db_chunks.json")
    pass
