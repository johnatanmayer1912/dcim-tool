"""
Organized search_it report folders under {data_root}/outputs/<category>/<date>/<run_id>/.

Re-exports from utils.output_paths for backward compatibility.
"""
from utils.output_paths import (  # noqa: F401
    get_app_root,
    get_data_root,
    prepare_search_run,
    prepare_run_output,
    path_in_run,
    slugify,
    write_run_manifest,
)
