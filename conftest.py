import os
import asyncio

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
os.environ["AIOCOAP_SERVER_TRANSPORT"] = "simplesocketserver"