"""Minimal A2A 1.0 JSON-RPC client for the local booking service."""

import argparse
import json
import os
from uuid import uuid4

import httpx
from dotenv import load_dotenv


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("message")
    parser.add_argument(
        "--context-id", help="Reuse the contextId returned by the previous response"
    )
    args = parser.parse_args()
    url = os.getenv("BOOKING_A2A_URL", "http://127.0.0.1:8001").rstrip("/")
    headers = {"A2A-Version": "1.0"}
    if os.getenv("BOOKING_API_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["BOOKING_API_TOKEN"]
    message = {"messageId": str(uuid4()), "role": "ROLE_USER", "parts": [{"text": args.message}]}
    if args.context_id:
        message["contextId"] = args.context_id
    with httpx.Client(timeout=120, headers=headers) as client:
        response = client.post(
            url + "/",
            json={
                "jsonrpc": "2.0",
                "id": str(uuid4()),
                "method": "SendMessage",
                "params": {"message": message},
            },
        )
        response.raise_for_status()
        data = response.json()
        print(json.dumps(data, indent=2))
        if "error" in data:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
