import os
import subprocess
import threading
import queue
import json
"""
voice  en-US-AriaNeural
       zh-CN-XiaoxiaoNeural

"""
def synthesize_audio(text, audio_queue):
    command = f'edge-tts --voice zh-CN-XiaoxiaoNeural --text "{text}" --write-media book.mp3'
    subprocess.run(command, shell=True, check=True)
    audio_queue.put('book.mp3')


def play_audio(audio_queue, play_lock):
    while True:
        audio_file = audio_queue.get()
        if audio_file == 'STOP':
            break
        with play_lock:
            command = ["mpv.exe", "-vo", "null", audio_file]
            subprocess.run(command, check=True)
        audio_queue.task_done()


def read_file(file_path, start_line):
    lines = []
    with open(file_path, 'r', encoding='gbk') as f:
        for i, line in enumerate(f):
            if i >= start_line:
                lines.append(line)
                if len(lines) >= 100:
                    break
    return lines, start_line + len(lines)

def save_progress(progress_file, book_path, current_line):
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        progress = {}
    progress[book_path] = current_line
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f)


def load_progress(progress_file, book_path):
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        progress = {}

    return progress.get(book_path, 0)


def main():
    file_path = input('请输入TXT文件路径：')
    progress_file = 'progress.txt'
    start_line = load_progress(progress_file, file_path)

    audio_queue = queue.Queue()
    play_lock = threading.Lock()

    try:
        play_thread = threading.Thread(target=play_audio, args=(audio_queue, play_lock))
        play_thread.start()

        while True:
            lines, next_start_line = read_file(file_path, start_line)
            if not lines:
                print('已经读完整个文件。')
                break

            for line in lines:
                line = line.strip()
                if len(line) > 0:
                    synthesize_audio(line, audio_queue)
                    with play_lock:
                        start_line += 1
                        save_progress(progress_file,  file_path,start_line)

           

        audio_queue.put('STOP')
        play_thread.join()
    except KeyboardInterrupt:
        print('\n检测到 Ctrl+C，正在保存进度...')
        save_progress(progress_file, file_path,start_line)
        print('进度已保存。')
    finally:
        audio_queue.put('STOP')
        play_thread.join()

if __name__ == "__main__":
    main()