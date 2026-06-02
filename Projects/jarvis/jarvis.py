import os
import wave
import datetime

import numpy as np
import sounddevice as sd


RECORDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'records')
SAMPLE_RATE = 44100
CHANNELS = 1
SAMPLE_WIDTH = 2  # int16 = 2 bytes


def ensure_records_dir():
    if not os.path.exists(RECORDS_DIR):
        os.makedirs(RECORDS_DIR)


def list_microphones():
    devices = sd.query_devices()
    print('\n사용 가능한 마이크 목록:')
    mic_found = False
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f'  [{i}] {device["name"]}')
            mic_found = True
    if not mic_found:
        print('  인식된 마이크가 없습니다.')


def record_audio(duration):
    print(f'\n{duration}초 동안 녹음을 시작합니다...')
    audio_data = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='int16'
    )
    sd.wait()
    print('녹음이 완료되었습니다.')
    return audio_data


def save_audio(audio_data):
    ensure_records_dir()
    now = datetime.datetime.now()
    filename = now.strftime('%Y%m%d-%H%M%S') + '.wav'
    filepath = os.path.join(RECORDS_DIR, filename)

    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())

    print(f'파일이 저장되었습니다: {filepath}')


def show_recordings_by_date_range(start_date, end_date):
    ensure_records_dir()
    all_files = os.listdir(RECORDS_DIR)
    wav_files = [f for f in all_files if f.endswith('.wav')]

    print(
        f'\n{start_date.strftime("%Y-%m-%d")} ~ {end_date.strftime("%Y-%m-%d")} '
        f'범위의 녹음 파일:'
    )

    found = []
    for filename in sorted(wav_files):
        try:
            date_part = os.path.splitext(filename)[0]
            file_datetime = datetime.datetime.strptime(date_part, '%Y%m%d-%H%M%S')
            file_date = file_datetime.date()
            if start_date <= file_date <= end_date:
                found.append(filename)
        except ValueError:
            continue

    if found:
        for f in found:
            print(f'  {f}')
    else:
        print('  해당 범위의 녹음 파일이 없습니다.')


def parse_date(date_str):
    return datetime.datetime.strptime(date_str, '%Y%m%d').date()


def main():
    print('=== Jarvis 음성 녹음 시스템 ===')

    while True:
        print('\n[1] 녹음 시작')
        print('[2] 날짜 범위로 녹음 파일 보기')
        print('[3] 마이크 목록 보기')
        print('[4] 종료')

        choice = input('\n선택: ').strip()

        if choice == '1':
            try:
                duration_input = input('녹음 시간(초): ').strip()
                duration = int(duration_input)
                if duration <= 0:
                    print('녹음 시간은 1초 이상이어야 합니다.')
                    continue
                audio_data = record_audio(duration)
                save_audio(audio_data)
            except ValueError:
                print('올바른 숫자를 입력해주세요.')
            except sd.PortAudioError as e:
                print(f'마이크 오류가 발생했습니다: {e}')

        elif choice == '2':
            try:
                start_str = input('시작 날짜 (YYYYMMDD): ').strip()
                end_str = input('종료 날짜 (YYYYMMDD): ').strip()
                start_date = parse_date(start_str)
                end_date = parse_date(end_str)
                if start_date > end_date:
                    print('시작 날짜가 종료 날짜보다 늦을 수 없습니다.')
                    continue
                show_recordings_by_date_range(start_date, end_date)
            except ValueError:
                print('날짜 형식이 올바르지 않습니다. (예: 20260602)')

        elif choice == '3':
            list_microphones()

        elif choice == '4':
            print('종료합니다.')
            break

        else:
            print('올바른 메뉴를 선택해주세요.')


if __name__ == '__main__':
    main()
