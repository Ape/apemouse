#!/usr/bin/env python3

import argparse
import atexit
import collections
import queue
import signal
import threading
import time

import evdev
import evdev.ecodes as ecodes
import numpy as np
import numpy.linalg

CLICK_KEYS = {
    ecodes.KEY_KP5: ecodes.BTN_LEFT,
    ecodes.KEY_KP0: ecodes.BTN_RIGHT,
    ecodes.KEY_KPENTER: ecodes.BTN_MIDDLE,
}

MOVE_KEYS = {
    ecodes.KEY_KP1: np.array([-1.0,  1.0]),
    ecodes.KEY_KP2: np.array([ 0.0,  1.0]),
    ecodes.KEY_KP3: np.array([ 1.0,  1.0]),
    ecodes.KEY_KP4: np.array([-1.0,  0.0]),
    ecodes.KEY_KP6: np.array([ 1.0,  0.0]),
    ecodes.KEY_KP7: np.array([-1.0, -1.0]),
    ecodes.KEY_KP8: np.array([ 0.0, -1.0]),
    ecodes.KEY_KP9: np.array([ 1.0, -1.0]),
}

Event = collections.namedtuple("Event", "type code value")

class Mouse:
    def __init__(self, args, output_events, move_events):
        self.args = args
        self.output_events = output_events
        self.move_events = move_events
        self.update_time = 1.0 / args.freq

        self.pressed_keys = set()
        self.movement = np.zeros(2)
        self.speed = args.speed

    def run(self):
        while True:
            while True:
                try:
                    self._handle_event(self.move_events.get_nowait())
                except queue.Empty:
                    break

            direction = self._normalize(sum(MOVE_KEYS[x] for x in self.pressed_keys))
            if direction is not None:
                self.movement += self.update_time * self.speed * direction
                int_movement = self.movement.astype(int)
                self.movement -= int_movement

                self.output_events.put([
                    Event(ecodes.EV_REL, ecodes.REL_X, int_movement[0]),
                    Event(ecodes.EV_REL, ecodes.REL_Y, int_movement[1]),
                ])

                time.sleep(self.update_time)
            else:
                self._handle_event(self.move_events.get())

    def _handle_event(self, event):
        if event.code == ecodes.KEY_LEFTSHIFT:
            self.speed = self.args.speed
            if event.value:
                self.speed *= self.args.speedup
        else:
            if event.value:
                self.pressed_keys.add(event.code)
            else:
                self.pressed_keys.discard(event.code)

    def _normalize(self, vector):
        norm = numpy.linalg.norm(vector)
        if norm > 0.5:
            return vector / norm
        else:
            return None

def write_events(output_events):
    device = evdev.UInput({
        ecodes.EV_KEY: ecodes.keys,
        ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y],
    }, name="apemouse")

    while True:
        for event in output_events.get():
            device.write(event.type, event.code, event.value)
        device.syn()

def read_events_retry(*args):
    while True:
        try:
            read_events(*args)
        except OSError:
            print("Device lost, trying to reconnect...")
            time.sleep(3)

def read_events(args, output_events, move_events):
    active = False
    input_device = evdev.InputDevice(args.device)
    atexit.register(lambda: input_device.ungrab())
    input_device.grab()

    for event in input_device.read_loop():
        block = False

        if event.type != ecodes.EV_KEY:
            continue

        if event.code == ecodes.KEY_LEFTMETA:
            active = bool(event.value)
        elif event.code == ecodes.KEY_LEFTSHIFT:
            move_events.put(event)
        elif active:
            if event.code in CLICK_KEYS:
                block = True
                output_events.put([
                    Event(ecodes.EV_KEY, ecodes.KEY_LEFTMETA, int(not event.value)),
                    Event(ecodes.EV_KEY, CLICK_KEYS[event.code], event.value),
                ])
            elif event.code in MOVE_KEYS:
                block = True
                move_events.put(event)

        if not block:
            output_events.put([Event(ecodes.EV_KEY, event.code, event.value)])

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = argparse.ArgumentParser(description="Create a virtual mouse device controlled with numpad")
    parser.add_argument("device", help="the controlling keyboard device")
    parser.add_argument("--speed", type=float, default=400, help="mouse movement speed (default 400)")
    parser.add_argument("--speedup", type=float, default=3, help="speedup when holding shift (default 3)")
    parser.add_argument("--freq", type=float, default=200, help="mouse event frequency (default 200)")
    args = parser.parse_args()

    output_events = queue.Queue()
    move_events = queue.Queue()
    mouse = Mouse(args, output_events, move_events)

    threads = [
        threading.Thread(target=write_events, args=[output_events]),
        threading.Thread(target=read_events_retry, args=[args, output_events, move_events]),
        threading.Thread(target=lambda: mouse.run()),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
