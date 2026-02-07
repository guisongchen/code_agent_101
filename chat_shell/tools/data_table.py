"""
Data table tool for querying and analyzing tabular data.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolInput, ToolOutput

logger = logging.getLogger(__name__)


class DataTableInput(ToolInput):
    """Input schema for data table tool."""
    operation: str = Field(
        ...,
        description="Operation to perform: 'query', 'aggregate', 'filter', 'sort', 'info'"
    )
    source: str = Field(..., description="Data source: file path or table name")
    query: Optional[str] = Field(default=None, description="Query string or condition")
    columns: Optional[List[str]] = Field(default=None, description="Columns to select")
    limit: Optional[int] = Field(default=100, ge=1, le=1000, description="Maximum rows to return")


class DataTableOutput(ToolOutput):
    """Output schema for data table tool."""
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    columns: List[str] = Field(default_factory=list)
    total_rows: int = 0
    summary: Optional[Dict[str, Any]] = None


class DataTableTool(BaseTool):
    """Data table tool for querying tabular data.

    Supports CSV, JSON, and Excel files. Provides operations like
    filtering, sorting, aggregation, and simple SQL-like queries.

    Example:
        tool = DataTableTool()
        result = await tool.execute(DataTableInput(
            operation="filter",
            source="data.csv",
            query="age > 25",
            limit=10
        ))
    """

    name = "data_table"
    description = (
        "Query and analyze tabular data from CSV, Excel, or JSON files. "
        "Supports filtering, sorting, aggregation, and column selection. "
        "Use this for data analysis tasks."
    )
    input_schema = DataTableInput

    def __init__(self):
        """Initialize data table tool."""
        self._cached_data: Dict[str, Any] = {}

    async def execute(self, input_data: DataTableInput) -> ToolOutput:
        """Execute data table operation."""
        try:
            # Load data
            df = await self._load_data(input_data.source)
            if df is None:
                return ToolOutput(
                    result="",
                    error=f"Failed to load data from: {input_data.source}"
                )

            # Perform operation
            if input_data.operation == "query":
                result_df = await self._do_query(df, input_data)
            elif input_data.operation == "filter":
                result_df = await self._do_filter(df, input_data)
            elif input_data.operation == "sort":
                result_df = await self._do_sort(df, input_data)
            elif input_data.operation == "aggregate":
                return await self._do_aggregate(df, input_data)
            elif input_data.operation == "info":
                return await self._do_info(df, input_data)
            else:
                return ToolOutput(
                    result="",
                    error=f"Unknown operation: {input_data.operation}"
                )

            # Format output
            return self._format_output(result_df, input_data)

        except Exception as e:
            logger.error(f"Data table operation failed: {e}")
            return ToolOutput(
                result="",
                error=f"Operation failed: {str(e)}"
            )

    async def _load_data(self, source: str) -> Optional[Any]:
        """Load data from source."""
        import pandas as pd

        # Check cache
        if source in self._cached_data:
            return self._cached_data[source]

        try:
            path = Path(source)
            if not path.exists():
                return None

            suffix = path.suffix.lower()

            if suffix == '.csv':
                df = pd.read_csv(source)
            elif suffix == '.json':
                df = pd.read_json(source)
            elif suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(source)
            elif suffix == '.parquet':
                df = pd.read_parquet(source)
            else:
                # Try CSV as default
                df = pd.read_csv(source)

            # Cache for reuse
            self._cached_data[source] = df
            return df

        except Exception as e:
            logger.error(f"Failed to load data from {source}: {e}")
            return None

    async def _do_query(self, df: Any, input_data: DataTableInput) -> Any:
        """Execute query operation."""
        if input_data.query:
            # Use pandas query syntax
            df = df.query(input_data.query)

        if input_data.columns:
            df = df[input_data.columns]

        return df.head(input_data.limit)

    async def _do_filter(self, df: Any, input_data: DataTableInput) -> Any:
        """Execute filter operation."""
        if input_data.query:
            df = df.query(input_data.query)
        return df.head(input_data.limit)

    async def _do_sort(self, df: Any, input_data: DataTableInput) -> Any:
        """Execute sort operation."""
        if input_data.query:
            # Parse sort columns from query (comma-separated)
            sort_cols = [c.strip() for c in input_data.query.split(',')]
            ascending = [not c.startswith('-') for c in sort_cols]
            sort_cols = [c.lstrip('-+') for c in sort_cols]
            df = df.sort_values(by=sort_cols, ascending=ascending)
        return df.head(input_data.limit)

    async def _do_aggregate(self, df: Any, input_data: DataTableInput) -> DataTableOutput:
        """Execute aggregation operation."""
        # Simple aggregations
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

        summary = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "numeric_summary": {}
        }

        for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
            summary["numeric_summary"][col] = {
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
            }

        result_text = json.dumps(summary, indent=2)

        return DataTableOutput(
            result=result_text,
            rows=[],
            columns=df.columns.tolist(),
            total_rows=len(df),
            summary=summary
        )

    async def _do_info(self, df: Any, input_data: DataTableInput) -> DataTableOutput:
        """Get table info."""
        info = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": []
        }

        for col in df.columns:
            col_info = {
                "name": col,
                "dtype": str(df[col].dtype),
                "non_null": int(df[col].count()),
                "null_count": int(df[col].isnull().sum())
            }
            info["columns"].append(col_info)

        result_text = f"Table Info:\n"
        result_text += f"Rows: {info['row_count']}\n"
        result_text += f"Columns: {info['column_count']}\n\n"
        result_text += "Column Details:\n"
        for col in info["columns"]:
            result_text += f"  {col['name']}: {col['dtype']} "
            result_text += f"({col['non_null']} non-null)\n"

        return DataTableOutput(
            result=result_text,
            rows=[],
            columns=df.columns.tolist(),
            total_rows=info['row_count'],
            summary=info
        )

    def _format_output(self, df: Any, input_data: DataTableInput) -> DataTableOutput:
        """Format DataFrame as output."""
        # Select columns
        columns = input_data.columns or df.columns.tolist()
        df = df[[c for c in columns if c in df.columns]]

        # Limit rows
        df = df.head(input_data.limit)

        # Convert to records
        rows = df.to_dict('records')

        # Format as text
        if len(rows) == 0:
            result_text = "No rows found."
        else:
            result_text = df.to_string(index=False)

        return DataTableOutput(
            result=result_text,
            rows=rows,
            columns=columns,
            total_rows=len(rows)
        )
