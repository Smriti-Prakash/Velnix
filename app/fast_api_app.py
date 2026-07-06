# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib
import os
import json
import asyncio
import queue
import threading
from collections.abc import AsyncIterator

import google.auth
from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.cloud import logging as google_cloud_logging

from app.app_utils import services
from app.app_utils.a2a import attach_a2a_routes
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

load_dotenv()
setup_telemetry()

# Ensure profiling output is visible in server console
import logging as _py_logging
_py_logging.basicConfig(level=_py_logging.INFO, format="%(asctime)s %(name)s %(levelname)s  %(message)s")
_py_logging.getLogger("velnix.profiler").setLevel(_py_logging.INFO)

_, project_id = google.auth.default()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") 
    if os.getenv("ALLOW_ORIGINS") 
    else [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Initialise the ERP SQLite database (creates tables + seeds data if empty)
    from app.erp.database import init_db
    init_db()

    from app.agent import app as adk_app
    from app.agent import root_agent

    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
        auto_create_session=True,
    )
    app.state.runner = runner
    app.state.agent_app_name = adk_app.name
    await attach_a2a_routes(
        app,
        agent=root_agent,
        runner=runner,
        task_store=InMemoryTaskStore(),
        rpc_path=f"/a2a/{adk_app.name}",
    )
    yield


app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=services.ARTIFACT_SERVICE_URI,
    allow_origins=allow_origins,
    session_service_uri=services.SESSION_SERVICE_URI,
    otel_to_cloud=False,
    lifespan=lifespan,
)
app.title = "velnix"
app.description = "API for interacting with the Agent velnix"

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    try:
        logger.log_struct(feedback.model_dump(), severity="INFO")
    except Exception as e:
        import logging as py_logging
        local_logger = py_logging.getLogger("velnix.feedback")
        local_logger.warning("Failed to log to Cloud Logging; falling back to local: %s (Error: %s)", feedback.model_dump(), e)
    return {"status": "success"}


# ---------------------------------------------------------------------------
# ERP Data Management Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/erp/vendors")
def get_erp_vendors():
    """Retrieve all vendors from the ERP database."""
    from app.erp.queries import fetch_all_vendors
    vendors = fetch_all_vendors()
    return [v.to_dict() for v in vendors]


@app.get("/api/erp/vendors/{vendor_id}")
def get_erp_vendor(vendor_id: int):
    """Retrieve a specific vendor's profile from the ERP database by ID."""
    from app.erp.queries import fetch_vendor_by_id
    vendor = fetch_vendor_by_id(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor.to_dict()


@app.get("/api/erp/vendors/{vendor_id}/history")
def get_erp_vendor_history(vendor_id: int):
    """Retrieve historical invoices for a specific vendor by vendor ID."""
    from app.erp.queries import fetch_invoice_history_by_vendor_id
    history = fetch_invoice_history_by_vendor_id(vendor_id)
    return [h.to_dict() for h in history]


@app.get("/api/erp/vendors/{vendor_id}/purchase-orders")
def get_erp_vendor_purchase_orders(vendor_id: int):
    """Retrieve purchase orders associated with a specific vendor ID."""
    from app.erp.queries import fetch_purchase_orders_by_vendor_id
    pos = fetch_purchase_orders_by_vendor_id(vendor_id)
    return [po.to_dict() for po in pos]


@app.get("/api/erp/vendors/{vendor_id}/goods-receipts")
def get_erp_vendor_goods_receipts(vendor_id: int):
    """Retrieve goods receipts associated with a specific vendor ID."""
    from app.erp.queries import fetch_goods_receipts_by_vendor_id
    receipts = fetch_goods_receipts_by_vendor_id(vendor_id)
    return [r.to_dict() for r in receipts]


@app.get("/api/erp/purchase-orders")
def get_erp_purchase_orders():
    """Retrieve all purchase orders from the ERP database."""
    from app.erp.queries import fetch_all_purchase_orders
    pos = fetch_all_purchase_orders()
    return [po.to_dict() for po in pos]


@app.get("/api/erp/purchase-orders/{po_number}")
def get_erp_purchase_order(po_number: str):
    """Retrieve a specific purchase order from the ERP database by PO number."""
    from app.erp.queries import fetch_purchase_order
    po = fetch_purchase_order(po_number)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    return po.to_dict()


@app.get("/api/erp/goods-receipts")
def get_erp_goods_receipts():
    """Retrieve all goods receipts from the ERP database."""
    from app.erp.queries import fetch_all_goods_receipts
    receipts = fetch_all_goods_receipts()
    return [r.to_dict() for r in receipts]


@app.get("/api/erp/goods-receipts/{grn_number}")
def get_erp_goods_receipt(grn_number: str):
    """Retrieve a specific goods receipt from the ERP database by GRN."""
    from app.erp.queries import fetch_goods_receipt_by_grn
    receipt = fetch_goods_receipt_by_grn(grn_number)
    if not receipt:
        raise HTTPException(status_code=404, detail="Goods Receipt not found")
    return receipt.to_dict()



def parse_csv_invoice(contents: bytes) -> dict:
    import csv
    import io
    import re

    try:
        text = contents.decode("utf-8", errors="ignore")
    except Exception as e:
        raise ValueError(f"Failed to decode CSV bytes: {str(e)}")

    f = io.StringIO(text.strip())
    reader = csv.reader(f)
    rows = [row for row in reader if row]

    if not rows:
        raise ValueError("The uploaded CSV file is empty.")

    data = {}
    key_mapping = {
        "invoice_number": ["invoice_number", "invoice_id", "invoice number", "invoice id", "number", "id"],
        "vendor_name": ["vendor_name", "vendor name", "vendor", "name"],
        "invoice_date": ["invoice_date", "invoice date", "date"],
        "due_date": ["due_date", "due date"],
        "purchase_order_number": ["purchase_order_number", "purchase order number", "purchase_order", "purchase order", "po_number", "po number", "po"],
        "order_id": ["order_id", "order id", "order"],
        "currency": ["currency", "curr"],
        "invoice_amount": ["invoice_amount", "invoice amount", "amount", "total"],
        "payment_terms": ["payment_terms", "payment terms", "terms"],
    }

    # Detect header-row vs key-value format (header-row needs at least 4 columns for required fields)
    headers = [h.strip().lower() for h in rows[0]]
    is_header_row = len(rows[0]) >= 4

    if is_header_row and len(rows) > 1:
        values = rows[1]
        for std_key, aliases in key_mapping.items():
            for i, h in enumerate(headers):
                if h in aliases and i < len(values):
                    data[std_key] = values[i].strip()
                    break
    else:
        for row in rows:
            if len(row) >= 2:
                key = row[0].strip().lower()
                val = row[1].strip()
                for std_key, aliases in key_mapping.items():
                    if key in aliases:
                        data[std_key] = val
                        break

    # Required fields validation
    inv_num = data.get("invoice_number")
    if not inv_num or not inv_num.strip():
        raise ValueError("Missing required field: Invoice Number.")

    vend_name = data.get("vendor_name")
    if not vend_name or not vend_name.strip():
        raise ValueError("Missing required field: Vendor Name.")

    inv_amount_str = data.get("invoice_amount")
    if not inv_amount_str or not inv_amount_str.strip():
        raise ValueError("Missing required field: Invoice Amount.")

    # Clean amount string to extract float (preserve minus sign for negative numbers)
    amount_clean = re.sub(r'[^\d.-]', '', inv_amount_str)
    try:
        inv_amount = float(amount_clean) if amount_clean else 0.0
    except ValueError:
        inv_amount = 0.0


    if inv_amount <= 0:
        raise ValueError("Invalid or missing Invoice Amount. Must be a positive number.")

    inv_date = data.get("invoice_date")
    if not inv_date or not inv_date.strip():
        raise ValueError("Missing required field: Invoice Date.")

    # Try to auto-normalize common date formats to YYYY-MM-DD
    from datetime import datetime
    date_formats = [
        "%Y-%m-%d",      # 2026-07-01
        "%m/%d/%Y",      # 07/01/2026
        "%d/%m/%Y",      # 01/07/2026
        "%Y/%m/%d",      # 2026/07/01
        "%d-%m-%Y",      # 01-07-2026
        "%m-%d-%Y",      # 07-01-2026
        "%Y.%m.%d",      # 2026.07.01
        "%B %d, %Y",     # July 01, 2026
        "%b %d, %Y",     # Jul 01, 2026
        "%d %B %Y",      # 01 July 2026
        "%d %b %Y",      # 01 Jul 2026
    ]
    normalized = None
    for fmt in date_formats:
        try:
            dt = datetime.strptime(inv_date.strip(), fmt)
            normalized = dt.strftime("%Y-%m-%d")
            break
        except ValueError:
            pass

    if normalized:
        inv_date = normalized
    else:
        try:
            # Also try splitting by space to handle timestamps like "2026-07-01 00:00:00"
            date_part = inv_date.strip().split(" ")[0]
            for fmt in date_formats:
                try:
                    dt = datetime.strptime(date_part, fmt)
                    inv_date = dt.strftime("%Y-%m-%d")
                    break
                except ValueError:
                    pass
        except Exception:
            pass

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", inv_date.strip()):
        raise ValueError("Invalid Invoice Date format (must be YYYY-MM-DD).")

    # Extract currency if not provided
    currency = data.get("currency")
    if not currency:
        currency = "$"
        sym_match = re.match(r'^([^\d\s]+)', inv_amount_str)
        if sym_match:
            currency = sym_match.group(1).strip()

    # Compile standard representation for Gemini / fallback parser
    structured_text = (
        f"Invoice ID: {inv_num}\n"
        f"Vendor Name: {vend_name}\n"
        f"Invoice Date: {inv_date}\n"
        f"Total Amount: {currency}{inv_amount:,.2f}\n"
    )
    if data.get("due_date"):
        structured_text += f"Due Date: {data.get('due_date')}\n"
    if data.get("purchase_order_number"):
        structured_text += f"Purchase Order Number: {data.get('purchase_order_number')}\n"
    if data.get("order_id"):
        structured_text += f"Order ID: {data.get('order_id')}\n"
    if data.get("payment_terms"):
        structured_text += f"Payment Terms: {data.get('payment_terms')}\n"

    return {
        "text": structured_text,
        "amount": inv_amount,
        "currency": currency,
        "invoice_number": inv_num,
        "vendor_name": vend_name,
        "invoice_date": inv_date,
    }


@app.post("/api/upload")
async def upload_invoice(file: UploadFile = File(...)):
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pdf", ".png", ".jpg", ".jpeg", ".csv"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a PDF, PNG, JPEG, or CSV."
        )

    # Validate file size (10MB limit)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds the 10MB limit."
        )

    # -----------------------------------------------------------------------
    # Create a per-request profiler and propagate it via thread-local context
    # to all downstream modules (queries.py, invoice_tools.py, agent.py).
    # -----------------------------------------------------------------------
    import uuid
    from app.profiler import PipelineProfiler
    _profiler = PipelineProfiler(run_id=str(uuid.uuid4())[:8])

    def _attach_profiler():
        """Propagate the profiler to every thread-local context that instruments code."""
        from app.erp import queries as _q
        from app.tools import invoice_tools as _it
        from app import agent as _ag
        _q._profiler_ctx.profiler = _profiler
        _it._profiler_ctx.profiler = _profiler
        _ag._profiler_ctx.profiler = _profiler

    import threading
    threading.Thread(target=_attach_profiler, daemon=True).start()
    # Also attach on the calling (event-loop) thread directly
    _attach_profiler()

    async def event_generator():
        # Step 1: Upload Complete
        yield {
            "event": "progress",
            "data": json.dumps({"step": "upload_complete", "message": "Upload complete"})
        }
        await asyncio.sleep(0.5)

        # Step 2: Document Extraction
        yield {
            "event": "progress",
            "data": json.dumps({"step": "extracting_text", "message": "Extracting document text..."})
        }

        # Perform local/Gemini extraction
        extracted_text = ""
        is_scanned_pdf = False
        loop = asyncio.get_running_loop()

        if ext == ".csv":
            with _profiler.stage("document_extraction_csv", file_type="csv", file_bytes=len(contents)):
                try:
                    csv_data = parse_csv_invoice(contents)
                    extracted_text = csv_data["text"]
                except ValueError as val_err:
                    yield {
                        "event": "error",
                        "data": json.dumps({"message": f"Validation failure: {str(val_err)}"})
                    }
                    return
                except Exception as e:
                    yield {
                        "event": "error",
                        "data": json.dumps({"message": f"CSV parsing failure: {str(e)}"})
                    }
                    return
        elif ext == ".pdf":
            with _profiler.stage("document_extraction_pdf_local", file_type="pdf", file_bytes=len(contents)):
                try:
                    # Local extraction using PyMuPDF (fitz)
                    def extract_fitz():
                        import fitz
                        doc = fitz.open(stream=contents, filetype="pdf")
                        txt = ""
                        for page in doc:
                            txt += page.get_text()
                        doc.close()
                        return txt

                    extracted_text = await loop.run_in_executor(None, extract_fitz)
                    if len(extracted_text.strip()) < 50:
                        is_scanned_pdf = True
                except Exception:
                    is_scanned_pdf = True
        
        # If it's an image or a scanned PDF, fall back to Gemini Vision
        if ext in [".png", ".jpg", ".jpeg"] or is_scanned_pdf:
            yield {
                "event": "progress",
                "data": json.dumps({"step": "extracting_text", "message": "Performing AI OCR on scanned document..."})
            }
            with _profiler.stage("document_extraction_gemini_ocr", file_type=ext, file_bytes=len(contents)):
                try:
                    from google import genai
                    from google.genai import types
                    
                    # Map MIME type appropriately
                    mime_type = file.content_type
                    if ext in [".jpg", ".jpeg"] and mime_type in ["image/jpg", "image/jpeg"]:
                        mime_type = "image/jpeg"
                    elif ext == ".png":
                        mime_type = "image/png"
                    elif ext == ".pdf":
                        mime_type = "application/pdf"
                    
                    api_key = os.environ.get("GEMINI_API_KEY")
                    client = genai.Client(api_key=api_key)

                    # Record the OCR Gemini call
                    _ocr_call = _profiler.record_gemini_call(
                        caller="gemini_vision_ocr",
                        prompt_chars=len(contents),
                        model="gemini-2.5-flash",
                        call_type="generate_content",
                    )
                    
                    # Use gemini-2.5-flash for OCR
                    response = await loop.run_in_executor(
                        None,
                        lambda: client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[
                                types.Part.from_bytes(
                                    data=contents,
                                    mime_type=mime_type,
                                ),
                                "Extract and return all text from this document as plain text. Do not add comments, formatting, or markdown wrappers, just return the raw text."
                            ]
                        )
                    )
                    _ocr_call.finish()
                    extracted_text = response.text
                except Exception as e:
                    yield {
                        "event": "error",
                        "data": json.dumps({"message": f"Extraction failure: {str(e)}"})
                    }
                    return

        if not extracted_text or not extracted_text.strip():
            yield {
                "event": "error",
                "data": json.dumps({"message": "Document text extraction returned empty content."})
            }
            return

        yield {
            "event": "progress",
            "data": json.dumps({"step": "document_extraction", "message": "Document text extracted"})
        }
        await asyncio.sleep(0.5)

        # Step 3: Run the multi-agent pipeline using the runner
        # NOTE: Cannot use `with _profiler.stage()` here because this section
        # contains `yield` and `async for`, which are incompatible with synchronous
        # context managers. Instead, record start/end time manually.
        _pipeline_stage_start = __import__("time").perf_counter()
        try:
            from google.adk.agents.run_config import RunConfig, StreamingMode
            from google.adk.runners import Runner
            from app.agent import root_agent, _clear_request_context, _request_ctx as _agent_request_ctx
            from app.app_utils import services
            from google.genai import types

            # Clear canonical stores before each run so that a previous
            # request's vendor profile cannot leak into this one.
            _clear_request_context()

            # Propagate the profiler into the agent context (existing pattern).
            from app.agent import _profiler_ctx as _agent_profiler_ctx
            _agent_profiler_ctx.profiler = _profiler
            
            session_service = services.get_session_service()
            session = await loop.run_in_executor(
                None,
                lambda: session_service.create_session_sync(user_id="anonymous", app_name="velnix")
            )
            
            runner = app.state.runner
            
            message = types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"Please analyze this invoice:\n{extracted_text}")]
            )
            
            # Run the generator asynchronously on the FastAPI event loop
            events_generator = runner.run_async(
                new_message=message,
                user_id="anonymous",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
            
            full_report = ""
            seen_steps = set()
            # Per-agent stage timers: start when the orchestrator dispatches, end on next dispatch or completion
            _agent_stage_timers: dict = {}
            
            # Collect response payloads to return structured data to the frontend
            invoice_data = {}
            vendor_profile = {}
            risk_assessment = {}
            fraud_assessment = {}
            final_report_text = ""
            
            async for event in events_generator:

                # Detect active sub-agents and capture tool responses
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        # Extract structured tool responses
                        if part.function_response:
                            resp = part.function_response
                            
                            # Parse response value safely
                            res_val = resp.response
                            resp_dict = {}
                            if res_val is not None:
                                try:
                                    if hasattr(res_val, "fields") or not isinstance(res_val, (dict, list, str, int, float, bool)):
                                        from google.protobuf.json_format import MessageToDict
                                        resp_dict = MessageToDict(res_val)
                                    elif isinstance(res_val, dict):
                                        resp_dict = res_val
                                    else:
                                        resp_dict = dict(res_val)
                                except Exception:
                                    try:
                                        resp_dict = dict(res_val)
                                    except Exception:
                                        resp_dict = {}
                                        
                                # If it's wrapped in a "result" key, unwrap it
                                if isinstance(resp_dict, dict) and "result" in resp_dict:
                                    # Sometimes sub-agents return their text wrapped in result, but we only want tool dictionary
                                    if not isinstance(resp_dict["result"], str):
                                        resp_dict = resp_dict["result"]
                                    
                            if isinstance(resp_dict, dict) and len(resp_dict) > 0:
                                if resp.name == "parse_invoice_tool":
                                    invoice_data = resp_dict
                                elif resp.name == "calculate_risk_tool":
                                    risk_assessment = resp_dict
                                elif resp.name == "calculate_fraud_tool":
                                    fraud_assessment = resp_dict
                                elif resp.name in ("get_vendor_profile_tool", "get_vendor_profile"):
                                    # Capture vendor profile from either the new Python tool
                                    # (get_vendor_profile_tool) or the legacy MCP tool name.
                                    vendor_profile = resp_dict
                                elif resp.name == "compile_report_tool":
                                    if isinstance(resp_dict, dict) and "result" in resp_dict:
                                        final_report_text = resp_dict["result"]

                        if part.text:
                            # Only capture the text from the final compile/decision phase to avoid intermediate text dumps
                            if "final_decision" in seen_steps:
                                full_report += part.text

                        if part.function_call:
                            name = part.function_call.name
                            import time as _time

                            # --- Agent dispatch timing ---
                            # Close any previous agent timer when a new agent is dispatched
                            _AGENT_DISPATCH_NAMES = {
                                "invoice_analysis_agent": "agent_invoice_analysis",
                                "vendor_intelligence_agent": "agent_vendor_intelligence",
                                "risk_assessment_agent": "agent_risk_assessment",
                                "fraud_intelligence_agent": "agent_fraud_intelligence",
                                "final_decision_agent": "agent_final_decision",
                            }
                            if name in _AGENT_DISPATCH_NAMES:
                                # End the previous open agent timer, if any
                                for _prev_name, _prev_rec in list(_agent_stage_timers.items()):
                                    _prev_rec.finish()
                                    _profiler.stages.append(_prev_rec)
                                    _agent_stage_timers.pop(_prev_name)
                                    import logging as _logging
                                    _logging.getLogger("velnix.profiler").info(
                                        "[PROFILER] %-38s  %8.1f ms",
                                        _prev_rec.stage,
                                        _prev_rec.duration_ms,
                                    )
                                # Start a new timer for this agent
                                from app.profiler import StageRecord
                                _stage_name = _AGENT_DISPATCH_NAMES[name]
                                _agent_stage_timers[_stage_name] = StageRecord(
                                    stage=_stage_name,
                                    start_time=_time.perf_counter(),
                                )
                            # --- End agent dispatch timing ---

                            if name == "invoice_analysis_agent" and "invoice_analysis" not in seen_steps:
                                seen_steps.add("invoice_analysis")
                                yield {
                                    "event": "progress",
                                    "data": json.dumps({"step": "invoice_analysis", "message": "Invoice analysis complete"})
                                }
                            elif name == "vendor_intelligence_agent" and "vendor_intelligence" not in seen_steps:
                                seen_steps.add("vendor_intelligence")
                                yield {
                                    "event": "progress",
                                    "data": json.dumps({"step": "vendor_intelligence", "message": "Vendor intelligence complete"})
                                }
                            elif name == "risk_assessment_agent" and "risk_assessment" not in seen_steps:
                                seen_steps.add("risk_assessment")
                                yield {
                                    "event": "progress",
                                    "data": json.dumps({"step": "risk_assessment", "message": "Risk assessment complete"})
                                }
                            elif name == "fraud_intelligence_agent" and "fraud_intelligence" not in seen_steps:
                                seen_steps.add("fraud_intelligence")
                                yield {
                                    "event": "progress",
                                    "data": json.dumps({"step": "fraud_intelligence", "message": "Fraud intelligence complete"})
                                }
                            elif name == "final_decision_agent" and "final_decision" not in seen_steps:
                                seen_steps.add("final_decision")
                                yield {
                                    "event": "progress",
                                    "data": json.dumps({"step": "final_decision", "message": "Final decision complete"})
                                }
                    
            # Close any remaining open agent timer
            for _prev_name, _prev_rec in list(_agent_stage_timers.items()):
                _prev_rec.finish()
                _profiler.stages.append(_prev_rec)

            # Record total pipeline duration manually
            import time as _t
            _pipeline_duration_ms = (_t.perf_counter() - _pipeline_stage_start) * 1000.0
            from app.profiler import StageRecord as _SR
            _pipe_rec = _SR(stage="multi_agent_pipeline_total", start_time=_pipeline_stage_start)
            _pipe_rec.end_time = _t.perf_counter()
            _pipe_rec.duration_ms = _pipeline_duration_ms
            _pipe_rec.metadata = {"extracted_chars": len(extracted_text)}
            _profiler.stages.append(_pipe_rec)

            # Step 8: Final Report Ready
            if final_report_text:
                full_report = final_report_text.strip()

            if not full_report or "VELNIX INVESTIGATION REPORT" not in full_report:
                raise ValueError("AI workflow succeeded but did not return a valid VELNIX Investigation Report.")
                
            rec = risk_assessment.get("recommendation") or "REVIEW"
            status_map = {
                "APPROVE": "Approved",
                "REVIEW": "Review",
                "INVESTIGATE": "Investigate",
                "REJECT": "Rejected"
            }
            status_val = status_map.get(rec, "Review")
            
            risk_sc = risk_assessment.get("risk_score") or 0
            fraud_sc = fraud_assessment.get("fraud_score") or 0
            
            priority_val = "Low"
            if risk_sc > 70 or fraud_sc > 70:
                priority_val = "High"
            elif risk_sc > 40 or fraud_sc > 40:
                priority_val = "Medium"

            enriched_invoice = {
                **invoice_data,
                "risk_score": risk_sc,
                "fraud_score": fraud_sc,
                "recommendation": rec,
                "status": status_val,
                "priority": priority_val,
                "risk_findings": risk_assessment.get("risk_findings") or [],
                "fraud_findings": fraud_assessment.get("fraud_findings") or [],
                "final_reasoning": risk_assessment.get("final_reasoning") or "",
                "vendor_alerts": vendor_profile.get("alerts") or []
            }

            # ---------------------------------------------------------------
            # Emit profiling report to server logs
            # ---------------------------------------------------------------
            _profile_report = _profiler.finish()
            import logging as _logging
            _logging.getLogger("velnix.profiler").info(
                "\n%s", _profile_report.to_log_lines()
            )
                
            yield {
                "event": "progress",
                "data": json.dumps({
                    "step": "report_ready",
                    "message": "Report ready",
                    "report": full_report,
                    "invoice_data": enriched_invoice,
                    "vendor_profile": vendor_profile,
                    "risk_assessment": risk_assessment,
                    "fraud_assessment": fraud_assessment,
                    "profiling": _profile_report.to_dict(),
                })
            }
            
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Orchestration failure: {str(e)}"})
            }
            return

    return EventSourceResponse(event_generator())


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
