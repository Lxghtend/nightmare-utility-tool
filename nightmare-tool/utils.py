import time
import asyncio
import threading
import pyperclip
import configparser
from wizwalker.memory import Window
from wizwalker.errors import HookNotActive
from wizwalker import ClientHandler, Client, XYZ
from wizwalker.constants import Keycode, Primitive
from wizwalker.memory.memory_objects.enums import WindowFlags

from worlds_collide import WorldsCollideTP

class Utils():
    def __init__(self):
        self.handler = ClientHandler()
        self.config_parser = configparser.ConfigParser()
        self.foreground_client = None

        threading.Thread(target=self.update_foreground_client, daemon=True).start()
        threading.Thread(target=lambda: asyncio.run(self.update_hooked_text()), daemon=True).start()

    def update_foreground_client(self):
        while True:
            if (client := self.handler.get_foreground_client()):
                self.foreground_client = client
            time.sleep(0.1)

    async def update_hooked_text(self):
        async def write_window_rectangle(window: Window, x1: int, y1: int, x2: int, y2: int):
            await window.write_value_to_offset(160, x1, Primitive.int32)
            await window.write_value_to_offset(164, y1, Primitive.int32)
            await window.write_value_to_offset(168, x2, Primitive.int32)
            await window.write_value_to_offset(172, y2, Primitive.int32)

        while True:
            for client in self.get_open_clients():
                try:
                    window = (await client.root_window.get_windows_with_name('txtTestRealmText'))[0]

                    await write_window_rectangle(window, 10, 146, 153, 165)

                    await window.write_maybe_text('HOOKED')
                    await window.write_flags(WindowFlags.visible)

                except (IndexError, HookNotActive):
                    pass

            await asyncio.sleep(1)

    def read_config(self) -> dict[str, bool]:
        settings = {}
        self.config_parser.read("config.ini")

        # [General]
        settings["always_on_top"] = self.config_parser.getboolean("General", "always_on_top", fallback=True)
        settings["enable_clients_tab"] = self.config_parser.getboolean("General", "enable_clients_tab", fallback=True)
        settings["use_dungeon_theme"] = self.config_parser.getboolean("General", "use_dungeon_theme", fallback=True)

        # [Keybinds]
        settings["handle_xyz_sync"] = self.config_parser.get("Keybinds", "handle_xyz_sync", fallback="F3")
        settings["toggle_speedhack"] = self.config_parser.get("Keybinds", "toggle_speedhack", fallback="F4")
        settings["toggle_freecam"] = self.config_parser.get("Keybinds", "toggle_freecam", fallback="F5")
        settings["handle_freecam_teleport"] = self.config_parser.get("Keybinds", "handle_freecam_teleport", fallback="F6")
        settings["toggle_auto_dialogue"] = self.config_parser.get("Keybinds", "toggle_auto_dialogue", fallback="F7")

        return settings

    async def is_visible_by_path(self, base_window: Window, path: list[str]):
        if window := await self.window_from_path(base_window, path):
            return await window.is_visible()
        return False

    async def window_from_path(self, base_window: Window, path: list[str]) -> Window:
        if not path:
            return base_window
        for child in await base_window.children():
            if await child.name() == path[0]:
                if found_window := await self.window_from_path(child, path[1:]):
                    return found_window
        return False

    def get_open_clients(self) -> list[Client]:
        self.handler.remove_dead_clients()

        clients = self.handler.get_new_clients()
        if not clients:
            clients = self.handler.get_ordered_clients()
        return clients

    def rename_clients(self):
        clients = self.handler.get_new_clients()
        if not clients:
            clients = self.handler.get_ordered_clients()

        for i, client in enumerate(clients, 1):
            client.title = "Client: " + str(i)

    async def activate_hooks(self, client: Client): # TODO: rework logic and make this stop getting clients from get_open_clients
        await client.activate_hooks()
        print(f"{client.title} hooks activated.")

    async def deactivate_hooks(self, client: Client): # TODO: rework logic and make this stop getting clients from get_open_clients
        hooked_window = (await client.root_window.get_windows_with_name('txtTestRealmText'))[0]
        await hooked_window.write_flags(WindowFlags.disabled)

        await client.close()
        print(f"{client.title} hooks deactivated.")

    async def handle_auto_dialogue(self, client: Client):
        try:
            print(f"{client.title} auto dialogue activated.")

            while True:
                if await self.is_visible_by_path(client.root_window, ['WorldView', 'wndDialogMain', 'btnRight']):
                    await client.send_key(Keycode.SPACEBAR)
                await asyncio.sleep(0.5)

        except asyncio.CancelledError:
                print(f"{client.title} auto dialogue deactivated.")

    async def handle_speedhack(self, client: Client):
        try:
            print(f"{client.title} speedhack activated.")

            while True:
                await client.client_object.write_speed_multiplier(400)
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            await client.client_object.write_speed_multiplier(1)
            print(f"{client.title} speedhack deactivated.")

    async def handle_freecam(self):
        client = self.foreground_client
        if client:
            try:
                while True:
                    if not await client.game_client.is_freecam():
                        await client.camera_freecam()
                        print(f"[TOGGLE] Freecam started.")

                    await asyncio.sleep(0)

            except asyncio.CancelledError:
                camera = await client.game_client.free_camera_controller()
                camera_pos = await camera.position()

                await client.camera_elastic()
                # print(f"[TOGGLE] Freecam cancelled.")

                return camera_pos

    async def freecam_teleport(self, camera_pos: XYZ):
        client = self.foreground_client
        if client:
            await client.teleport(camera_pos, wait_on_inuse=True, purge_on_after_unuser_fixer=True)
            print(f"{client.title} teleported to freecam position.")

    async def xyz_sync(self):
        client = self.foreground_client
        if client:
            client_position = await client.body.position()

            for teleporting_client in self.handler.get_ordered_clients():
                if not teleporting_client is client:
                    await teleporting_client.teleport(client_position)

    async def copy_position(self):
        client = self.foreground_client
        if client:
            current_pos = await client.body.position()

            print(f"{client.title} copied current position at {current_pos}.")
            pyperclip.copy(f'XYZ({current_pos.x}, {current_pos.y}, {current_pos.z})')

    async def handle_basic_teleport(self, location_x: float, location_y: float, location_z: float, yaw: float = None):
        client = self.foreground_client
        if client:
            await client.teleport(XYZ(location_x, location_y, location_z), yaw)

    async def entity_teleport(self, entity_name: str):
        client = self.foreground_client
        if client:
            entity = await client.get_base_entities_with_name(entity_name)
            if not entity:
                print(f"{client.title} did not find {entity_name}")
                return

            await WorldsCollideTP(client, await entity[0].location())
            print(f"{client.title} teleported to {entity_name}.")

    async def wait_for_range(self, client: Client):
        while True:
            if self.is_visible_by_path(client.root_window, ['WorldView', 'NPCRangeWin']):
                return
            await asyncio.sleep(0.1)

    async def break_idols(self):
        idol_positions = [(3690.726, -15581.208, 411.292), (1954.191, -15049.565, 405.440),
                          (-2226.922, -16031.020, 400.254), (-3522.000, -15288.324, 410.040)]

        client = self.foreground_client
        if client:
            for idol in idol_positions:
                await client.teleport(XYZ(*idol))
                await self.wait_for_range(client)
                await asyncio.sleep(0.1)
                await client.send_key(Keycode.X)

    async def check_broken_dream(self, client) -> bool:
        client_position = await client.body.position()
        if client_position == XYZ(-148.000, -11751.999, 436.000):
            return True

        return False

    async def dreamwater(self):
        sleeper_positions = [(-277.11358642578125, -25830.056640625, 332.819091796875),
            (-879.7774047851562, -27695.830078125, 332.819091796875),
            (631.965087890625, -27503.0234375, 332.819091796875)]

        dreamwater_positions = [
            (17690.548828125, -19879.84765625, 347.0538330078125),
            (14345.3720703125, -22480.83203125, 337.429443359375),
            (9410.283203125, -19600.91796875, 337.4325866699219),
            (13975.2001953125, -28369.369140625, 337.6564025878906),
            (9534.2197265625, -35531.0859375, 337.2992248535156),
            (1276.478271484375, -17722.1328125, 338.7263488769531),
            (2115.623779296875, -21331.74609375, 337.7518310546875),
            (4404.2236328125, -22432.185546875, 337.8857421875),
            (-2705.47509765625, -18066.244140625, 337.83892822265625),
            (-7566.29443359375, -22091.8515625, 337.05633544921875),
            (-10900.3154296875, -24096.162109375, 337.7960205078125),
            (-14106.8681640625, -17755.119140625, 337.7401123046875),
            (-15030.1728515625, -19808.513671875, 336.02862548828125),
            (-18101.087890625, -20287.6953125, 338.0257568359375),
            (-3082.203369140625, -26576.857421875, 385.1693420410156),
            (-6698.95458984375, -26106.42578125, 337.7475891113281),
            (-14606.390625, -30870.869140625, 337.50274658203125),
            (-16999.693359375, -33679.921875, 338.0223083496094),
            (-1700.6639404296875, -35839.40625, 339.056640625),
            (4383.9609375, -32568.654296875, 337.9153137207031),
            (6367.15478515625, -29292.587890625, 339.1195068359375),
            (6132.337890625, -27502.78515625, 337.72210693359375),
            (10352.8310546875, -31497.4609375, 337.85174560546875),
            (15357.1357421875, -33545.8125, 338.0357666015625),
            (238.40765380859375, -29302.095703125, 385.3066711425781),
            (12152.876953125, -19342.18359375, 380.29766845703125),
            (-2404.990234375, -32785.734375, 376.5253601074219),
        ]

        client = self.foreground_client
        if client:
            for dreamwater in dreamwater_positions:
                await client.teleport(XYZ(*dreamwater))
                await self.wait_for_range(client)
                await asyncio.sleep(1)
                await client.send_key(Keycode.X)

                if await self.check_broken_dream(client):
                    return

                for sleeper in sleeper_positions:
                    await client.teleport(XYZ(*sleeper))
                    await self.wait_for_range(client)
                    await asyncio.sleep(1)
                    await client.send_key(Keycode.X)

                    if await self.check_broken_dream(client):
                        return
