# my_qareport.py
from __future__ import annotations
import json
import csv
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set
import pytest

try:
    import xlwings as xw  # For Excel writing
except ImportError:
    xw = None


# ===================== Configuration Registration (using pytest.ini) =====================
def pytest_addoption(parser):
    # Custom options to read from pytest.ini
    parser.addini("qa_csv_path", "CSV result file path", default="./report/qa_report.csv")
    parser.addini("qa_excel_path", "Excel file path (target for automatic test result entry)", default=None)
    parser.addini("qa_excel_sheet", "Excel sheet name", default="Sheet1")
    parser.addini("qa_excel_id_col", "Test ID column header in Excel", default="Auto Script")
    parser.addini("qa_excel_result_col", "Result entry column header in Excel", default="Result (Linux)")
    parser.addini("qa_excel_auto_classification", "Auto classification column header in Excel", default="Auto")
    parser.addini("qa_auto_excel_mode", "Excel automatic update mode", type="bool", default=True)
    parser.addini("qa_excel_header_row", "Row number containing headers", default="2")
    

def pytest_configure(config):
    config.addinivalue_line("markers", "priority(level): Priority level (e.g., 'P0','P1')")


# ===================== Result Collector =====================
class _QAResultRecorder:
    def __init__(self, config: pytest.Config):
        self.config = config
        self.records: List[Dict[str, Any]] = []
        self.node_markers: Dict[str, Dict[str, List[str]]] = {}  # nodeid -> {marker_name: [args]}
        self._seen: Set[str] = set()  # Prevent duplicate records (skip/setup vs call)

    def add_markers(self, item: pytest.Item):
        nodeid = item.nodeid
        m: Dict[str, List[str]] = {}
        for mark in item.iter_markers():
            args = [str(a) for a in mark.args] if mark.args else []
            m.setdefault(mark.name, []).extend(args)
        self.node_markers[nodeid] = m

    def _outcome_from_report(self, report: pytest.TestReport) -> str:
        if report.failed:
            return "failed"
        if report.passed:
            return "passed"
        return report.outcome  # fallback

    def add_report(self, report: pytest.TestReport):
        nodeid = report.nodeid

        # Check test completion point
        # However, record the same nodeid only once.
        is_final_phase = (report.when == "call")
        if not is_final_phase or nodeid in self._seen:
            return

        markers = self.node_markers.get(nodeid, {})
        # Use global _current_test_id first, extract from markers if not available
        global _current_test_id
        test_id = _current_test_id
        outcome = self._outcome_from_report(report)

        message = ""
        if getattr(report, "longreprtext", None) and (outcome == "failed"):
            # Extract only check fail message
            full_message = report.longreprtext
            
            # Check pytest-check failure count (from terminal output)
            # Find "Failed Checks: N" pattern
            failed_checks_match = re.search(r'Failed Checks: (\d+)', full_message)
            failure_count = int(failed_checks_match.group(1)) if failed_checks_match else 1
            
            # Extract first failure message from pytest-check
            # Find "FAILURE: check ... : message" pattern
            failure_messages = re.findall(r'FAILURE: check [^:]+: ([^\n\r]+)', full_message)
            
            if failure_messages:
                # Use first failure message
                message = failure_messages[0]
                
                # Add count information if multiple failures
                if failure_count > 1:
                    message = f"({failure_count} failures) {message}"
            else:
                # Regular expression to extract third argument (message) from check.equal() function
                check_messages = re.findall(r'check\.equal\([^,)]+,\s*[^,)]+,\s*["\']([^"\']+)["\']', full_message)
                if check_messages:
                    message = check_messages[0]
                    if failure_count > 1:
                        message = f"({failure_count} failures) {message}"
                else:
                    # Use default failure message
                    if failure_count > 1:
                        message = f"({failure_count} check failures)"
                    else:
                        message = "Test failed"

        rec = {
            "test_id": test_id,
            "nodeid": nodeid,
            "outcome": outcome,  # passed/failed
            "duration": getattr(report, "duration", None),
            "markers": markers,  # Original markers (all keys)
            "message": message,
        }
        self.records.append(rec)
        self._seen.add(nodeid)

    def stats(self):
        from collections import Counter
        c = Counter(r["outcome"] for r in self.records)
        return {"total": len(self.records), **c}


# Global collector
_recorder: _QAResultRecorder | None = None

# Global variable to store test_id of currently running test
_current_test_id: str | None = None

# Global variable to store timestamp at test session start
_session_timestamp: str | None = None

def set_test_id(test_id: str):
    """Function to set test_id from test function"""
    global _current_test_id
    _current_test_id = test_id


# ===================== Hook Implementation =====================
@pytest.hookimpl
def pytest_sessionstart(session):
    global _recorder, _session_timestamp
    _recorder = _QAResultRecorder(session.config)
    # Generate timestamp at session start
    _session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

@pytest.hookimpl
def pytest_collection_modifyitems(session, config, items):
    for it in items:
        _recorder.add_markers(it)

@pytest.hookimpl
def pytest_runtest_logreport(report):
    _recorder.add_report(report)

@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    config = session.config
    
    # Generate CSV only if actual tests were executed
    if not _recorder or not _recorder.records:
        print("DEBUG: No executed tests found, skipping CSV file generation.")
        return
    
    # Check if pytest actually executed tests (if collected items exist)
    if not hasattr(session, 'items') or not session.items:
        print("DEBUG: No collected tests found, skipping CSV file generation.")
        return
    
    # Check if there are actually executed tests
    executed_tests = [r for r in _recorder.records if r.get("duration") is not None]
    if not executed_tests:
        print("DEBUG: No executed tests found, skipping CSV file generation.")
        return
    
    print()
    print()
    print(f"DEBUG: Generating CSV file with {len(executed_tests)} executed test results.")
    
    # Save CSV
    csv_path = config.getini("qa_csv_path").strip('"')
    
    # Use timestamp from session start
    global _session_timestamp
    date_time = _session_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Separate directory and filename from original path
    csv_dir = os.path.dirname(csv_path)
    csv_filename = os.path.basename(csv_path)
    
    # Add timestamp to filename
    name, ext = os.path.splitext(csv_filename)
    timestamped_filename = f"{date_time}_{name}{ext}"
    timestamped_csv_path = os.path.join(csv_dir, timestamped_filename)
    
    # Excel update (only when qa_auto_excel_mode is true and executed tests exist)
    auto_excel_mode = config.getini("qa_auto_excel_mode")
    excel_path = config.getini("qa_excel_path")
    
    if auto_excel_mode and excel_path and executed_tests:
        # Remove quotes
        excel_path = excel_path.strip('"')
        if os.path.exists(excel_path):
            print(f"DEBUG: Excel file found: {excel_path}")
        else:
            print(f"WARNING: Excel file not found: {excel_path}")
        
        if xw is None:
            print("WARNING: Skipping Excel update due to xlwings not installed. `pip install xlwings` required.")
        else:
            try:
                _update_excel(
                    excel_path,
                    sheet=config.getini("qa_excel_sheet").strip('"'),
                    id_col=config.getini("qa_excel_id_col").strip('"'),
                    result_col=config.getini("qa_excel_result_col").strip('"'),
                    records=_recorder.records,
                    header_row=int(config.getini("qa_excel_header_row")),
                    auto_classification_col=config.getini("qa_excel_auto_classification").strip('"'),
                )
            except Exception as e:
                print(f"WARNING: Error occurred during Excel update: {e}")
                print("CSV file was generated successfully.")
    elif not auto_excel_mode:
        print("DEBUG: Skipping Excel update as qa_auto_excel_mode is set to false.")
    else:
        print("DEBUG: qa_excel_path is not configured.")
    
    # Generate CSV file (run after Excel update to include Auto classification values)
    print(f"DEBUG: Generating CSV file with {len(_recorder.records)} test results.")
    _write_csv(timestamped_csv_path, _recorder.records)


# ===================== Utilities =====================
def _sanitize_for_excel(v):
    s = str(v) if v is not None else ""
    return "'" + s if s and s[0] in ("=", "+", "-", "@") else s

def _write_csv(path: str, records: List[Dict[str, Any]]):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    # Basic fields + Auto column added
    fields = ["test_id", "result", "message", "markers", "duration", "path", "Auto"]

    with open(path, "w", newline="", encoding="utf-8-sig") as f:  # Include BOM
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in records:
            # Convert markers to simple list format
            markers_list = []
            for marker_name, marker_values in r.get("markers", {}).items():
                if marker_values:
                    # When values exist: marker_name=value1,value2
                    markers_list.append(f"{marker_name}={','.join(marker_values)}")
                else:
                    # When no values: marker_name
                    markers_list.append(marker_name)
            markers_str = ", ".join(markers_list)
            
            # Format duration to 2 decimal places
            duration = r.get("duration")
            duration_str = f"{duration:.2f}" if isinstance(duration, (int, float)) else ""
            
            row = {
                "test_id": _sanitize_for_excel(r.get("test_id", "")),
                "path": _sanitize_for_excel(r.get("nodeid", "")),
                "result": r.get("outcome", ""),
                "duration": duration_str,
                "message": _sanitize_for_excel(r.get("message", "")),
                "markers": _sanitize_for_excel(markers_str),
                "Auto": _sanitize_for_excel(r.get("auto_classification", "")),
            }
            w.writerow(row)

def _update_excel(xlsx: str, sheet: str, id_col: str, result_col: str, records: List[Dict[str, Any]], header_row: int, auto_classification_col: str = None):
    app = None
    wb = None
    try:
        # Open Excel file with xlwings
        app = xw.App(visible=False)  # Run Excel in background
        wb = app.books.open(xlsx)
        
        # Check sheet
        if sheet not in [s.name for s in wb.sheets]:
            print(f"ERROR: Sheet '{sheet}' not found.")
            wb.close()
            app.quit()
            return
            
        ws = wb.sheets[sheet]
        
        # Read headers
        headers = {}
        header_range = ws.range(f"{header_row}:{header_row}")
        for idx, cell in enumerate(header_range, start=1):
            if cell.value is not None:
                headers[str(cell.value).strip()] = idx
                
        if id_col not in headers or result_col not in headers:
            print(f"ERROR: Headers not found. (id_col='{id_col}', result_col='{result_col}')")
            wb.close()
            app.quit()
            return

        id_idx = headers[id_col]
        res_idx = headers[result_col]
        
        # Find auto_classification column index
        auto_idx = None
        if auto_classification_col and auto_classification_col in headers:
            auto_idx = headers[auto_classification_col]
        else:
            print(f"WARNING: Auto classification column not found: '{auto_classification_col}'")
            print(f"DEBUG: Available headers: {list(headers.keys())}")
        
        # Create Excel ID -> row number map
        id_to_row = {}
        
        # Generate test ID list collected from CSV (for matching verification)
        csv_test_ids = set()
        for r in records:
            tid = r.get("test_id", "")
            if tid:
                csv_test_ids.add(tid)
                # Also add Excel format
                nodeid = r.get("nodeid", "")
                if "::" in nodeid:
                    script_path, test_name = nodeid.split("::", 1)
                    script_name = os.path.basename(script_path)
                    excel_format_id = f"[{script_name}] {tid}"
                    csv_test_ids.add(excel_format_id)
        
        # Read in small ranges (100 rows at a time)
        batch_size = 100
        start_row = header_row + 1
        max_attempts = 50  # Try up to 5000 rows (50 * 100)
        
        for batch in range(max_attempts):
            batch_start = start_row + (batch * batch_size)
            batch_end = batch_start + batch_size - 1
            
            batch_found = False
            for row_num in range(batch_start, batch_end + 1):
                try:
                    # Read individual cells (safer method)
                    id_cell = ws.cells(row_num, id_idx)
                    if id_cell.value is not None and str(id_cell.value).strip():
                        excel_id = str(id_cell.value).strip()
                        id_to_row[excel_id] = row_num
                        batch_found = True
                        
                except Exception as e:
                    # Ignore cell reading errors and continue
                    continue
            
            # Check if all CSV test IDs are matched
            matched_count = 0
            for csv_id in csv_test_ids:
                # Direct matching check
                if csv_id in id_to_row:
                    matched_count += 1
                    continue
                # Partial matching check (normalize line break characters)
                for excel_id in id_to_row.keys():
                    normalized_excel_id = excel_id.replace('\n', ' ').replace('\r', ' ')
                    if csv_id in normalized_excel_id or any(part in normalized_excel_id for part in csv_id.split() if len(part) > 3):
                        matched_count += 1
                        break
            
            # Stop if all CSV tests are matched
            if matched_count >= len(csv_test_ids) and len(csv_test_ids) > 0:
                break

        # Result mapping (use desired notation)
        outcome_map = {
            "passed": "PASS",
            "failed": "FAIL",
        }

        # Update test results
        updated_count = 0
        auto_classification_count = 0
        total_records = len(records)
        
        for r in records:
            tid = r.get("test_id")
            if not tid:
                continue
            
            # Convert CSV test_id to Excel format
            # Extract script name from nodeid (e.g., cxr-4010/tests/testcase/test_common_api.py::test_capi_health_to_gw)
            nodeid = r.get("nodeid", "")
            if "::" in nodeid:
                script_path, test_name = nodeid.split("::", 1)
                script_name = os.path.basename(script_path)  # test_common_api.py
                excel_format_id = f"[{script_name}] {tid}"
            else:
                excel_format_id = tid
            
            # Try matching in Excel
            rownum = None
            matched_id = None
            
            # 1. Try direct test_id matching
            test_id_key = str(tid).strip()
            rownum = id_to_row.get(test_id_key)
            if rownum:
                matched_id = test_id_key
            
            # 2. Try Excel format [script_name] test_id matching
            if rownum is None:
                rownum = id_to_row.get(excel_format_id)
                if rownum:
                    matched_id = excel_format_id
            
            # 3. Try partial matching (when Excel ID contains test_id)
            if rownum is None:
                for excel_id, row_num in id_to_row.items():
                    # Convert line break characters to spaces in Excel ID for comparison
                    normalized_excel_id = excel_id.replace('\n', ' ').replace('\r', ' ')
                    if tid in normalized_excel_id:
                        rownum = row_num
                        matched_id = excel_id
                        break
            
            if rownum:
                try:
                    # Update result
                    result_cell = ws.cells(rownum, res_idx)
                    result_value = outcome_map.get(r["outcome"], r["outcome"].upper())
                    result_cell.value = result_value
                    
                    # Read Auto classification value and add to records
                    if auto_idx:
                        try:
                            auto_cell = ws.cells(rownum, auto_idx)
                            auto_value = auto_cell.value
                            if auto_value is not None:
                                r["auto_classification"] = str(auto_value).strip()
                                auto_classification_count += 1
                        except Exception as e:
                            print(f"WARNING: Cannot read Auto classification value (row {rownum}): {e}")
                    
                    updated_count += 1
                except Exception as e:
                    # Try alternative method
                    try:
                        result_cell = ws.range(f"{rownum}:{rownum},{res_idx}:{res_idx}")
                        result_value = outcome_map.get(r["outcome"], r["outcome"].upper())
                        result_cell.value = result_value
                        
                        # Read Auto classification value and add to records
                        if auto_idx:
                            try:
                                auto_cell = ws.range(f"{rownum}:{rownum},{auto_idx}:{auto_idx}")
                                auto_value = auto_cell.value
                                if auto_value is not None:
                                    r["auto_classification"] = str(auto_value).strip()
                                    auto_classification_count += 1
                            except Exception as e:
                                print(f"WARNING: Cannot read Auto classification value (row {rownum}): {e}")
                        
                        updated_count += 1
                    except Exception as e2:
                        continue

        # Save file and exit
        wb.save()
        wb.close()
        app.quit()
        
        # Output success log
        if updated_count == total_records and total_records > 0:
            print(f"INFO: Excel file updated successfully. ({updated_count}/{total_records} test results updated)")
        elif updated_count > 0:
            print(f"WARNING: Excel file partially updated. ({updated_count}/{total_records} test results updated)")
        else:
            print("WARNING: No matching tests found in Excel file.")
        
        # Auto classification success message
        if auto_classification_count > 0:
            print(f"INFO: Successfully updated Auto classification values in CSV file. ({auto_classification_count}/{total_records})")
        
    except Exception as e:
        print(f"ERROR: Error occurred while processing Excel file: {e}")
        try:
            if wb:
                wb.close()
            if app:
                app.quit()
        except:
            pass
