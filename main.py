import os
import mido
import json
import shutil
import tkinter
import threading
import traceback
import subprocess
from tkinter import filedialog

def sys_call_exit():
    os._exit(0)

def set_max_thread_num(n):
    global_info["max_thread_num"] = int(n)

def ask_filename():
    i = filedialog.askopenfilename(title="MinecraftMusicMaker", filetypes=[("MIDI Files", ".mid")])
    if i:
        gui_file_path.set(i)

def start_task():
    if global_info["thread_num"] == 0:
        global_info["log"] = []
        global_info["task_name"] = os.path.splitext(os.path.basename(gui_file_path.get()))[0]
        threading.Thread(target=convertor, args=(gui_file_path.get(), global_info["sound_font"], global_info["max_thread_num"])).start()

def make_track(note_text, note_num, track_num):
    global_info["thread_num"] += 1
    try:
        for n in range(note_num):
            note_text += "[A_" + str(n) + "]"

        note_text += " amix=inputs=" + str(note_num) + ":duration=longest:normalize=0"

        with open("Cache/cmd_" + str(track_num), "w") as io:
            io.write(note_text)

        task = subprocess.Popen("ffmpeg -i " + global_info["file_position"] + "/Asset/audio/harp.ogg -i " + global_info["file_position"] + "/Asset/audio/pling.ogg -i " + global_info["file_position"] + "/Asset/audio/bass.ogg -i " + global_info["file_position"] + "/Asset/audio/guitar.ogg -i " + global_info["file_position"] + "/Asset/audio/bit.ogg -i " + global_info["file_position"] + "/Asset/audio/hat.ogg -i " + global_info["file_position"] + "/Asset/audio/snare.ogg -i " + global_info["file_position"] + "/Asset/audio/basedrum.ogg -i " + global_info["file_position"] + "/Asset/audio/bell.ogg -i " + global_info["file_position"] + "/Asset/audio/cowbell.ogg -i " + global_info["file_position"] + "/Asset/audio/flute.ogg -i " + global_info["file_position"] + "/Asset/audio/sand.ogg -i " + global_info["file_position"] + "/Asset/audio/iron_xylophone.ogg -i " + global_info["file_position"] + "/Asset/audio/xylophone.ogg -i " + global_info["file_position"] + "/Asset/audio/chime.ogg -i " + global_info["file_position"] + "/Asset/audio/didgeridoo.ogg -/filter_complex " + global_info["file_position"] + "/Cache/cmd_" + str(track_num) + " \"" + global_info["file_position"] + "/Cache/Track_" + str(track_num) + ".wav\"", stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        for output_line in task.stdout:
            global_info["log"] += output_line.decode().splitlines()
            global_info["refresh_log"] = True
        task.wait()
    except:
        global_info["log"] += traceback.format_exc().splitlines()
        global_info["refresh_log"] = True
    finally:
        global_info["thread_num"] -= 1

def convertor(midi_path, sound_font, thread_num):
    try:
        global_info["task_state"] = "Analysing..."
        if os.path.exists("Cache"):
            shutil.rmtree("Cache")
        os.mkdir("Cache")

        mid = mido.MidiFile(midi_path, clip=True)

        info_list = {}
        tempo_list = [(0, 500000), (float("INF"), 0)]
        global_info["thread_num"] = 0
        for track_num, track in enumerate(mid.tracks):
            note_num = 0
            note_text = ""
            source_time = 0
            global_info["task_state"] = "Analysing..."
            for msg in track:
                source_time += msg.time
                if msg.type == "set_tempo":
                    for n, i in enumerate(tempo_list):
                        if i[0] > source_time:
                            tempo_list.insert(n, (source_time, msg.tempo))
                            break

                if msg.type == "control_change":
                    channel = msg.channel
                    if channel not in info_list:
                        info_list[channel] = {"program": [(float("INF"), "")], "volume": [(float("INF"), 1)]}
                    if msg.control == 7:
                        value = int(msg.value / 1.27) / 100
                        for n, i in enumerate(info_list[channel]["volume"]):
                            if i[0] > source_time:
                                info_list[channel]["volume"].insert(n, (source_time, value))
                                break
                    elif msg.control == 121:
                        for n, i in enumerate(info_list[channel]["volume"]):
                            if i[0] > source_time:
                                info_list[channel]["volume"].insert(n, (source_time, 1))
                                break

                if msg.type == "program_change":
                    program = msg.program
                    channel = msg.channel
                    if channel not in info_list:
                        info_list[channel] = {"program": [(float("INF"), "")], "volume": [(float("INF"), 1)]}
                    if channel != 9:
                        if str(program) in sound_font["sound_list"]:
                            value = sound_font["sound_list"][str(program)]
                        else:
                            value = sound_font["sound_list"]["undefined"]
                        for n, i in enumerate(info_list[channel]["program"]):
                            if i[0] > source_time:
                                info_list[channel]["program"].insert(n, (source_time, value))
                                break

                if msg.type == "note_on":
                    note = msg.note
                    channel = msg.channel
                    velocity = msg.velocity
                    if velocity != 0 and 21 <= note <= 108:
                        if channel not in info_list:
                            info_list[channel] = {"program": [(float("INF"), "")], "volume": [(float("INF"), 1)]}

                        volume = 1
                        for i in info_list[channel]["volume"]:
                            if i[0] > source_time:
                                break
                            else:
                                volume = i[1]

                        if channel == 9:
                            if str(note) in sound_font["sound_list"]["percussion"]:
                                program = sound_font["sound_list"]["percussion"][str(note)]
                            else:
                                program = sound_font["sound_list"]["percussion"]["undefined"]
                        else:
                            program = sound_font["sound_list"]["default"]
                            for typ in info_list[channel]["program"]:
                                if typ[0] > source_time:
                                    break
                                else:
                                    program = typ[1]

                        velocity = (velocity / 127) * volume

                        if channel == 9:
                            pitch = 1
                        else:
                            pitch = sound_font["note_list"][note - 21]

                        tick_time = 0
                        for n in range(1, len(tempo_list)):
                            if tempo_list[n][0] <= source_time:
                                tick_time += mido.tick2second(tempo_list[n][0] - tempo_list[n - 1][0], mid.ticks_per_beat, tempo_list[n - 1][1]) * 1000
                            else:
                                tick_time += mido.tick2second(source_time - tempo_list[n - 1][0], mid.ticks_per_beat, tempo_list[n - 1][1]) * 1000
                                break

                        note_text += "[" + str(program) + ":a] aresample=16000, asetrate=16000*" + str(pitch) + ", aresample=16000, volume=" + str(round(velocity, 2)) + ", adelay=" + str(round(tick_time, 2)) + ":all=1, asetpts=PTS-STARTPTS [A_" + str(note_num) + "]; "
                        note_num += 1

            global_info["task_state"] = "Processing..."

            while global_info["thread_num"] >= thread_num:
                pass

            if note_num:
                threading.Thread(target=make_track, args=(note_text, note_num, track_num)).start()

        while global_info["thread_num"] != 0:
            pass

        global_info["task_state"] = "Mixing..."

        command = "ffmpeg "
        note_text = ""
        track_num = 0
        for i in os.listdir("Cache"):
            if i.endswith(".wav"):
                command += "-i " + global_info["file_position"] + "/Cache/" + i + " "
                track_num += 1

        for n in range(track_num):
            note_text += "[" + str(n) + ":a] aresample=16000, asetpts=PTS-STARTPTS [A_" + str(n) + "]; "

        for n in range(track_num):
            note_text += "[A_" + str(n) + "]"

        note_text += " amix=inputs=" + str(track_num) + ":duration=longest:normalize=0"

        with open("Cache/cmd", "w") as io:
            io.write(note_text)

        task = subprocess.Popen(command + " -/filter_complex " + global_info["file_position"] + "/Cache/cmd \"" + global_info["file_position"] + "/Cache/audio.wav\"", stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        for output_line in task.stdout:
            global_info["log"] += output_line.decode().splitlines()
            global_info["refresh_log"] = True
        task.wait()
        global_info["task_state"] = "Saving..."
    except:
        global_info["log"] += traceback.format_exc().splitlines()
        global_info["refresh_log"] = True
    finally:
        if global_info["task_state"] != "Saving...":
            global_info["task_state"] = "Error"

global_info = {"max_thread_num": 1, "thread_num": 0, "file_position": os.path.abspath(""), "task_state": "Process finished", "task_name": "", "refresh_log": True, "log": []}

with open("Asset/text/default.json", "rb") as f:
    global_info["sound_font"] = json.loads(f.read())

tk_window = tkinter.Tk()
tk_window.resizable(False, False)
tk_window.geometry("800x450")
tk_window.title("MinecraftMusicMaker")
tk_window.iconbitmap("Asset/image/icon.ico")

tk_window.protocol("WM_DELETE_WINDOW", sys_call_exit)

gui_log = tkinter.StringVar()
gui_info1 = tkinter.StringVar()
gui_info2 = tkinter.StringVar()
gui_file_path = tkinter.StringVar()
gui_file_path.set("")
tkinter.Label(tk_window, textvariable=gui_info1).place(x=10, y=80)
tkinter.Label(tk_window, textvariable=gui_info2).place(x=220, y=80)
tkinter.Entry(tk_window, width=100, textvariable=gui_file_path).place(x=10, y=10, height=30)
tkinter.Button(tk_window, text="Browse...", width=8, command=ask_filename).place(x=724, y=10)
tkinter.Button(tk_window, text="Start", width=110, command=start_task).place(x=10, y=50)
tkinter.Label(tk_window, textvariable=gui_log, justify="left").place(x=10, y=102)
scale_bar = tkinter.Scale(tk_window, from_=1, to=16, orient="horizontal", showvalue=False, command=set_max_thread_num)
scale_bar.place(x=100, y=80)

while True:
    if global_info["task_state"] == "Saving...":
        if save_path := filedialog.asksaveasfilename(title="MinecraftMusicMaker", initialfile=global_info["task_name"], filetypes=[("WAV Files", ".wav")], defaultextension=".wav"):
            try:
                shutil.move("Cache/audio.wav", save_path)
            except:
                global_info["log"] += traceback.format_exc().splitlines()
                global_info["refresh_log"] = True
        global_info["task_state"] = "Process finished"
    if global_info["refresh_log"]:
        global_info["refresh_log"] = False
        gui_log.set("\n".join(global_info["log"][-20:]))
    gui_info1.set("Thread: " + str(global_info["thread_num"]) + "/" + str(global_info["max_thread_num"]))
    gui_info2.set("State: " + str(global_info["task_state"]))
    tk_window.update()
