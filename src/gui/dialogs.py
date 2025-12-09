"""
Dialog Windows for PyRAG GUI

This module serves as an import hub for all dialog windows.
Individual dialogs are now separated into their own modules for better maintainability.
"""

from .new_document_dialog import NewDocumentDialog
from .settings_dialog import SettingsDialog
from .database_manager_dialog import DatabaseManagerDialog
from .cross_reference_dialog import CrossReferenceDialog
from .auto_summary_dialog import AutoSummaryDialog
from .query_history_dialog import QueryHistoryDialog
from .export_dialog import ExportDialog
from .graph_visualization_dialog import GraphVisualizationDialog

__all__ = [
    'NewDocumentDialog',
    'SettingsDialog',
    'DatabaseManagerDialog',
    'CrossReferenceDialog',
    'AutoSummaryDialog',
    'QueryHistoryDialog',
    'ExportDialog',
    'GraphVisualizationDialog',
]
