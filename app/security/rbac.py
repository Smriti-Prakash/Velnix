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


class AuthorizationError(Exception):
    """Custom exception raised when a user or role is unauthorized to perform an action."""

    pass


ROLES_PERMISSIONS = {
    "Finance Analyst": {"view_profile", "find_duplicate", "analyze_invoice"},
    "Finance Manager": {
        "view_profile",
        "find_duplicate",
        "analyze_invoice",
        "submit_investigation_result",
    },
    "Administrator": {
        "view_profile",
        "find_duplicate",
        "analyze_invoice",
        "submit_investigation_result",
        "list_pending_invoices",
        "view_audit_logs",
    },
}


def verify_permission(role: str, action: str) -> None:
    """Verifies if the given role is authorized to perform the action.

    Args:
        role: The role name (Finance Analyst, Finance Manager, Administrator).
        action: The target action/tool name.

    Raises:
        AuthorizationError: If the role is unauthorized or unknown.
    """
    if role not in ROLES_PERMISSIONS:
        raise AuthorizationError(f"Access Denied: Unknown role '{role}'.")

    if action not in ROLES_PERMISSIONS[role]:
        raise AuthorizationError(
            f"Access Denied: Role '{role}' is not authorized to perform action '{action}'."
        )
