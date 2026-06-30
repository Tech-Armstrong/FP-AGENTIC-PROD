"""
PowerPoint Report Generator - Standalone CLI

Runs the financial planning workflow against a persona fixture, then writes a .pptx
to Financial_Planning/PPT_io/PPT_output/.

For dashboard use, see POST /financial-plan/ppt (uses cached workflow_state from Make plan).
"""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from Financial_Planning.Utilities.ppt_runner import generate_financial_plan_ppt
from Financial_Planning.Workflow.workflow import workflow

try:
    from Financial_Planning.input_data_personas import client_data
except ImportError as exc:
    raise SystemExit(
        "Financial_Planning.input_data_personas is required for the standalone CLI. "
        "Use POST /financial-plan/ppt from the dashboard instead."
    ) from exc


def main() -> None:
    initial_state = {
        "client_data": client_data,
        "EMI_allocated": False,
        "loan_prepayed_times": 0,
        "used_monthly_surplus": [0],
        "optimal_selected": False,
    }
    final_state = workflow.invoke(initial_state, config={"recursion_limit": 50})

    ppt_bytes, filename = generate_financial_plan_ppt(final_state)
    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "PPT_io", "PPT_output"
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)
    with open(out_path, "wb") as f:
        f.write(ppt_bytes)
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
