"""Exercises the real ADK runner/tools without a paid API call."""

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types


class ScriptedModel(BaseLlm):
    model: str = "scripted-offline-test"

    async def generate_content_async(self, llm_request, stream=False):
        last = llm_request.contents[-1]
        if any(p.function_response for p in last.parts):
            yield LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(text="Please review the proposal and confirm using the client.")
                    ],
                )
            )
            return
        text = " ".join(p.text or "" for p in last.parts)
        if "prepare" in text.lower():
            part = types.Part(
                function_call=types.FunctionCall(
                    name="propose_booking",
                    args={
                        "customer_name": "Atri",
                        "start": "2030-01-08T10:00:00+05:30",
                        "duration_minutes": 30,
                        "service_name": "consultation",
                    },
                )
            )
        else:
            part = types.Part(function_call=types.FunctionCall(name="booking_policy", args={}))
        yield LlmResponse(content=types.Content(role="model", parts=[part]))
