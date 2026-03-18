"""
Report Data Manager

This service manages the storage and retrieval of agent data for report generation.
It captures the structured data from all agents in a normalized format for easy report access.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict

from app.core.config import DATA_DIR


@dataclass
class ReportDataEntry:
    """Structured entry for report data storage."""
    session_id: str
    prompt_id: str
    drug_name: str
    indication: str
    timestamp: str
    iqvia_data: Dict[str, Any]
    clinical_data: Dict[str, Any] 
    patent_data: Dict[str, Any]
    exim_data: Dict[str, Any]
    internal_knowledge_data: Dict[str, Any]
    web_intelligence_data: Dict[str, Any]
    
    
class ReportDataManager:
    """Manages report data storage and retrieval."""
    
    def __init__(self):
        self.data_dir = Path(DATA_DIR)
        self.report_data_file = self.data_dir / "report_data_cache.json"
        self.ensure_data_dir()
        
    def ensure_data_dir(self):
        """Ensure data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)
        
    def store_report_data(
        self,
        session_id: str,
        prompt_id: str,
        drug_name: str,
        indication: str,
        agents_data: Dict[str, Any]
    ) -> str:
        """
        Store agent data in structured format for report generation.
        
        Args:
            session_id: MongoDB session ID
            prompt_id: Unique prompt identifier
            drug_name: Drug/molecule name
            indication: Medical indication
            agents_data: Dictionary containing all agent results
            
        Returns:
            Storage key for retrieval
        """
        try:
            # Create structured entry
            entry = ReportDataEntry(
                session_id=session_id,
                prompt_id=prompt_id,
                drug_name=drug_name or "Unknown Drug",
                indication=indication or "Unknown Indication",
                timestamp=datetime.utcnow().isoformat(),
                iqvia_data=agents_data.get("iqvia", {}),
                clinical_data=agents_data.get("clinical", {}),
                patent_data=agents_data.get("patent", {}),
                exim_data=agents_data.get("exim", {}),
                internal_knowledge_data=agents_data.get("internal_knowledge", {}),
                web_intelligence_data=agents_data.get("web_intelligence", {})
            )
            
            # Load existing data
            existing_data = self._load_existing_data()
            
            # Store with prompt_id as key
            existing_data[prompt_id] = asdict(entry)
            
            # Save to file
            with open(self.report_data_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
            print(f"[REPORT_DATA_MANAGER] Stored data for prompt_id: {prompt_id}")
            return prompt_id
            
        except Exception as e:
            print(f"[REPORT_DATA_MANAGER] Error storing data: {e}")
            return None
            
    def get_report_data(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored report data by prompt ID.
        
        Args:
            prompt_id: Unique prompt identifier
            
        Returns:
            Structured agent data or None if not found
        """
        try:
            existing_data = self._load_existing_data()
            return existing_data.get(prompt_id)
            
        except Exception as e:
            print(f"[REPORT_DATA_MANAGER] Error retrieving data: {e}")
            return None
            
    def get_formatted_agents_data(self, prompt_id: str) -> Dict[str, Any]:
        """
        Get agents data in the format expected by report generator.
        
        Args:
            prompt_id: Unique prompt identifier
            
        Returns:
            Dictionary with agent data ready for report generation
        """
        entry = self.get_report_data(prompt_id)
        if not entry:
            return {}
            
        return {
            "iqvia": entry.get("iqvia_data", {}),
            "clinical": entry.get("clinical_data", {}),
            "patent": entry.get("patent_data", {}),
            "exim": entry.get("exim_data", {}),
            "internal_knowledge": entry.get("internal_knowledge_data", {}),
            "web_intelligence": entry.get("web_intelligence_data", {})
        }
        
    def list_reports(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available reports, optionally filtered by session.
        
        Args:
            session_id: Optional session filter
            
        Returns:
            List of report metadata
        """
        try:
            existing_data = self._load_existing_data()
            reports = []
            
            for prompt_id, entry in existing_data.items():
                if session_id is None or entry.get("session_id") == session_id:
                    reports.append({
                        "prompt_id": prompt_id,
                        "session_id": entry.get("session_id"),
                        "drug_name": entry.get("drug_name"),
                        "indication": entry.get("indication"),
                        "timestamp": entry.get("timestamp"),
                        "has_data": {
                            "iqvia": bool(entry.get("iqvia_data")),
                            "clinical": bool(entry.get("clinical_data")),
                            "patent": bool(entry.get("patent_data")),
                            "exim": bool(entry.get("exim_data")),
                            "internal_knowledge": bool(entry.get("internal_knowledge_data")),
                            "web_intelligence": bool(entry.get("web_intelligence_data"))
                        }
                    })
            
            # Sort by timestamp (newest first)
            reports.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return reports
            
        except Exception as e:
            print(f"[REPORT_DATA_MANAGER] Error listing reports: {e}")
            return []
            
    def _load_existing_data(self) -> Dict[str, Any]:
        """Load existing data from file."""
        try:
            if self.report_data_file.exists():
                with open(self.report_data_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[REPORT_DATA_MANAGER] Error loading data: {e}")
        
        return {}
        
    def cleanup_old_entries(self, max_age_days: int = 30):
        """
        Clean up entries older than specified days.
        
        Args:
            max_age_days: Maximum age in days to keep entries
        """
        try:
            existing_data = self._load_existing_data()
            cutoff_time = datetime.utcnow().timestamp() - (max_age_days * 24 * 3600)
            
            cleaned_data = {}
            removed_count = 0
            
            for prompt_id, entry in existing_data.items():
                try:
                    entry_time = datetime.fromisoformat(entry.get("timestamp", "")).timestamp()
                    if entry_time >= cutoff_time:
                        cleaned_data[prompt_id] = entry
                    else:
                        removed_count += 1
                except:
                    # Keep entries with invalid timestamps
                    cleaned_data[prompt_id] = entry
                    
            if removed_count > 0:
                with open(self.report_data_file, 'w') as f:
                    json.dump(cleaned_data, f, indent=2)
                print(f"[REPORT_DATA_MANAGER] Cleaned up {removed_count} old entries")
                
        except Exception as e:
            print(f"[REPORT_DATA_MANAGER] Error during cleanup: {e}")


# Global instance for easy access
report_data_manager = ReportDataManager()