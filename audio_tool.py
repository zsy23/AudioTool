import os, wave
import threading
import tkinter as tk
from tkinter import filedialog
import numpy as np
import pygame


width = 600
height = 100
ratio = 0.7
close = 0
line_id = None
start_time = 0
cur_time = 0
record_start = 0
record_end = 0
nchannels = 0
sampwidth = 0
framerate = 0
nframes = 0
total_time = 0
data = None
save_dir = ""
save_prefix = "test_"
save_start = 0
mp3_fn = ""
lock = threading.Lock()


def time_line():
    global line_id, cur_time, start_bt, start_time
    while not close:
        if pygame.mixer.music.get_busy():
            cur_time = pygame.mixer.music.get_pos() / 1000 + start_time
            time_lab["text"] = "%d:%d/%d:%d" % (cur_time / 60, cur_time % 60, total_time / 60, total_time % 60)
            x = cur_time / total_time * width
            canvas.delete(line_id)
            line_id = canvas.create_line(x, 0, x, height * (ratio + 0.1), fill = "white")

            if cur_time >= total_time:
                pygame.mixer.music.stop()
                start_bt["text"] = "Start"
                cur_time = 0
                start_time = 0

            app.update()


def click_callback(event):
    global line_id, cur_time, start_time

    cur_time = event.x / width * total_time
    start_time = cur_time
    canvas.delete(line_id)
    line_id = canvas.create_line(event.x, 0, event.x, height * (ratio + 0.1), fill = "white")
    time_lab["text"] = "%d:%d/%d:%d" % (cur_time / 60, cur_time % 60, total_time / 60, total_time % 60)
    app.update()

    pygame.mixer.music.stop()
    if start_bt["text"] == "Stop":
        pygame.mixer.music.play(start = start_time)

def drag_callback(event):
    global line_id, cur_time, start_time

    cur_time = event.x / width * total_time
    start_time = cur_time
    canvas.delete(line_id)
    line_id = canvas.create_line(event.x, 0, event.x, height * (ratio + 0.1), fill = "white")
    time_lab["text"] = "%d:%d/%d:%d" % (cur_time / 60, cur_time % 60, total_time / 60, total_time % 60)
    app.update()

    pygame.mixer.music.stop()
    if start_bt["text"] == "Stop":
        pygame.mixer.music.play(start = start_time)
    

def read_wav(wav):
    global nchannels, sampwidth, framerate, nframes, total_time, data

    f = wave.open(wav, "rb")
    params = f.getparams()
    # (nchannels, sampwidth, framerate, nframes, comptype, compname)
    nchannels, sampwidth, framerate, nframes = params[:4]
    total_time = nframes / framerate
    str_data = f.readframes(nframes)
    f.close()
    
    data = np.fromstring(str_data, dtype = np.short)
    if nchannels == 2:
        data.shape = -1, 2
        data = data.T


def open_wav():
    global line_id, start_time, cur_time, mp3_fn

    wav_fn = filedialog.askopenfilename(initialdir = ".", filetypes = (("Audio File", ".wav"), ))
    if wav_fn == "":
        return
    read_wav(wav_fn)
    max_amp = np.max(np.abs(data))

    time_lab["text"] = "0:0/%d:%d" % (total_time / 60, total_time % 60)

    color = ["green", "blue"]
    for i in range(nchannels):
        for j in range(width):
            idx = int(j / width * nframes)
            amp = data[i][idx]
            h = height * ratio * 0.5 - amp / max_amp * height * ratio * 0.5 * 0.9
            half = height * ratio * 0.5
            canvas.create_line(j, half, j, h, fill = color[i])
    if line_id:
        canvas.delete(line_id)
    line_id = canvas.create_line(0, 0, 0, height * (ratio + 0.1), fill = "white")
    start_bt["text"] = "Start"
    start_time = 0
    cur_time = 0
    app.update()

    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
    if mp3_fn != "":
        os.system("rm %s" % mp3_fn)
    mp3_fn = wav_fn[:-3] + "mp3"
    os.system("ffmpeg -i %s %s" % (wav_fn, mp3_fn))
    pygame.mixer.music.load(mp3_fn)


def start():
    if start_bt["text"] == "Start":
        start_bt["text"] = "Stop"
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.play(start = start_time)
    elif start_bt["text"] == "Stop":
        start_bt["text"] = "Start"
        pygame.mixer.music.pause()
    app.update()


def reset():
    global cur_time, start_time, line_id
    start_time = 0
    cur_time = 0
    start_bt["text"] = "Start"
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
        time_lab["text"] = "0:0/%d:%d" % (total_time / 60, total_time % 60)
        canvas.delete(line_id)
        line_id = canvas.create_line(0, 0, 0, height * (ratio + 0.1), fill = "white")
    
    app.update()


def save():
    global save_dir
    save_dir = filedialog.askdirectory(initialdir = ".")


def record():
    global record_start, record_end, save_start
    if record_bt["text"] == "Record":
        record_bt["text"] = "Stop"
        record_start = cur_time * framerate
    elif record_bt["text"] == "Stop":
        record_bt["text"] = "Record"
        record_end = cur_time * framerate
        fname = os.path.join(save_dir, "%s%d.wav" % (save_prefix, save_start))
        save_start += 1
        f = wave.open(fname, "wb")
        f.setnchannels(nchannels)
        f.setsampwidth(sampwidth)
        f.setframerate(framerate)
        tmp = data[:, int(record_start):int(record_end)].T
        tmp.shape = 1, -1
        tmp = tmp.astype(np.short)
        f.writeframes(tmp.tostring())
        f.close()
    
    app.update()


def close_callback():
    global close
    close = 1
    if mp3_fn != "":
        os.system("rm %s" % mp3_fn)
    app.destroy()


pygame.mixer.init()
th=threading.Thread(target=time_line)
th.setDaemon(True)
th.start()

app = tk.Tk()
app.title("Audio Tool")
app.geometry("%dx%d" % (width, height))

canvas = tk.Canvas(app, width = width, height = int(height * ratio), bg = "black")
canvas.bind("<Button-1>", click_callback)
canvas.bind('<B1-Motion>', drag_callback)
canvas.pack()

frame = tk.Frame(app)
frame.pack(fill = "both")
open_bt = tk.Button(frame, text = "Open Wav", height = int(height * ratio), bg = "gray", command = open_wav)
open_bt.pack(side = "left", padx = 1)
start_bt = tk.Button(frame, text = "Start", height = int(height * ratio), bg = "gray", command = start)
start_bt.pack(side = "left", padx = 1)
reset_bt = tk.Button(frame, text = "Reset", height = int(height * ratio), bg = "gray", command = reset)
reset_bt.pack(side = "left", padx = 1)
save_bt = tk.Button(frame, text = "Save Dir", height = int(height * ratio), bg = "gray", command = save)
save_bt.pack(side = "left", padx = 1)
record_bt = tk.Button(frame, text = "Record", height = int(height * ratio), bg = "gray", command = record)
record_bt.pack(side = "left", padx = 1)
time_lab = tk.Label(frame, text = "", height = int(height * ratio))
time_lab.pack(side = "right", padx = 1)

app.protocol("WM_DELETE_WINDOW", close_callback)
app.mainloop()

    
