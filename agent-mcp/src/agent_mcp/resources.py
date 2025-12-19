from typing import Dict
from agent_mcp.video.ingestion.models import CachedTable , CachedTableMetadata
from agent_mcp.video.ingestion.registry import get_registry


def list_tables() -> Dict[str,str]:
    keys = list(get_registry().keys())
    if not keys:
        return None
    
    response = {
        "message": "current processed videos",
        "indexes": keys,
    }
    return response

def table_info(table_name:str)->str:
    registry = get_registry()
    if table_name not in registry:
        return f"Video Index '{table_name}' does not exist"
    table_metadata = registry[table_name]
    table_info = CachedTableMetadata(**table_metadata)
    table = CachedTable.from_metadata(table_info)
    response = table.describe()
    return response
