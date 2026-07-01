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

import sys

# Define dummy credentials class
class DummyCredentials:
    def refresh(self, request):
        pass

# Mock google.auth
try:
    import google.auth
    google.auth.default = lambda **kwargs: (DummyCredentials(), "velnix-dummy-project")
except Exception:
    pass

# Mock google.cloud.logging
try:
    import google.cloud.logging
    class MockClient:
        def __init__(self, *args, **kwargs):
            pass
        def logger(self, name):
            class MockLogger:
                def log_struct(self, data, severity="INFO"):
                    pass
                def log_text(self, text, severity="INFO"):
                    pass
            return MockLogger()
    google.cloud.logging.Client = MockClient
except Exception:
    pass

# Mock google.adk.models.google_llm.Gemini to avoid hitting Gemini API rate limits in tests
try:
    from google.adk.models.google_llm import Gemini
    from google.adk.models.llm_response import LlmResponse
    from google.genai import types

    async def mock_generate_content_async(self, llm_request, stream=False):
        # Extract prompt text
        prompt = ""
        if llm_request.contents:
            parts = []
            for content in llm_request.contents:
                if hasattr(content, "parts") and content.parts:
                    for part in content.parts:
                        if hasattr(part, "text") and part.text:
                            parts.append(part.text)
            prompt = " ".join(parts)

        # Mock reply text
        reply = "I am Velnix, your AI Finance Intelligence Platform. The sky is blue due to Rayleigh scattering."
        if "hi" in prompt.lower() or "hello" in prompt.lower():
            reply = "Hello! I am Velnix, how can I assist you today?"

        mock_part = types.Part(text=reply)
        mock_content = types.Content(role="model", parts=[mock_part])
        mock_candidate = types.Candidate(content=mock_content, finish_reason="STOP")
        mock_response = types.GenerateContentResponse(
            candidates=[mock_candidate]
        )
        yield LlmResponse.create(mock_response)

    Gemini.generate_content_async = mock_generate_content_async
except Exception as e:
    pass
