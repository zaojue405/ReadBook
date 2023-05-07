import os
import subprocess
import threading
import queue


def synthesize_audio(text, audio_queue):
    command = f'edge-tts --voice zh-CN-XiaoyiNeural --text "{text}" --write-media book.mp3'
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
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= start_line:
                lines.append(line)
                if len(lines) >= 100:
                    break
    return lines, start_line + len(lines)

def save_progress(progress_file, line_number):
    with open(progress_file, 'w') as f:
        f.write(str(line_number))

def load_progress(progress_file):
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            content = f.read().strip()
            try:
                return int(content)
            except ValueError:
                print(f'warning：cant load from {progress_file} ,start read from beginning。')
                return 0
    return 0



def main():
    file_path = input('input your TXT path：')
    progress_file = 'progress.txt'
    start_line = load_progress(progress_file)

    audio_queue = queue.Queue()
    play_lock = threading.Lock()

    try:
        play_thread = threading.Thread(target=play_audio, args=(audio_queue, play_lock))
        play_thread.start()

        while True:
            lines, next_start_line = read_file(file_path, start_line)
            if not lines:
                print('already finished。')
                break

            for line in lines:
                line = line.strip()
                if len(line) > 0:
                    synthesize_audio(line, audio_queue)
                    with play_lock:
                        start_line += 1
                        save_progress(progress_file, start_line)

           

        audio_queue.put('STOP')
        play_thread.join()
    except KeyboardInterrupt:
        print('\ndetect Ctrl+C，Saving...')
        save_progress(progress_file, start_line)
        print('already Saved')

if __name__ == "__main__":
    main()