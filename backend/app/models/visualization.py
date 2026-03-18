from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class VisualizationType(str, Enum):
    BAR = "bar"
    PIE = "pie"
    LINE = "line"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    TABLE = "table"
    CARD = "card"
    IMAGE = "image"


class TableColumn(BaseModel):
    key: str
    label: Optional[str] = None
    type: Optional[str] = None


class VizConfig(BaseModel):
    xField: Optional[str] = None
    yField: Optional[str] = None
    labelField: Optional[str] = None
    valueField: Optional[str] = None
    orientation: Optional[str] = "vertical"
    pageSize: Optional[int] = 15
    sortable: Optional[bool] = None
    colors: Optional[List[str]] = None
    legend: Optional[bool] = True
    tooltip: Optional[bool] = True


class Visualization(BaseModel):
    id: str
    vizType: VisualizationType
    title: str
    description: Optional[str] = None
    data: Any
    config: Optional[VizConfig] = VizConfig()
    source: Optional[str] = None
    promptId: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True


__all__ = [
    "VisualizationType",
    "Visualization",
    "VizConfig",
    "TableColumn",
]
