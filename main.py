import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
import os
import tempfile
import subprocess
from pynbt import NBTFile, TAG_String, TAG_Long, TAG_Int, TAG_Short, TAG_List, TAG_Compound, TAG_Byte
import context

def select_file():
    filename = askopenfilename(initialdir="~/.minecraft-pi/games/com.mojang/minecraftWorlds", filetypes=[('NBT Files', 'level.dat')])
    if not type(filename) is str:
        exit(0)
    _, temp_filename = tempfile.mkstemp()
    completed_process = subprocess.run(['./pi-nbt', 'remove-header', filename, temp_filename])
    if completed_process.returncode != 0:
        raise Exception('Unable To Prepare Files')
    context.current_file = filename
    context.current_temp_file = temp_filename;
    with open(temp_filename, 'rb') as io:
        context.nbt_file = NBTFile(io, little_endian=True)

def save_file():
    with open(context.current_temp_file, 'wb') as io:
        context.nbt_file.save(io, little_endian=True)
    completed_process = subprocess.run(['./pi-nbt', 'add-header', context.current_temp_file, context.current_file])
    if completed_process.returncode != 0:
        raise Exception('Unable To Save Files')

tabs = []

class Tab(ttk.Frame):
    def create_widgets(self):
        return
    def save_nbt(self):
        return
    def reload_nbt(self):
        return
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        self.pack()
        self.create_widgets()
        tabs.append(self)

def save_nbt():
    for tab in tabs:
        tab.save_nbt()
def reload_nbt():
    for tab in tabs:
        tab.reload_nbt()

GAME_MODE = [
    'Survival',
    'Creative'
]

class WorldTab(Tab):
    def save_nbt(self):
        context.nbt_file['LevelName'] = TAG_String(self.world_name.get('1.0', 'end'))
        context.nbt_file['RandomSeed'] = TAG_Long(int(self.seed.get('1.0', 'end')))
        context.nbt_file['Time'] = TAG_Long(int(self.time.get('1.0', 'end')))
        context.nbt_file['GameType'] = TAG_Int(GAME_MODE.index(self.game_mode.get()))
    def reload_nbt(self):
        self.world_name.delete('1.0', 'end')
        self.world_name.insert('1.0', context.nbt_file['LevelName'].value)
        self.seed.delete('1.0', 'end')
        self.seed.insert('1.0', str(context.nbt_file['RandomSeed'].value))
        self.time.delete('1.0', 'end')
        self.time.insert('1.0', str(context.nbt_file['Time'].value))
        self.game_mode.set(GAME_MODE[context.nbt_file['GameType'].value])
    def create_widgets(self):
        self.columnconfigure(1, weight=1)

        world_name_label = tk.Label(self, text='World Name:')
        world_name_label.grid(row=0, column=0, padx=6, pady=6, sticky='W')
        self.world_name = tk.Text(self, height=1, width=24, padx=5, pady=5)
        self.world_name.grid(row=0, column=1, padx=5, pady=5, sticky='EW')

        seed_label = tk.Label(self, text='Seed:')
        seed_label.grid(row=1, column=0, padx=6, pady=6, sticky='W')
        self.seed = tk.Text(self, height=1, width=24, padx=5, pady=5)
        self.seed.grid(row=1, column=1, padx=5, pady=5, sticky='EW')

        time_label = tk.Label(self, text='Time:')
        time_label.grid(row=2, column=0, padx=6, pady=6, sticky='W')
        self.time = tk.Text(self, height=1, width=24, padx=5, pady=5)
        self.time.grid(row=2, column=1, padx=5, pady=5, sticky='EW')
        
        self.game_mode = tk.StringVar(self)
        game_mode_label = tk.Label(self, text='Game Mode:')
        game_mode_label.grid(row=3, column=0, padx=6, pady=6, sticky='W')
        game_mode_widget = ttk.Combobox(self, textvariable=self.game_mode, values=GAME_MODE)
        game_mode_widget.state(['readonly'])
        game_mode_widget.grid(row=3, column=1, padx=5, pady=5, sticky='EW')

class PlayerTab(Tab):
    def save_nbt(self):
        context.nbt_file['Player'].value['Health'] = TAG_Short(int(self.health.get('1.0', 'end')))
    def reload_nbt(self):
        self.health.delete('1.0', 'end')
        self.health.insert('1.0', str(context.nbt_file['Player'].value['Health'].value))
    def create_widgets(self):
        self.columnconfigure(1, weight=1)

        health_label = tk.Label(self, text='Health:')
        health_label.grid(row=0, column=0, padx=6, pady=6, sticky='W')
        self.health = tk.Text(self, height=1, width=24, padx=5, pady=5)
        self.health.grid(row=0, column=1, padx=5, pady=5, sticky='EW')

class ScrollableTab(Tab):
    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.grid(row=0, column=1, sticky='NSE')
        self.canvas.grid(row=0, column=0, sticky='NSEW')
        
        self.scrollable_frame = ttk.Frame(self.canvas)
        scrollable_frame_id = self.canvas.create_window(0, 0, window=self.scrollable_frame, anchor='nw')
        
        def configure_scrollable_frame(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.scrollable_frame.bind('<Configure>', configure_scrollable_frame)
        def configure_canvas(event):
            self.canvas.itemconfig(scrollable_frame_id, width=event.width)
        self.canvas.bind('<Configure>', configure_canvas)

def create_slot(root, item, count, damage, slot):
    frame = ttk.Frame(root, borderwidth=1, relief='raised')
    
    item_label = tk.Label(frame, text='Item:')
    item_label.grid(row=0, column=0, padx=6, pady=6, sticky='W')
    item_widget = tk.Text(frame, height=1, width=4, padx=5, pady=5)
    item_widget.grid(row=0, column=1, padx=5, pady=5, sticky='EW')
    item_widget.insert('1.0', str(item));

    count_label = tk.Label(frame, text='Count:')
    count_label.grid(row=0, column=2, padx=6, pady=6, sticky='W')
    count_widget = tk.Text(frame, height=1, width=4, padx=5, pady=5)
    count_widget.grid(row=0, column=3, padx=5, pady=5, sticky='EW')
    count_widget.insert('1.0', str(count));

    damage_label = tk.Label(frame, text='Damage:')
    damage_label.grid(row=0, column=4, padx=6, pady=6, sticky='W')
    damage_widget = tk.Text(frame, height=1, width=4, padx=5, pady=5)
    damage_widget.grid(row=0, column=5, padx=5, pady=5, sticky='EW')
    damage_widget.insert('1.0', str(damage));

    frame.columnconfigure(1, weight=1)
    frame.columnconfigure(3, weight=1)
    frame.columnconfigure(5, weight=1)

    frame.grid(row=slot, padx=6, pady=6, sticky='EW')
    
    return (item_widget, count_widget, damage_widget)

def create_slot_tag(slot):
    return TAG_Compound({'id': TAG_Short(int(slot[0].get('1.0', 'end'))), 'Count': TAG_Byte(int(slot[1].get('1.0', 'end'))), 'Damage': TAG_Short(int(slot[2].get('1.0', 'end')))})

class InventoryTab(ScrollableTab):
    def save_nbt(self):
        tags = []
        for slot in self.slots:
            tags.append(create_slot_tag(slot))
        context.nbt_file['Player'].value[self.name] = TAG_List(TAG_Compound, tags)
    def reload_nbt(self):
        self.slots = []
        for child in self.scrollable_frame.winfo_children():
            child.destroy()
        i = 0
        for slot in context.nbt_file['Player'].value[self.name].value:
            i = i + 1
            if i > self.total_slots:
                break
            self.slots.append(create_slot(self.scrollable_frame, slot['id'].value, slot['Count'].value, slot['Damage'].value, i))
        remaining_slots = self.total_slots - i
        for _ in range(remaining_slots):
            self.slots.append(create_slot(self.scrollable_frame, 255, -1, 0, i))
            i = i + 1
        self.canvas.update_idletasks()
    def create_widgets(self):
        ScrollableTab.create_widgets(self);
        self.scrollable_frame.columnconfigure(0, weight=1)
    def __init__(self, root, total_slots, name):
        ScrollableTab.__init__(self, root);
        self.total_slots = total_slots
        self.name = name
        self.slots = []

def save_callback():
    save_nbt()
    save_file()
    reload_nbt()

def show_error(val):
    showerror('Error', message=str(val))
    exit(1)
def report_callback_exception(self, exc, val, tb):
    show_error(val)

tk.Tk.report_callback_exception = report_callback_exception

try:
    root = tk.Tk()
    root.withdraw()

    select_file()

    root.title('MCPIedit')

    tab_control = ttk.Notebook(root)

    world_tab = WorldTab(tab_control)
    player_tab = PlayerTab(tab_control)
    inventory_tab = InventoryTab(tab_control, 36, 'Inventory')
    armor_tab = InventoryTab(tab_control, 4, 'Armor')

    tab_control.add(world_tab, text='World')
    tab_control.add(player_tab, text='Player')
    tab_control.add(inventory_tab, text='Inventory')
    tab_control.add(armor_tab, text='Armor')

    tab_control.pack(expand=1, fill='both', padx=12, pady=12)

    save_button = tk.Button(root, text='Save', command=save_callback)
    save_button.pack(side='right', padx=6, pady=6)

    reload_nbt()

    root.deiconify()

    root.mainloop()
except Exception as e:
    show_error(e)
