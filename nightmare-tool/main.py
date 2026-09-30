import os
import json
import sys
import ctypes
import asyncio
import keyboard
from qasync import QEventLoop, asyncSlot
from PyQt6.QtWidgets import QApplication, QLabel, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QPushButton, QSizePolicy, QCheckBox, QDialog, QMessageBox
from PyQt6.QtCore import QTimer, Qt, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices

from utils import Utils
from themes import Themes

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shared"))
from updater import check_for_update, trigger_update

class HooksTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.hooks_group_layout = QVBoxLayout()
        self.setLayout(self.hooks_group_layout)
        # --------------------------- #

        # ----- Creating Hooks Group ----- #
        self.hooks_group = QGroupBox("Hooks")
        self.hooks_tab_layout = QVBoxLayout()
        self.hooks_group.setLayout(self.hooks_tab_layout)
        # -------------------------------- #

        # ----- Rename Clients Button ----- #
        rename_clients_button = QPushButton("Rename Clients")

        rename_clients_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        #rename_clients_button.setMaximumHeight(50)
        rename_clients_button.setMinimumHeight(50)

        rename_clients_button.clicked.connect(lambda: asyncio.create_task(self.rename_clients_wrapper()))

        self.hooks_tab_layout.addWidget(rename_clients_button)
        # --------------------------------- #

        self.hooks_tab_layout.addStretch() # makes rename button go to top

        # ----- Available Clients Checkboxes ----- #
        self.hooks_checkboxes = QGroupBox("Available Clients")
        self.hooks_checkboxes_layout = QVBoxLayout()

        self.client_checkboxes = []
        QTimer.singleShot(0, lambda: asyncio.create_task(self.update_client_checkboxes()))

        self.hooks_checkboxes.setLayout(self.hooks_checkboxes_layout)
        self.hooks_tab_layout.addWidget(self.hooks_checkboxes)
        # ---------------------------------------- #

        # ----- Creating No Clients Found Label ----- #
        self.no_clients_found_label = QLabel("No clients found.")
        self.hooks_checkboxes_layout.addWidget(self.no_clients_found_label)
        self.no_clients_found_label.hide()
        # ------------------------------------------- #

        # ----- Activate Hooks Button ----- #
        activate_hooks_button = QPushButton("Activate Hooks")

        activate_hooks_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #activate_hooks_button.setMaximumHeight(50)
        activate_hooks_button.setMinimumHeight(50)

        activate_hooks_button.clicked.connect(lambda: asyncio.create_task(self.activate_hooks_wrapper()))

        self.hooks_tab_layout.addWidget(activate_hooks_button)
        # --------------------------------- #

        # ----- Deactivate Hooks Button ----- #
        deactivate_hooks_button = QPushButton("Deactivate Hooks")

        deactivate_hooks_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #deactivate_hooks_button.setMaximumHeight(50)
        deactivate_hooks_button.setMinimumHeight(50)

        deactivate_hooks_button.clicked.connect(lambda: asyncio.create_task(self.deactivate_hooks_wrapper()))

        self.hooks_tab_layout.addWidget(deactivate_hooks_button)
        # ----------------------------------- #

        self.hooks_group_layout.addWidget(self.hooks_group)

    async def rename_clients_wrapper(self):
        print(f"[HOOKS] Rename Clients pressed.")

        self.utils.rename_clients()

    async def activate_hooks_wrapper(self):
        print("[HOOKS] Activate Hooks pressed.")

        clients_to_hook = []
        for client_checkbox in self.client_checkboxes:
            if client_checkbox.isChecked():
                client = client_checkbox.property("client")
                clients_to_hook.append(client)

        await asyncio.gather(*[(self.utils.activate_hooks(client)) for client in clients_to_hook])

        for client in clients_to_hook:
            if client.process_id not in {hooked_client.process_id for hooked_client in self.hooked_clients}:
                self.hooked_clients.append(client)

    async def deactivate_hooks_wrapper(self):
        print("[HOOKS] Deactivate Hooks pressed.")
        for client_checkbox in self.client_checkboxes:
            if client_checkbox.isChecked():
                client = client_checkbox.property("client")

                for hooked_client in self.hooked_clients:
                    if client == hooked_client:
                        self.hooked_clients.remove(client)

                await self.utils.deactivate_hooks(client)

    async def update_client_checkboxes(self):
        while True:
            clients = self.utils.get_open_clients()
            existing_processes = [client_checkbox.property("client").process_id for client_checkbox in self.client_checkboxes]

            # Remove Client Checkboxes that don't exist
            for client_checkbox in self.client_checkboxes[:]:
                if client_checkbox.property("client").process_id not in [client.process_id for client in clients]:
                    self.hooks_checkboxes_layout.removeWidget(client_checkbox)
                    client_checkbox.deleteLater()

                    self.client_checkboxes.remove(client_checkbox)

            for client_checkbox in self.client_checkboxes:
                client_process_id = client_checkbox.property("client").process_id # process id that is stored
                for client in clients:
                    if client.process_id == client_process_id:
                        if client_checkbox.text() != client.title:
                            client_checkbox.setText(client.title)
                            client_checkbox.setProperty("client", client)

            # Create Client Checkboxes
            for client in clients:
                if client.process_id not in existing_processes:
                    client_checkbox = QCheckBox(client.title)
                    client_checkbox.setProperty("client", client)

                    self.client_checkboxes.append(client_checkbox)

                    self.hooks_checkboxes_layout.addWidget(client_checkbox)

            if self.client_checkboxes:
                self.no_clients_found_label.hide()

            if not self.client_checkboxes:
                self.no_clients_found_label.show()

            await asyncio.sleep(1)

class ClientsTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.clients_group_layout = QVBoxLayout()
        self.setLayout(self.clients_group_layout)
        # --------------------------- #

        # ----- Creating Clients Group ----- #
        self.clients_group = QGroupBox("Clients")
        self.clients_tab_layout = QVBoxLayout()
        self.clients_group.setLayout(self.clients_tab_layout)
        # ---------------------------------- #

        self.clients_group_layout.addWidget(self.clients_group)

        self.client_frames = {}  # key: client.process_id (dict), value: QFrame

        QTimer.singleShot(0, lambda: asyncio.create_task(self.update_hooked_client_info()))

    async def update_hooked_client_info(self):
        while True:
            # Remove clients that are no longer hooked
            for client_process_id in list(self.client_frames.keys()):
                if all(client_process_id != client.process_id for client in self.hooked_clients): # unreadable, i know
                    client_frame_info = self.client_frames.pop(client_process_id)
                    client_frame = client_frame_info['frame']
                    self.clients_tab_layout.removeWidget(client_frame)
                    client_frame.deleteLater()

            # Add new hooked clients
            for client in self.hooked_clients:
                if client.process_id not in self.client_frames:
                    client_frame = QGroupBox(client.title)
                    client_frame_layout = QVBoxLayout()

                    level_label = QLabel(f"Level: {await client.stats.reference_level()}")
                    health_label = QLabel(f"Health: {await client.stats.current_hitpoints()}/{await client.stats.max_hitpoints()}")
                    mana_label = QLabel(f"Mana: {await client.stats.current_mana()}/{await client.stats.max_mana()}")
                    energy_label = QLabel(f"Energy: {await client.current_energy()}/{await client.stats.energy_max() + await client.stats.bonus_energy()}")
                    position_label = QLabel(f"Position: {await client.body.position()}")
                    yaw_label = QLabel(f"Yaw: {await client.body.yaw()}")

                    client_frame_layout.addWidget(level_label)
                    client_frame_layout.addWidget(health_label)
                    client_frame_layout.addWidget(mana_label)
                    client_frame_layout.addWidget(energy_label)
                    client_frame_layout.addWidget(position_label)
                    client_frame_layout.addWidget(yaw_label)

                    self.client_frames[client.process_id] = {
                        'frame': client_frame,
                        'labels': {
                            'level': level_label,
                            'health': health_label,
                            'mana': mana_label,
                            'energy': energy_label,
                            'position': position_label,
                            'yaw': yaw_label
                        }
                    }

                    client_frame.setLayout(client_frame_layout)

                    #self.client_frames[client.title] = client_frame # sets the key (title) to the frame
                    self.clients_tab_layout.addWidget(client_frame, alignment=Qt.AlignmentFlag.AlignTop)

                else:
                    client_labels = self.client_frames[client.process_id]['labels']
                    client_labels['level'].setText(f"Level: {await client.stats.reference_level()}")
                    client_labels['health'].setText(f"Health: {await client.stats.current_hitpoints()}/{await client.stats.max_hitpoints()}")
                    client_labels['mana'].setText(f"Mana: {await client.stats.current_mana()}/{await client.stats.max_mana()}")
                    client_labels['energy'].setText(f"Energy: {await client.current_energy()}/{await client.stats.energy_max() + await client.stats.bonus_energy()}")
                    client_labels['position'].setText(f"Position: {await client.body.position()}")
                    client_labels['yaw'].setText(f"Yaw: {await client.body.yaw()}")

            await asyncio.sleep(1)

class PortalsTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.portals_group_layout = QVBoxLayout()
        self.setLayout(self.portals_group_layout)
        # --------------------------- #

        # ----- Creating Inside Group ----- #
        self.inside_group = QGroupBox("Inside")
        self.inside_tab_layout = QGridLayout()

        self.inside_group.setLayout(self.inside_tab_layout)
        self.portals_group_layout.addWidget(self.inside_group)
        # ---------------------------------- #

        # ----- Inside Yellow Portal Button ----- #
        inside_yellow_portal_button = QPushButton("Inside Yellow Portal")

        inside_yellow_portal_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        inside_yellow_portal_button.setMinimumHeight(50)

        inside_yellow_portal_button.clicked.connect(self.handle_inside_yellow_portal)

        self.inside_tab_layout.addWidget(inside_yellow_portal_button, 0, 0)
        # --------------------------------------- #

        # ----- Inside Blue Portal Button ----- #
        inside_blue_portal_button = QPushButton("Inside Blue Portal")

        inside_blue_portal_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        inside_blue_portal_button.setMinimumHeight(50)

        inside_blue_portal_button.clicked.connect(self.handle_inside_blue_portal)

        self.inside_tab_layout.addWidget(inside_blue_portal_button, 0, 1)
        # --------------------------------------- #

        # ----- Inside Green Portal Button ----- #
        inside_green_portal_button = QPushButton("Inside Green Portal")

        inside_green_portal_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        inside_green_portal_button.setMinimumHeight(50)

        inside_green_portal_button.clicked.connect(self.handle_inside_green_portal)

        self.inside_tab_layout.addWidget(inside_green_portal_button, 1, 0)
        # --------------------------------------- #

        # ----- Inside Pink Portal Button ----- #
        inside_pink_portal_button = QPushButton("Inside Pink Portal")

        inside_pink_portal_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        inside_pink_portal_button.setMinimumHeight(50)

        inside_pink_portal_button.clicked.connect(self.handle_inside_pink_portal)

        self.inside_tab_layout.addWidget(inside_pink_portal_button, 1, 1)
        # --------------------------------------- #

        # ----- Creating Outside Group ----- #
        self.outside_group = QGroupBox("Outside")
        self.outside_tab_layout = QGridLayout()

        self.outside_group.setLayout(self.outside_tab_layout)
        self.portals_group_layout.addWidget(self.outside_group)
        # ---------------------------------- #

        # ----- Outside Yellow Portal Button ----- #
        outside_yellow_portal_button = QPushButton("Outside Yellow Portal")

        outside_yellow_portal_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        outside_yellow_portal_button.setMinimumHeight(50)

        outside_yellow_portal_button.clicked.connect(self.handle_outside_yellow_portal)

        self.outside_tab_layout.addWidget(outside_yellow_portal_button, 0, 0)
        # --------------------------------------- #

        # ----- Outside Blue Portal Button ----- #
        outside_blue_portal_button = QPushButton("Outside Blue Portal")

        outside_blue_portal_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        outside_blue_portal_button.setMinimumHeight(50)

        outside_blue_portal_button.clicked.connect(self.handle_outside_blue_portal)

        self.outside_tab_layout.addWidget(outside_blue_portal_button, 0, 1)
        # --------------------------------------- #

        # ----- Outside Green Portal Button ----- #
        outside_green_portal_button = QPushButton("Outside Green Portal")

        outside_green_portal_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        outside_green_portal_button.setMinimumHeight(50)

        outside_green_portal_button.clicked.connect(self.handle_outside_green_portal)

        self.outside_tab_layout.addWidget(outside_green_portal_button, 1, 0)
        # --------------------------------------- #

        # ----- Outside Pink Portal Button ----- #
        outside_pink_portal_button = QPushButton("Outside Pink Portal")

        outside_pink_portal_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        outside_pink_portal_button.setMinimumHeight(50)

        outside_pink_portal_button.clicked.connect(self.handle_outside_pink_portal)

        self.outside_tab_layout.addWidget(outside_pink_portal_button, 1, 1)
        # --------------------------------------- #

    @asyncSlot()
    async def handle_inside_yellow_portal(self):
        print("[PORTALS] Inside Yellow Portal pressed.")

        await self.utils.handle_basic_teleport(15347.999, -14231.999, 328.000)

    @asyncSlot()
    async def handle_inside_blue_portal(self):
        print("[PORTALS] Inside Blue Portal pressed.")

        await self.utils.handle_basic_teleport(15357.581, -38994.316, 335.450)

    @asyncSlot()
    async def handle_inside_green_portal(self):
        print("[PORTALS] Inside Green Portal pressed.")

        await self.utils.handle_basic_teleport(-15682.201, -39139.546, 336.191)

    @asyncSlot()
    async def handle_inside_pink_portal(self):
        print("[PORTALS] Inside Pink Portal pressed.")

        await self.utils.handle_basic_teleport(-15839.999, -14227.999, 328.000)

    @asyncSlot()
    async def handle_outside_yellow_portal(self):
        print("[PORTALS] Outside Yellow Portal pressed.")

        await self.utils.handle_basic_teleport(5806.903, -14577.535, 414.030)

    @asyncSlot()
    async def handle_outside_blue_portal(self):
        print("[PORTALS] Outside Blue Portal pressed.")

        await self.utils.handle_basic_teleport(5843.190, -15631.522, 410.240)

    @asyncSlot()
    async def handle_outside_green_portal(self):
        print("[PORTALS] Outside Green Portal pressed.")

        await self.utils.handle_basic_teleport(-5935.393, -15682.678, 408.350)

    @asyncSlot()
    async def handle_outside_pink_portal(self):
        print("[PORTALS] Outside Pink Portal pressed.")

        await self.utils.handle_basic_teleport(-5839.460, -14560.791, 410.588)


class BossesTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.bosses_group_layout = QVBoxLayout()
        self.setLayout(self.bosses_group_layout)
        # --------------------------- #

        # ----- Creating Bosses Group ----- #
        self.bosses_group = QGroupBox("Bosses")
        self.bosses_tab_layout = QVBoxLayout()

        self.bosses_group.setLayout(self.bosses_tab_layout)
        self.bosses_group_layout.addWidget(self.bosses_group)
        # ---------------------------------- #

        # ----- Dragon Button ----- #
        dragon_button = QPushButton("Dragon")

        dragon_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        dragon_button.setMinimumHeight(50)

        dragon_button.clicked.connect(self.handle_dragon)

        self.bosses_tab_layout.addWidget(dragon_button)
        # ------------------------- #

        # ----- Krok Button ----- #
        krok_button = QPushButton("Krok")

        krok_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        krok_button.setMinimumHeight(50)

        krok_button.clicked.connect(self.handle_krok)

        self.bosses_tab_layout.addWidget(krok_button)
        # ----------------------- #

        # ----- Malus Button ----- #
        malus_button = QPushButton("Malus")

        malus_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        malus_button.setMinimumHeight(50)

        malus_button.clicked.connect(self.handle_malus)

        self.bosses_tab_layout.addWidget(malus_button)
        # ------------------------ #

    @asyncSlot()
    async def handle_dragon(self):
        print("[BOSSES] Dragon pressed.")

        await self.utils.handle_basic_teleport(15482.805, -27428.171, 335.950)

    @asyncSlot()
    async def handle_krok(self):
        print("[BOSSES] Krok pressed.")

        await self.utils.handle_basic_teleport(-15624.958, -26149.779, 337.719)

    @asyncSlot()
    async def handle_malus(self):
        print("[BOSSES] Malus pressed.")

        await self.utils.handle_basic_teleport(-1544.024, -28651.068, 337.379)


class PrayerTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.prayer_group_layout = QVBoxLayout()
        self.setLayout(self.prayer_group_layout)
        # --------------------------- #

        # ----- Creating Prayer Wheels Group ----- #
        self.prayer_group = QGroupBox("Prayer Wheels")
        self.prayer_tab_layout = QVBoxLayout()

        self.prayer_group.setLayout(self.prayer_tab_layout)
        self.prayer_group_layout.addWidget(self.prayer_group)
        # ---------------------------------- #

        # ----- Dragon School Wheel Button ----- #
        dragon_school_wheel_button = QPushButton("Dragon School Wheel")

        dragon_school_wheel_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        dragon_school_wheel_button.setMinimumHeight(50)

        dragon_school_wheel_button.clicked.connect(self.handle_dragon_school_wheel)

        self.prayer_tab_layout.addWidget(dragon_school_wheel_button)
        # -------------------------------------- #

        # ----- Dragon Wildlife Wheel Button ----- #
        dragon_wildlife_wheel_button = QPushButton("Dragon Wildlife Wheel")

        dragon_wildlife_wheel_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        dragon_wildlife_wheel_button.setMinimumHeight(50)

        dragon_wildlife_wheel_button.clicked.connect(self.handle_dragon_wildlife_wheel)

        self.prayer_tab_layout.addWidget(dragon_wildlife_wheel_button)
        # ---------------------------------------- #

        # ----- Krok School Wheel Button ----- #
        krok_school_wheel_button = QPushButton("Krok School Wheel")

        krok_school_wheel_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        krok_school_wheel_button.setMinimumHeight(50)

        krok_school_wheel_button.clicked.connect(self.handle_krok_school_wheel)

        self.prayer_tab_layout.addWidget(krok_school_wheel_button)
        # ------------------------------------ #

        # ----- Krok Astral Wheel Button ----- #
        krok_astral_wheel_button = QPushButton("Krok Astral Wheel")

        krok_astral_wheel_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        krok_astral_wheel_button.setMinimumHeight(50)

        krok_astral_wheel_button.clicked.connect(self.handle_krok_astral_wheel)

        self.prayer_tab_layout.addWidget(krok_astral_wheel_button)
        # ------------------------------------ #

    @asyncSlot()
    async def handle_dragon_school_wheel(self):
        print("[PRAYER] Dragon School Wheel pressed.")

        await self.utils.handle_basic_teleport(15999.055, -17869.972, 337.223)

    @asyncSlot()
    async def handle_dragon_wildlife_wheel(self):
        print("[PRAYER] Dragon Wildlife Wheel pressed.")

        await self.utils.handle_basic_teleport(15142.157, -35529.484, 337.710)

    @asyncSlot()
    async def handle_krok_school_wheel(self):
        print("[PRAYER] Krok School Wheel pressed.")

        await self.utils.handle_basic_teleport(-16375.003, -35788.078, 337.454)

    @asyncSlot()
    async def handle_krok_astral_wheel(self):
        print("[PRAYER] Krok Astral Wheel pressed.")

        await self.utils.handle_basic_teleport(-15510.254, -18039.664, 337.702)


class AutomationTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.automation_group_layout = QVBoxLayout()
        self.setLayout(self.automation_group_layout)
        # --------------------------- #

        # ----- Creating Automation Group ----- #
        self.automation_group = QGroupBox("Automation")
        self.automation_tab_layout = QVBoxLayout()

        self.automation_group.setLayout(self.automation_tab_layout)
        self.automation_group_layout.addWidget(self.automation_group)
        # ---------------------------------- #

        # ----- Dream Water Button ----- #
        dream_water_button = QPushButton("Dream Water")

        dream_water_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        dream_water_button.setMinimumHeight(50)

        dream_water_button.clicked.connect(self.handle_dream_water)

        self.automation_tab_layout.addWidget(dream_water_button)
        # ------------------------------ #

        # ----- Idols Button ----- #
        idols_button = QPushButton("Idols")

        idols_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        idols_button.setMinimumHeight(50)

        idols_button.clicked.connect(self.handle_idols)

        self.automation_tab_layout.addWidget(idols_button)
        # ------------------------ #

    @asyncSlot()
    async def handle_dream_water(self):
        print("[AUTOMATION] Dream Water pressed.")

        pass

    @asyncSlot()
    async def handle_idols(self):
        print("[AUTOMATION] Idols pressed.")

        await self.utils.break_idols()


class UtilityTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        self.auto_dialogue_tasks = {}
        self.speedhack_tasks = {}
        self.freecam_task = None

        # ----- Creating Layout ----- #
        self.utility_group_layout = QVBoxLayout()
        self.setLayout(self.utility_group_layout)
        # --------------------------- #

        # ----- Creating Utility Group ----- #
        self.utility_group = QGroupBox("Utility")
        self.utility_tab_layout = QVBoxLayout()

        #self.utility_tab_layout.addStretch()

        self.utility_group.setLayout(self.utility_tab_layout)
        self.utility_group_layout.addWidget(self.utility_group)
        # ---------------------------------- #

        # ----- Auto Dialogue Button ----- #
        auto_dialogue_button = QPushButton("Toggle Auto Dialogue")

        auto_dialogue_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #auto_dialogue_button.setMaximumHeight(50)
        #auto_dialogue_button.setMinimumHeight(50)

        auto_dialogue_button.clicked.connect(lambda: asyncio.create_task(self.toggle_auto_dialogue()))

        self.utility_tab_layout.addWidget(auto_dialogue_button)
        # -------------------------------- #

        # ----- Speedhack Button ----- #
        speedhack_button = QPushButton("Toggle Speedhack")

        speedhack_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #speedhack_button.setMaximumHeight(50)
        #speedhack_button.setMinimumHeight(50)

        speedhack_button.clicked.connect(lambda: asyncio.create_task(self.toggle_speedhack()))

        self.utility_tab_layout.addWidget(speedhack_button)
        # ---------------------------- #

        # ----- Freecam Button ----- #
        freecam_button = QPushButton("Toggle Freecam")

        freecam_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #freecam_button.setMaximumHeight(50)
        #freecam_button.setMinimumHeight(50)

        freecam_button.clicked.connect(lambda: asyncio.create_task(self.toggle_freecam()))

        self.utility_tab_layout.addWidget(freecam_button)
        # -------------------------- #

        # ----- Freecam Teleport Button ----- #
        freecam_teleport_button = QPushButton("Freecam Teleport")

        freecam_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #freecam_teleport_button.setMaximumHeight(50)
        #freecam_teleport_button.setMinimumHeight(50)

        freecam_teleport_button.clicked.connect(lambda: asyncio.create_task(self.handle_freecam_teleport()))

        self.utility_tab_layout.addWidget(freecam_teleport_button)
        # ---------------------------------- #

        # ----- XYZ Sync Button ----- #
        xyz_sync_button = QPushButton("XYZ Sync")

        xyz_sync_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #xyz_sync_button.setMaximumHeight(50)
        #xyz_sync_button.setMinimumHeight(50)

        xyz_sync_button.clicked.connect(lambda: asyncio.create_task(self.handle_xyz_sync()))

        self.utility_tab_layout.addWidget(xyz_sync_button)
        # --------------------------- #

        # ----- Copy Position Button ----- #
        copy_position_button = QPushButton("Copy Position")

        copy_position_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #copy_position_button.setMaximumHeight(50)
        #copy_position_button.setMinimumHeight(50)

        copy_position_button.clicked.connect(lambda: asyncio.create_task(self.handle_copy_position()))

        self.utility_tab_layout.addWidget(copy_position_button)
        # ------------------------------- #

    async def toggle_auto_dialogue(self):
        print("[UTILITY] Auto Dialogue pressed.")

        if not self.auto_dialogue_tasks:
            for client in self.hooked_clients:
                self.auto_dialogue_tasks[client] = asyncio.create_task(self.utils.handle_auto_dialogue(client))
            return

        if self.auto_dialogue_tasks:
            for client, auto_dialogue_task in self.auto_dialogue_tasks.items():
                auto_dialogue_task.cancel()
            self.auto_dialogue_tasks = {}

    async def toggle_speedhack(self):
        print("[UTILITY] Speedhack pressed.")

        if not self.speedhack_tasks:
            for client in self.hooked_clients:
                self.speedhack_tasks[client] = asyncio.create_task(self.utils.handle_speedhack(client))
            return

        if self.speedhack_tasks:
            for client, speedhack_task in self.speedhack_tasks.items():
                speedhack_task.cancel()
            self.speedhack_tasks = {}

    async def toggle_freecam(self):
        print("[UTILITY] Freecam pressed.")

        if not self.freecam_task:
            if self.hooked_clients:
                self.freecam_task = asyncio.create_task(self.utils.handle_freecam())
                return

        if self.freecam_task:
            self.freecam_task.cancel()
            self.freecam_task = None
            print(f"[TOGGLE] Freecam cancelled.") # i dont like this here but i was forced to

    async def handle_freecam_teleport(self):
        print("[UTILITY] Freecam Teleport pressed.")

        if not self.freecam_task:
            print(f"[UTILITY] Freecam is not active.")

        if self.freecam_task:
            self.freecam_task.cancel()

            camera_pos = await self.freecam_task

            self.freecam_task = None

            self.freecam_teleport_task = asyncio.create_task(self.utils.freecam_teleport(camera_pos))

    async def handle_xyz_sync(self):
        print("[UTILITY] XYZ Sync pressed.")

        await self.utils.xyz_sync()

    async def handle_copy_position(self):
        print("[UTILITY] Copy Position pressed.")

        await self.utils.copy_position()

class ThemesTab(QWidget):
    def __init__(self, themes: Themes):
        super().__init__()
        self.themes = themes

        # ----- Creating Layout ----- #
        self.themes_tab_layout = QVBoxLayout()
        self.setLayout(self.themes_tab_layout)
        # --------------------------- #

        # ----- Creating Main Themes Group ----- #
        self.main_themes_group = QGroupBox("Main Themes")
        self.main_themes_group_layout = QVBoxLayout()
        # -------------------------------------- #

        # ----- Creating Preset Themes Group ----- #
        self.preset_themes_group = QGroupBox("Preset Themes")
        self.preset_themes_group_layout = QVBoxLayout()
        # ---------------------------------------- #

        # ----- Default Theme Button ----- #
        default_theme_button_button = QPushButton("Default Theme")

        default_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #default_theme_button_button.setMaximumHeight(50)
        #default_theme_button_button.setMinimumHeight(50)

        default_theme_button_button.clicked.connect(self.enable_default_theme)

        self.main_themes_group_layout.addWidget(default_theme_button_button)
        # -------------------------------- #

        # ----- Nightmare Theme Button ----- #
        nightmare_theme_button_button = QPushButton("Nightmare Theme")

        nightmare_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #nightmare_theme_button_button.setMaximumHeight(50)
        #nightmare_theme_button_button.setMinimumHeight(50)

        nightmare_theme_button_button.clicked.connect(self.enable_nightmare_theme)

        self.main_themes_group_layout.addWidget(nightmare_theme_button_button)
        # -------------------------------- #

        # ----- Custom Theme Button ----- #
        custom_theme_button_button = QPushButton("Custom Theme")

        custom_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #custom_theme_button_button.setMaximumHeight(50)
        #custom_theme_button_button.setMinimumHeight(50)

        custom_theme_button_button.clicked.connect(self.enable_custom_theme)

        self.main_themes_group_layout.addWidget(custom_theme_button_button)
        # ------------------------------ #

        # ----- Night Theme Button ----- #
        night_theme_button_button = QPushButton("Night Theme")

        night_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #night_theme_button_button.setMaximumHeight(50)
        #night_theme_button_button.setMinimumHeight(50)

        night_theme_button_button.clicked.connect(self.enable_night_theme)

        self.preset_themes_group_layout.addWidget(night_theme_button_button)
        # ------------------------------ #

        # ----- Celestia Theme Button ----- #
        celestia_theme_button_button = QPushButton("Celestia Theme")

        celestia_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #celestia_theme_button_button.setMaximumHeight(50)
        #celestia_theme_button_button.setMinimumHeight(50)

        celestia_theme_button_button.clicked.connect(self.enable_celestia_theme)

        self.preset_themes_group_layout.addWidget(celestia_theme_button_button)
        # --------------------------------- #

        # ----- Mooshu Theme Button ----- #
        mooshu_theme_button_button = QPushButton("Mooshu Theme")

        mooshu_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #mooshu_theme_button_button.setMaximumHeight(50)
        #mooshu_theme_button_button.setMinimumHeight(50)

        mooshu_theme_button_button.clicked.connect(self.enable_mooshu_theme)

        self.preset_themes_group_layout.addWidget(mooshu_theme_button_button)
        # -------------------------------- #

        self.main_themes_group.setLayout(self.main_themes_group_layout)
        self.preset_themes_group.setLayout(self.preset_themes_group_layout)

        self.themes_tab_layout.addWidget(self.main_themes_group)
        self.themes_tab_layout.addWidget(self.preset_themes_group)

    def enable_default_theme(self):
        print("[THEMES] Default Theme pressed.")

        self.window().setStyleSheet(self.themes.default)

    def enable_nightmare_theme(self):
        print("[THEMES] Nightmare Theme pressed.")

        self.window().setStyleSheet(self.themes.nightmare)

    def enable_custom_theme(self):
        print("[THEMES] Custom Theme pressed.")

        themes_directory = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "themes"
        )

        def handle_select(theme_path):
            try:
                with open(theme_path, encoding="utf-8") as theme_file:
                    theme = json.load(theme_file)

                if not isinstance(theme, dict) or not all(
                    isinstance(value, str) for value in theme.values()
                ):

                    raise ValueError("Theme settings must be an object of strings.")

                stylesheet = self.themes.build_stylesheet(theme)

            except (OSError, ValueError, KeyError) as error:
                QMessageBox.warning(
                    self.theme_dialog, "Unable to Load Theme", str(error)
                )
                return

            self.window().setStyleSheet(stylesheet)
            self.theme_dialog.close()
            print(f"[THEMES] {os.path.basename(theme_path)} theme enabled.")

        self.theme_dialog = ThemeDialog(
            themes_directory, on_select=handle_select, parent=self.window()
        )
        self.theme_dialog.show()

    def enable_night_theme(self):
        print("[THEMES] Night Theme pressed.")

        self.window().setStyleSheet(self.themes.night)

    def enable_celestia_theme(self):
        print("[THEMES] Celestia Theme pressed.")

        self.window().setStyleSheet(self.themes.celestia)

    def enable_mooshu_theme(self):
        print("[THEMES] Mooshu Theme pressed.")

        self.window().setStyleSheet(self.themes.mooshu)

class MainWindow(QWidget):
    def __init__(self, loop: QEventLoop):
        super().__init__()
        self.loop = loop

        self.hooked_clients = []
        self.utils = Utils()
        self.themes = Themes()

        self.always_on_top_config = self.utils.read_config()["always_on_top"]
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.always_on_top_config)

        self.enable_clients_tab = self.utils.read_config()["enable_clients_tab"]

        self.use_dungeon_theme = self.utils.read_config()["use_dungeon_theme"]

        if self.use_dungeon_theme:
            self.window().setStyleSheet(self.themes.nightmare)

        self.setWindowTitle("Nightmare Dungeon Cheat Tool - Lxghtend")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North) # Changes tab position, North: Top, South: Bottom, West: Left, East: Right

        self.hooks_tab = HooksTab(self.utils, self.hooked_clients)
        if self.enable_clients_tab:
            self.clients_tab = ClientsTab(self.utils, self.hooked_clients)
        self.portals_tab = PortalsTab(self.utils, self.hooked_clients)
        self.bosses_tab = BossesTab(self.utils, self.hooked_clients)
        self.prayer_tab = PrayerTab(self.utils, self.hooked_clients)
        self.automation_tab = AutomationTab(self.utils, self.hooked_clients)
        self.utility_tab = UtilityTab(self.utils, self.hooked_clients)
        self.themes_tab = ThemesTab(self.themes)

        tabs.addTab(self.hooks_tab, "Hooks")
        if self.enable_clients_tab:
            tabs.addTab(self.clients_tab, "Clients")
        tabs.addTab(self.portals_tab, "Portals")
        tabs.addTab(self.bosses_tab, "Bosses")
        tabs.addTab(self.prayer_tab, "Prayer")
        tabs.addTab(self.automation_tab, "Automation")
        tabs.addTab(self.utility_tab, "Utility")
        tabs.addTab(self.themes_tab, "Themes")

        layout.addWidget(tabs)

        # Creating footer

        footers_layout = QHBoxLayout()

        left_layout = QHBoxLayout()
        left_layout.setSpacing(0)

        donation_link_label = QLabel('<a href="https://www.buymeacoffee.com/lxghtend">Donate, </a>', alignment=Qt.AlignmentFlag.AlignLeft)
        discord_label = QLabel('<a href="https://discord.gg/2xBeynxstw">Discord</a>', alignment=Qt.AlignmentFlag.AlignLeft)
        credit_label = QLabel('Made by Lxghtend (<a href="https://github.com/Lxghtend">https://github.com/Lxghtend</a>)', alignment=Qt.AlignmentFlag.AlignRight)

        donation_link_label.setOpenExternalLinks(True)
        discord_label.setOpenExternalLinks(True)
        credit_label.setOpenExternalLinks(True)

        left_layout.addWidget(donation_link_label)
        left_layout.addWidget(discord_label)

        footers_layout.addLayout(left_layout)
        footers_layout.addStretch()

        footers_layout.addWidget(credit_label)

        layout.addLayout(footers_layout)

        self.start_keybinds()

    def start_keybinds(self):
        def run_threadsafe(coroutine):
            asyncio.run_coroutine_threadsafe(coroutine, self.loop)

        keybinds = {
            self.utils.read_config()["handle_xyz_sync"]: self.utility_tab.handle_xyz_sync,
            self.utils.read_config()["toggle_auto_dialogue"]: self.utility_tab.toggle_auto_dialogue,
            self.utils.read_config()["toggle_speedhack"]: self.utility_tab.toggle_speedhack,
            self.utils.read_config()["toggle_freecam"]: self.utility_tab.toggle_freecam,
            self.utils.read_config()["handle_freecam_teleport"]: self.utility_tab.handle_freecam_teleport
        }

        for keybind, function in keybinds.items():
            keyboard.add_hotkey(keybind, lambda func=function: run_threadsafe(func()))

class ThemeDialog(QDialog):
    def __init__(self, themes_directory: str, on_select, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Custom Themes")
        self.setMinimumWidth(240)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)

        try:
            theme_files = sorted(
                entry.name for entry in os.scandir(themes_directory)
                if entry.is_file() and entry.name.lower().endswith(".json")
            )

        except OSError:
            theme_files = []

        for theme_file in theme_files:
            theme_path = os.path.join(themes_directory, theme_file)
            theme_button = QPushButton(theme_file)
            theme_button.setMinimumHeight(40)

            theme_button.clicked.connect(
                lambda checked=False, target=theme_path: on_select(target)
            )

            layout.addWidget(theme_button)

        if not theme_files:
            layout.addWidget(QLabel("No JSON theme files found."))


class UpdaterDialog(QDialog):
    def __init__(self, parent: MainWindow = None):
        super().__init__(parent)

        self.setWindowTitle("Updater")
        self.setFixedSize(210, 150)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout()

        label = QLabel("An update was found...")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        update_button = QPushButton("Update")
        update_button.clicked.connect(lambda: trigger_update(tool_dir=os.path.dirname(os.path.abspath(__file__))))

        ok_button = QPushButton("Ignore")
        ok_button.clicked.connect(self.accept)

        layout.addWidget(label)
        layout.addWidget(update_button)
        layout.addWidget(ok_button)

        self.setLayout(layout)

class DisclaimerDialog(QDialog):
    def __init__(self, parent: MainWindow = None):
        super().__init__(parent)

        self.setWindowTitle("Disclaimer")
        self.setFixedSize(200, 150)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout()

        label = QLabel("Please consider donating to\nsupport future development.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        donate_button = QPushButton("Donate")
        donate_button.clicked.connect(self.open_donate)

        ok_button = QPushButton("Ok")
        ok_button.clicked.connect(self.accept)

        layout.addWidget(label)
        layout.addWidget(donate_button)
        layout.addWidget(ok_button)

        self.setLayout(layout)

    def open_donate(self):
        QDesktopServices.openUrl(QUrl("https://buymeacoffee.com/lxghtend"))

def main():
    outdated, local, remote = check_for_update()

    app = QApplication(sys.argv)

    appid = "lxghtend.nightmare.tool.1.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    app.setWindowIcon(QIcon("icon.ico"))

    app.setStyle("Fusion")

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow(loop)
    window.show()

    disclaimer = DisclaimerDialog(window)

    if outdated:
        updater = UpdaterDialog(window)
        updater.finished.connect(disclaimer.show) # shows disclaimer after updater closed
        updater.show()

    else:
        disclaimer.show()

    with loop:
        loop.run_forever()

    #sys.exit(app.exec())

if __name__ == "__main__":
    main()
