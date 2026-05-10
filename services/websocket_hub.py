import asyncio
import json
from collections import defaultdict


class WebsocketHub:
    def __init__(self):
        self._clients = defaultdict(set)
        self._snapshots = {}
        self._loop = None

    def set_loop(self, loop):
        self._loop = loop

    async def register(self, user_id, websocket):
        self._clients[user_id].add(websocket)

    async def unregister(self, user_id, websocket):
        if user_id in self._clients:
            self._clients[user_id].discard(websocket)
            if not self._clients[user_id]:
                del self._clients[user_id]

    def get_latest_snapshot(self, user_id):
        return self._snapshots.get(user_id)

    def publish(self, user_id, payload):
        self._snapshots[user_id] = payload
        clients = list(self._clients.get(user_id, set()))
        if not clients:
            return

        async def _broadcast():
            dead = []
            for client in clients:
                try:
                    await client.send(json.dumps(payload))
                except Exception:
                    dead.append(client)
            for client in dead:
                await self.unregister(user_id, client)

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_broadcast())
        except RuntimeError:
            if self._loop:
                asyncio.run_coroutine_threadsafe(_broadcast(), self._loop)


websocket_hub = WebsocketHub()
