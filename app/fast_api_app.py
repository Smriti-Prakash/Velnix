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


@app.post("/api/upload")
async def upload_invoice(file: UploadFile = File(...)):
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pdf", ".png", ".jpg", ".jpeg"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a PDF, PNG, or JPEG."
        )

    # Validate file size (10MB limit)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds the 10MB limit."
        )

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

        if ext == ".pdf":
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
        try:
            from google.adk.agents.run_config import RunConfig, StreamingMode
            from google.adk.runners import Runner
            from app.agent import root_agent
            from app.app_utils import services
            from google.genai import types
            
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
            
            # Run the synchronous generator in a background thread and use a queue
            q = asyncio.Queue()
            
            def worker():
                try:
                    events = runner.run(
                        new_message=message,
                        user_id="anonymous",
                        session_id=session.id,
                        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
                    )
                    for event in events:
                        loop.call_soon_threadsafe(q.put_nowait, ("event", event))
                    loop.call_soon_threadsafe(q.put_nowait, ("done", None))
                except Exception as ex:
                    loop.call_soon_threadsafe(q.put_nowait, ("error", ex))
            
            threading.Thread(target=worker, daemon=True).start()
            
            full_report = ""
            seen_steps = set()
            
            # Collect response payloads to return structured data to the frontend
            invoice_data = {}
            vendor_profile = {}
            risk_assessment = {}
            fraud_assessment = {}
            final_report_text = ""
            
            while True:
                msg_type, val = await q.get()
                if msg_type == "done":
                    break
                elif msg_type == "error":
                    yield {
                        "event": "error",
                        "data": json.dumps({"message": f"ADK workflow failure: {str(val)}"})
                    }
                    return
                
                event = val
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
                                elif resp.name == "get_vendor_profile":
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
                
            yield {
                "event": "progress",
                "data": json.dumps({
                    "step": "report_ready",
                    "message": "Report ready",
                    "report": full_report,
                    "invoice_data": enriched_invoice,
                    "vendor_profile": vendor_profile,
                    "risk_assessment": risk_assessment,
                    "fraud_assessment": fraud_assessment
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
