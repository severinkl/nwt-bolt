import aiohttp
import json
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

# WLED CONTROLLER Playlists
# channel 1 foreward 7 reverse 9
# channel 2 foreward 8 reverse 10
# channel 3 foreward 11 reverse 12

class WledController:
    def __init__(self, ip_address, channel=1):
        self.base_url = f"http://{ip_address}/json/state"
        self.headers = {"Content-Type": "application/json"}
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.loop = None
        self.init_event_loop()
        if (channel == 1):
            self.preset_playlist_forward = 7
            self.preset_playlist_reverse = 9
        elif (channel == 2):
            self.preset_playlist_forward = 8
            self.preset_playlist_reverse = 10
        elif (channel == 3):
            self.preset_playlist_forward = 11
            self.preset_playlist_reverse = 12
        else:
            # unsupported
            self.preset_playlist_forward = 0
            self.preset_playlist_reverse = 0

    def init_event_loop(self):
        def run_event_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        thread = threading.Thread(target=run_event_loop, daemon=True)
        thread.start()

    async def set_state(self, on=True, preset=3):
        """
        Set the LED state asynchronously
        :param on: Boolean to turn LED on/off
        :param preset: Preset number for LED configuration (default 3)
        :return: True if successful, False otherwise
        """
        try:
            payload = {
                "on": on,
                "ps": preset
            }
            print(f"Sending request to {self.base_url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        self.base_url,
                        headers=self.headers,
                        json=payload
                ) as response:
                    print(f"Response status: {response.status}")
                    text = await response.text()
                    print(f"Response body: {text}")
                    return response.status == 200

        except Exception as e:
            print(f"Error controlling LED: {e}")
            return False

    def turn_on(self, reverse=False):
        """Turn LED on with specified preset"""
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.set_state(True, self.preset_playlist_reverse if reverse else self.preset_playlist_forward),
                self.loop)

    # def turn_off(self):
    #    """Turn LED off"""
    #    if self.loop:
    #        asyncio.run_coroutine_threadsafe(self.set_state(False), self.loop)
