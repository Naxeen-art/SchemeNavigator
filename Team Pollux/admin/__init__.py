"""Admin panel modules for Scheme Navigator"""

from .dashboard import render_dashboard
from .upload_json import render_json_upload
from .upload_csv import render_csv_upload
from .upload_form import render_form_upload

__all__ = [
    'render_dashboard',
    'render_json_upload',
    'render_csv_upload',
    'render_form_upload'
]