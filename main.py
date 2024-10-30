import asyncio
import random
import ssl
import json
import time
import uuid
import os
from urllib.parse import urlparse
from rich.console import Console
from rich import print
from loguru import logger
import aiohttp

console = Console()

def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")
    console.print("[bold magenta]BACTIAR 291 - Skrip Dimulai![/bold magenta]", justify="center")
    console.print("[bold green]Selamat datang! Skrip akan segera berjalan...[/bold green]\n", justify="center")

def load_proxy():
    try:
        with open("proxy.json", "r") as file:
            proxy_data = json.load(file)
            return proxy_data.get("proxy_url")
    except FileNotFoundError:
        print("❌ [red]File proxy.json tidak ditemukan! Menggunakan koneksi tanpa proxy.[/red]")
        return None

async def connect_to_wss(user_id, proxy=None):
    device_id = str(uuid.uuid4())
    logger.info(f"Device ID: {device_id} untuk User ID: {user_id}")
    balance = None

    while True:
        try:
            await asyncio.sleep(20)
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, seperti Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy.wynd.network:4650/"
            
            async with aiohttp.ClientSession(headers=custom_headers) as session:
                async with session.ws_connect(uri, ssl=ssl_context, proxy=proxy) as websocket:
                    while True:
                        send_message = json.dumps({"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        print(f"📡 [blue][{user_id}][/blue] Mengirim PING")
                        await websocket.send_str(send_message)
                        
                        response = await websocket.receive()
                        if response.type == aiohttp.WSMsgType.TEXT:
                            message = json.loads(response.data)
                            logger.info(f"Pesan diterima untuk User ID {user_id}: {message}")

                            if "balance" in message.get("result", {}):
                                balance = message["result"]["balance"]
                                print(f"✅ [green][{user_id}] Balance diperbarui: {balance}[/green]")

                            if message.get("action") == "AUTH":
                                auth_response = {
                                    "id": message["id"],
                                    "origin_action": "AUTH",
                                    "result": {
                                        "browser_id": device_id,
                                        "user_id": user_id,
                                        "user_agent": custom_headers['User-Agent'],
                                        "timestamp": int(time.time()),
                                        "device_type": "extension",
                                        "version": "2.5.0"
                                    }
                                }
                                print(f"🔐 [yellow][{user_id}] Mengirim respons AUTH[/yellow]")
                                await websocket.send_str(json.dumps(auth_response))

                            elif message.get("action") == "PONG":
                                pong_response = {"id": message["id"], "origin_action": "PONG"}
                                print(f"🔄 [cyan][{user_id}] PONG diterima, membalas...[/cyan]")
                                await websocket.send_str(json.dumps(pong_response))
                        
                        await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ [red][{user_id}] Kesalahan: {e}[/red]")
            await asyncio.sleep(20)

async def main():
    clear_terminal()
    with open("users.json", "r") as file:
        users_data = json.load(file)
        user_ids = [user["user_id"] for user in users_data["users"]]

    proxy = load_proxy()

    tasks = [asyncio.create_task(connect_to_wss(user_id, proxy)) for user_id in user_ids]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
