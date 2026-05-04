import rtmidi
from evdev import UInput, ecodes as e
import time

CONFIG_FILE = "midi_keys.conf"

def load_config(path):
    mapping = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            note, key = line.split("=")
            note = int(note.strip())
            key = key.strip()

            if not hasattr(e, key):
                print(f"Unknown key: {key}")
                continue

            mapping[note] = getattr(e, key)
    return mapping

mapping = load_config(CONFIG_FILE)

ui = UInput({e.EV_KEY: list(set(mapping.values()))}, name="midi-keyboard")

midi = rtmidi.MidiIn()
ports = midi.get_ports()

if not ports:
    print("no MIDI devices")
    exit(1)

print("available devices:")
for i, p in enumerate(ports):
    print(f"{i}: {p}")

port_index = int(input("choose device port: "))
midi.open_port(port_index)

print("listening to MIDI")

pressed = set()

def handle(message, _):
    msg, _ = message
    status = msg[0] & 0xF0
    note = msg[1]
    velocity = msg[2]

    if status == 0x90:
        if velocity == 0:
            if note in mapping and note in pressed:
                ui.write(e.EV_KEY, mapping[note], 0)
                ui.syn()
                pressed.remove(note)
        else:
            if note in mapping and note not in pressed:
                ui.write(e.EV_KEY, mapping[note], 1)
                ui.syn()
                pressed.add(note)

    elif status == 0x80:
        if note in mapping and note in pressed:
            ui.write(e.EV_KEY, mapping[note], 0)
            ui.syn()
            pressed.remove(note)

midi.set_callback(handle)

while True:
    time.sleep(1)
