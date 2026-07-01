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

import csv
import os
from datetime import datetime

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_LOG_CSV = os.path.join(current_dir, "data", "audit_log.csv")


def log_audit_event(
    invoice_number: str,
    agent: str,
    session_id: str,
    role: str,
    decision: str,
    recommendation: str,
    reason: str,
) -> None:
    """Logs an investigation or security action to the local audit log.

    Args:
        invoice_number: The unique invoice reference code.
        agent: The agent or role initiating the action.
        session_id: The active session identifier.
        role: The user role associated with the session.
        decision: The final decision (e.g. REJECTED, SUCCESS, PENDING).
        recommendation: The AP recommendation.
        reason: The reason or validation error summary.
    """
    os.makedirs(os.path.dirname(AUDIT_LOG_CSV), exist_ok=True)
    file_exists = os.path.exists(AUDIT_LOG_CSV)

    with open(AUDIT_LOG_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                [
                    "Timestamp",
                    "Invoice Number",
                    "Agent",
                    "Session ID",
                    "User Role",
                    "Decision",
                    "Recommendation",
                    "Reason",
                ]
            )

        timestamp = datetime.now().isoformat()
        writer.writerow(
            [
                timestamp,
                invoice_number,
                agent,
                session_id,
                role,
                decision,
                recommendation,
                reason,
            ]
        )
