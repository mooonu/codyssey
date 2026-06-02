"""
door_hacking.py
===============
emergency_storage_key.zip 파일의 비밀번호를 병렬 브루트포스로 해독한다.

알고리즘 비교
-----------
1. 기본 알고리즘 (순차 브루트포스, 싱글 프로세스):
   - 모든 후보를 단일 프로세스가 순서대로 시도
   - CPU 코어를 1개만 사용하므로 느림
   - 예상 속도: ~10,000~50,000 시도/초

2. 최적화 알고리즘 (multiprocessing 병렬 탐색 + 조기 종료):
   - CPU 코어 수만큼 워커 프로세스를 생성하여 탐색 공간을 분할 처리
   - 하나의 워커가 비밀번호를 찾으면 Event를 통해 나머지 워커가 즉시 종료
   - 이론상 코어 수에 비례하여 속도 향상 (8코어 → 약 8배 빠름)
   - 왜 빠른지: GIL(Global Interpreter Lock) 우회 가능, 각 코어가 독립적으로
     CPU 연산을 수행하므로 진정한 병렬 처리 달성
"""

import zipfile          # ZIP 파일 비밀번호 시도에 사용
import string           # 문자 집합(digits + ascii_lowercase) 생성에 사용
import itertools        # 카르테시안 곱으로 후보 생성, islice로 청크 분할에 사용
import multiprocessing  # 병렬 프로세스 풀 생성에 사용
import tempfile         # 임시 추출 디렉토리 생성에 사용
import shutil           # 임시 디렉토리 정리(rmtree)에 사용
import os               # 경로 조작에 사용
import time             # 경과 시간 계산에 사용
from datetime import datetime  # 시작 시간 포맷 출력에 사용


# --- 상수 정의 ---
# 탐색할 문자 집합: 숫자(0-9) + 소문자(a-z) = 36자
CHARSET = string.digits + string.ascii_lowercase  # '0123456789abcdefghijklmnopqrstuvwxyz'

# 비밀번호 길이: 6자리 → 36^6 = 2,176,782,336 가지
PASSWORD_LENGTH = 6

# 총 탐색 공간 크기 (36^6)
TOTAL_SPACE = len(CHARSET) ** PASSWORD_LENGTH  # 2,176,782,336

# 한 워커에게 한 번에 전달할 후보 개수
# 너무 작으면 프로세스 간 통신 오버헤드 증가, 너무 크면 조기 종료 지연
CHUNK_SIZE = 50_000

# 공유 카운터 업데이트 주기 (락 경합 최소화 목적)
# 1000번마다 한 번씩 공유 메모리에 기록하여 락 획득 횟수를 줄임
BATCH_UPDATE = 1_000

# 결과 저장 파일명
OUTPUT_FILE = "password.txt"


def _worker(args):
    """
    워커 프로세스 함수 - 후보 비밀번호 목록을 받아 ZIP 파일 해제를 시도한다.

    최상위 레벨에 정의된 이유:
        macOS는 multiprocessing 기본 시작 방식이 'spawn'이므로, 워커 함수를
        pickle 직렬화할 수 있어야 한다. 클래스 내부나 클로저로 정의하면
        pickle 오류가 발생하므로 모듈 최상위에 정의한다.

    Args:
        args (tuple): (zip_path, candidates, found_event, result_queue, shared_counter, counter_lock)
            - zip_path       : ZIP 파일 경로 (str)
            - candidates     : 이 워커가 시도할 비밀번호 목록 (list of str)
            - found_event    : 비밀번호 발견 시 다른 워커에게 알리는 Event
            - result_queue   : 발견한 비밀번호를 메인 프로세스에 전달하는 Queue
            - shared_counter : 전체 시도 횟수를 추적하는 공유 Value
            - counter_lock   : shared_counter 갱신 시 락 경합 방지용 Lock
    """
    # 인자를 명시적 변수로 언패킹 (가독성 향상)
    zip_path, candidates, found_event, result_queue, shared_counter, counter_lock = args

    # 임시 추출 디렉토리 생성 - 각 워커마다 독립된 경로를 가짐
    # mkdtemp()를 사용하는 이유: 여러 워커가 동시에 같은 경로에 추출하면 충돌 발생
    tmp_dir = tempfile.mkdtemp()

    # 로컬 카운터: 공유 메모리 락 획득 비용을 줄이기 위해 로컬에서 누적 후 일괄 반영
    local_count = 0  # 이 워커가 현재 배치에서 시도한 횟수

    try:
        # ZIP 파일을 워커 내부에서 열어 프로세스 간 객체 공유 문제를 방지
        # with 문을 사용하는 이유: 예외 발생 시에도 파일 핸들이 자동 해제됨
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # for 루프로 후보 목록을 순회
            for password in candidates:
                # 다른 워커가 이미 비밀번호를 찾았으면 즉시 루프 탈출 (조기 종료)
                if found_event.is_set():
                    break

                # 로컬 카운터 증가
                local_count += 1

                # BATCH_UPDATE 주기마다 공유 카운터에 반영
                # 이유: 락 획득을 매번 하지 않고 배치로 처리하여 오버헤드 감소
                if local_count % BATCH_UPDATE == 0:
                    with counter_lock:
                        shared_counter.value += BATCH_UPDATE

                try:
                    # extractall에 pwd 파라미터는 반드시 bytes 타입이어야 함
                    # 이유: zipfile 모듈 내부에서 bytes로 비교하기 때문
                    zf.extractall(path=tmp_dir, pwd=password.encode('utf-8'))

                    # 예외 없이 통과했다면 비밀번호가 맞음
                    # found_event.set()으로 다른 모든 워커에게 중단 신호 전송
                    found_event.set()
                    result_queue.put(password)  # 메인 프로세스에 결과 전달
                    return  # 워커 함수 즉시 종료

                except RuntimeError:
                    # zipfile이 잘못된 비밀번호에 대해 RuntimeError를 발생시킴
                    # (예: "Bad password for file ...")
                    continue  # 다음 후보로 진행

                except Exception:
                    # 그 외 예상치 못한 예외도 무시하고 계속 진행
                    continue

        # 루프 종료 후 남은 로컬 카운터 반영
        remaining = local_count % BATCH_UPDATE
        if remaining > 0:
            with counter_lock:
                shared_counter.value += remaining

    finally:
        # 임시 디렉토리 정리 - 예외 발생 여부와 무관하게 반드시 실행
        # finally 블록을 사용하는 이유: 정상 종료, 예외, 조기 종료 모두에서 정리 보장
        shutil.rmtree(tmp_dir, ignore_errors=True)


def unlock_zip():
    """
    메인 진입점 함수 - 병렬 브루트포스로 ZIP 파일의 비밀번호를 탐색한다.

    처리 흐름:
        1. ZIP 파일 유효성 확인
        2. multiprocessing 리소스 초기화 (Manager, Pool)
        3. 후보 생성기(itertools.product)로 청크 단위 작업 배포
        4. 메인 루프에서 5초마다 진행 상황 출력
        5. 비밀번호 발견 또는 탐색 완료 시 결과 저장
    """
    # ZIP 파일 경로 - 스크립트와 같은 디렉토리에 있다고 가정
    zip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emergency_storage_key.zip')

    # --- ZIP 파일 사전 검증 ---
    # try-except를 사용하는 이유: 파일 부재/권한 오류를 명확한 메시지로 처리
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            _ = zf.namelist()  # 파일 목록만 읽어 유효한 ZIP인지 확인
    except FileNotFoundError:
        print(f"[오류] ZIP 파일을 찾을 수 없습니다: {zip_path}")
        return
    except zipfile.BadZipFile:
        print(f"[오류] 유효하지 않은 ZIP 파일입니다: {zip_path}")
        return
    except PermissionError:
        print(f"[오류] ZIP 파일에 접근 권한이 없습니다: {zip_path}")
        return

    # --- 시작 정보 출력 ---
    start_time = time.time()                          # 경과 시간 계산 기준
    start_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 사람이 읽기 좋은 형식
    print(f"[시작] {start_dt}  |  탐색 공간: {TOTAL_SPACE:,}")

    # --- 워커 수 결정 ---
    # cpu_count()를 사용하는 이유: 시스템 코어 수에 맞게 자동으로 병렬화 수준 결정
    num_workers = multiprocessing.cpu_count()
    print(f"[정보] 워커 프로세스 수: {num_workers}  |  청크 크기: {CHUNK_SIZE:,}")

    # --- multiprocessing 공유 리소스 초기화 ---
    # Manager를 사용하는 이유: Value는 fork 방식에서만 공유 가능하지만,
    # spawn 방식(macOS 기본)에서는 Manager를 통해야 프로세스 간 메모리 공유 가능
    manager = multiprocessing.Manager()

    # found_event: 비밀번호 발견 시 모든 워커에게 중단 신호를 보내는 플래그
    found_event = manager.Event()

    # result_queue: 워커가 발견한 비밀번호를 메인 프로세스에 전달하는 큐
    result_queue = manager.Queue()

    # shared_counter: 전체 시도 횟수 추적 (진행 상황 출력용)
    shared_counter = manager.Value('i', 0)

    # counter_lock: shared_counter 갱신 시 경쟁 조건 방지
    counter_lock = manager.Lock()

    # --- 후보 생성기 초기화 ---
    # itertools.product가 적합한 이유: 메모리에 전체 목록을 올리지 않고
    # 필요할 때마다 생성하는 제너레이터 방식으로 메모리 효율적
    # repeat=PASSWORD_LENGTH: 6자리 조합 생성
    candidate_gen = (
        ''.join(combo)
        for combo in itertools.product(CHARSET, repeat=PASSWORD_LENGTH)
    )

    # 발견된 비밀번호를 저장할 변수 (None이면 미발견)
    found_password = None

    # --- Pool 생성 및 작업 배포 ---
    # Pool을 with 문으로 사용하는 이유: 예외 발생 시에도 워커 프로세스가 정리됨
    with multiprocessing.Pool(processes=num_workers) as pool:
        # 비동기 결과 핸들 목록 - apply_async 결과를 추적하기 위해 사용
        # list comprehension 대신 일반 리스트를 사용하는 이유:
        # 제너레이터가 소진되기 전까지만 청크를 생성해야 하므로 루프로 제어
        pending_results = []  # 아직 완료되지 않은 작업 핸들 목록
        last_report_time = start_time  # 마지막 진행 상황 출력 시각

        # 메인 루프: 후보를 청크 단위로 워커에 배포하고, 결과를 모니터링
        while not found_event.is_set():
            # itertools.islice로 CHUNK_SIZE 개만큼 후보를 잘라냄
            # list()로 변환하는 이유: islice는 제너레이터이므로 pickle 불가능,
            # apply_async로 워커에 전달하려면 직렬화 가능한 리스트 필요
            chunk = list(itertools.islice(candidate_gen, CHUNK_SIZE))

            if not chunk:
                # 더 이상 후보가 없으면 탐색 완료 (비밀번호 없음)
                break

            # apply_async로 비동기 배포
            # 인자 구조: _worker 함수가 단일 tuple을 받으므로 args에 tuple을 감쌈
            async_result = pool.apply_async(
                _worker,
                args=((zip_path, chunk, found_event, result_queue, shared_counter, counter_lock),)
            )
            pending_results.append(async_result)

            # 완료된 작업 핸들을 목록에서 제거하여 메모리 누수 방지
            # list comprehension을 사용하는 이유: 한 번에 조건부 필터링으로 간결
            pending_results = [r for r in pending_results if not r.ready()]

            # 5초마다 진행 상황 출력
            current_time = time.time()
            if current_time - last_report_time >= 5.0:
                elapsed = current_time - start_time
                # timedelta 없이 수동으로 HH:MM:SS 형식 구성
                elapsed_str = f"{int(elapsed // 3600):02d}:{int((elapsed % 3600) // 60):02d}:{int(elapsed % 60):02d}"
                count = shared_counter.value
                speed = int(count / elapsed) if elapsed > 0 else 0
                print(f"[진행] 경과: {elapsed_str}  |  시도 횟수: {count:,}  |  속도: ~{speed:,}/s")
                last_report_time = current_time

            # 비밀번호를 이미 찾았으면 추가 배포 불필요
            if found_event.is_set():
                break

        # 모든 워커가 완료될 때까지 대기 (Pool이 with 블록을 벗어나면 join)
        pool.terminate()  # found_event 설정 시 남은 작업 즉시 중단

    # --- 결과 처리 ---
    if not result_queue.empty():
        found_password = result_queue.get()

    elapsed_total = time.time() - start_time
    elapsed_str = f"{int(elapsed_total // 3600):02d}:{int((elapsed_total % 3600) // 60):02d}:{int(elapsed_total % 60):02d}"
    total_tried = shared_counter.value

    if found_password:
        print(f"[성공] 비밀번호 발견: {found_password}  |  경과: {elapsed_str}  |  총 시도: {total_tried:,}")

        # 비밀번호를 파일로 저장
        # try-except를 사용하는 이유: 저장 실패 시에도 콘솔에는 결과가 출력되어야 함
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILE)
        try:
            # with 문으로 파일을 열어 예외 발생 시에도 핸들 자동 해제 보장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(found_password)
            print(f"[저장] 비밀번호가 {output_path}에 저장되었습니다.")
        except FileNotFoundError:
            print(f"[경고] 저장 경로를 찾을 수 없습니다: {output_path}")
        except PermissionError:
            print(f"[경고] 파일 쓰기 권한이 없습니다: {output_path}")
    else:
        print(f"[실패] 비밀번호를 찾지 못했습니다.  |  경과: {elapsed_str}  |  총 시도: {total_tried:,}")


# --- 진입점 가드 ---
# if __name__ == '__main__' 가드가 필요한 이유:
# macOS에서 spawn 방식은 모듈을 재임포트하므로, 가드 없이 unlock_zip()을 호출하면
# 워커 프로세스 생성 시마다 재귀적으로 unlock_zip()이 실행되는 무한 루프 발생
if __name__ == '__main__':
    # spawn 시작 방식 강제 설정
    # force=True를 사용하는 이유: 이미 다른 방식이 설정된 경우에도 덮어쓰기 위함
    multiprocessing.set_start_method('spawn', force=True)
    unlock_zip()
