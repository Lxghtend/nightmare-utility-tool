# Nightmare Utility Tool

## [Join the discord community...](https://discord.gg/2xBeynxstw)

A utility tool designed to assist with the **Nightmare Dungeon**, the final dungeon of **Wallaru**.  A popup will appear when a new update has been released.  Updates can be installed with only one click.

If you enjoy my tools and would like to support future development,  please consider [buying me a coffee](https://www.buymeacoffee.com/lxghtend).  

---

### 🔹 **nightmare-tool**   
**Dungeon-specific features:**  
- Portal teleports
- Boss teleports
- Prayer wheel teleports
- Automated collection of dream water to **spawn Malus**
- Automated sequence to **solo** break the idols

---

## 🔹 Additional Features
- Client renaming
- Client hook management
- Client information    
- General utilities    
- Preset themes
- Configurable themes 

---

## Configuration (`config.ini`)

Each tool supports a simple configuration file named **`config.ini`**.  
This file allows you to toggle common settings without modifying code.

Example:

```ini
[General]
always_on_top = True
enable_clients_tab = True
use_dungeon_theme = True

[Keybinds]
handle_xyz_sync = F3
toggle_speedhack = F4
toggle_freecam = F5
handle_freecam_teleport = F6
toggle_auto_dialogue = F7
```

---

## Custom Theme Configuration

The themes are cross compatible with [Raid Tools](https://github.com/Lxghtend/raid-utility-tools) themes.

All tools support user-defined themes to customize the look and feel of the interface.  
Themes can be configured by editing the **`default.json`** file inside the **`themes`** directory.

Example (Default Custom Theme):

```json
{
    "window_bg": "#00775D",             # Main window background
    "text_color": "#FFFFFF",            # Default text color
    "label_color": "#FFFFFF",           # Label text color
    "button_bg": "#009EB3",             # Button background
    "button_hover": "#44B8DB",          # Button hover background, usually brighter
    "button_pressed": "#056E97",        # Button pressed background, usually darker
    "button_hover_border": "#8BE4FF",   # Button hover border
    "button_pressed_border": "#045369", # Button pressed border
    "button_text": "#FFFFFF",           # Button text color
    "button_border": "#FFFFFF",         # Button border color
    "border_radius": "8px",             # Button roundness
    "font_family": "Calibri",           # Font type
    "font_size": "14px",                # Font size
    "font_style": "italic"              # Font style
}
```

---

## Installation

Clone the repository and install dependencies:

Method 1 (Recommended):

```bash
git clone https://github.com/lxghtend/nightmare-utility-tool.git
cd nightmare-utility-tool
uv venv
uv pip install -r nightmare-tool\requirements.txt
```

Method 2:

```bash
git clone https://github.com/lxghtend/nightmare-utility-tool.git
cd nightmare-utility-tool
pip install -r nightmare-tool\requirements.txt
```
**Note: The built-in updater only works if the tool was installed via git**

---

## Usage
To run the tool...

```bash
# Nightmare Tool
python nightmare-tool/main.py
```

---

## Requirements
- Python **3.11+**  
- Dependencies listed in `requirements.txt`

---

## Credits
Built and maintained by **Lxghtend**  
- [GitHub](https://github.com/Lxghtend)  
- [Buy Me a Coffee](https://www.buymeacoffee.com/lxghtend)
