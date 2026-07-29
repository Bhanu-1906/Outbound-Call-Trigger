from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server-app")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Loaded from Render environment variables ──────────────────────────────────
LIVEKIT_URL        = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY    = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

@app.get("/")
def health():
    return {"status": "running"}


@app.post("/make-call")
async def make_call_list(numbers: list[str]):
    agent_name = "greatwhite-agent"

    if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
        raise HTTPException(status_code=500, detail="LiveKit env variables are not set.")

    if len(numbers) != len(account_ids):
        raise HTTPException(status_code=400, detail="numbers and account_ids must be same length")

    logger.info(f"Inside make_call_list | numbers={numbers} | account_ids={account_ids}")

    try:
        lkapi = api.LiveKitAPI(
            url=LIVEKIT_URL,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
        )

        for number, account_id in zip(numbers, account_ids):
            full_number = "+91" + number
            room_name   = f"{full_number}-{agent_name}-room"
            room_name   = room_name.encode("utf-8", errors="ignore").decode("utf-8")
            metadata    = json.dumps({"phone_number": full_number})

            await lkapi.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(
                    agent_name=agent_name, room=room_name, metadata=metadata
                )
            )
            await lkapi.agent_dispatch.list_dispatch(room_name=room_name)
            logger.info(f"Dispatch created for {full_number}")

        await lkapi.aclose()
        return {"status": "Call initiated successfully", "count": len(numbers)}

    except Exception as e:
        logger.error(f"Error making call list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

