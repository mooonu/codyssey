LOG_FILE = 'mission_computer_main.log'
TROUBLE_FILE = 'trouble.log'

TROUBLE_KEYWORDS = ('unstable', 'explosion', 'error', 'fail', 'critical', 'warning')


def read_log_lines(filepath):
    lines = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)
    return lines


def parse_logs(lines):
    header = lines[0]
    entries = []
    for line in lines[1:]:
        parts = line.split(',', 2)
        if len(parts) == 3:
            entries.append({
                'timestamp': parts[0],
                'event': parts[1],
                'message': parts[2],
                'raw': line,
            })
    return header, entries


def is_trouble(entry):
    event = entry['event'].lower()
    message = entry['message'].lower()
    if event in ('warning', 'error', 'critical'):
        return True
    for keyword in TROUBLE_KEYWORDS:
        if keyword in message:
            return True
    return False


def print_logs(header, entries):
    print(header)
    for entry in entries:
        print(entry['raw'])


def print_logs_reversed(header, entries):
    sorted_entries = sorted(entries, key=lambda e: e['timestamp'], reverse=True)
    print(header)
    for entry in sorted_entries:
        print(entry['raw'])


def save_trouble_logs(header, entries, filepath):
    trouble_entries = [e for e in entries if is_trouble(e)]
    if not trouble_entries:
        print('문제 로그 없음.')
        return
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(header + '\n')
        for entry in trouble_entries:
            f.write(entry['raw'] + '\n')
    print(f'문제 로그 {len(trouble_entries)}건 저장: {filepath}')


def main():
    print('Hello Mars')
    print()

    try:
        lines = read_log_lines(LOG_FILE)
    except FileNotFoundError:
        print(f'파일을 찾을 수 없음: {LOG_FILE}')
        return
    except PermissionError:
        print(f'파일 접근 권한 없음: {LOG_FILE}')
        return
    except Exception as e:
        print(f'파일 읽기 오류: {e}')
        return

    if len(lines) < 2:
        print('로그 데이터 없음.')
        return

    header, entries = parse_logs(lines)

    print('=== 전체 로그 ===')
    print_logs(header, entries)
    print()

    print('=== 시간 역순 정렬 ===')
    print_logs_reversed(header, entries)
    print()

    print('=== 문제 로그 저장 ===')
    try:
        save_trouble_logs(header, entries, TROUBLE_FILE)
    except PermissionError:
        print(f'파일 쓰기 권한 없음: {TROUBLE_FILE}')
    except Exception as e:
        print(f'파일 저장 오류: {e}')


main()
