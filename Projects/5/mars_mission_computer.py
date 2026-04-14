import platform  # OS 이름, 버전, CPU 아키텍처 정보 수집
import os        # CPU 코어 수 조회 (os.cpu_count())
import json      # 수집 결과를 JSON 형식으로 직렬화
import time      # get_mission_computer_load의 5초 대기 주기 구현
import psutil    # 메모리 전체 크기 및 실시간 CPU/메모리 사용률 수집


class MissionComputer:
    # MissionComputer: 화성 미션 컴퓨터의 시스템 정보 및 실시간 부하를 수집·출력하는 클래스

    def __init__(self):
        # __init__: 객체 생성 시 setting.txt를 읽어 출력 항목 필터를 초기화한다.
        # 인스턴스 변수 self.settings에 저장함으로써 모든 메서드가 공유할 수 있도록 한다.
        self.settings = self._load_settings()

    def _load_settings(self):
        # _load_settings: setting.txt 파일을 읽어 {항목명: bool} 형태의 dict를 반환한다.
        # 파일이 없을 경우 전 항목을 True로 설정한 기본값 dict를 반환하여 안전하게 동작하도록 한다.

        # 기본값 dict: setting.txt가 없을 때 모든 항목을 활성화(True)하기 위해 미리 정의한다.
        # dict 리터럴을 사용하는 이유: 고정된 키 목록을 명시적으로 표현하기 위해
        default = {
            'os_name': True,
            'os_version': True,
            'cpu_type': True,
            'cpu_core_count': True,
            'memory_size': True,
            'cpu_usage': True,
            'memory_usage': True,
        }

        # try-except: 파일 부재(FileNotFoundError) 상황을 우아하게 처리하기 위해 사용한다.
        # 예외 발생 시 기본값을 반환하여 프로그램이 중단되지 않도록 한다.
        try:
            # with 문: 파일을 열고 블록이 끝나면 자동으로 닫아주기 때문에
            # 명시적으로 f.close()를 호출하지 않아도 자원 누수가 없다.
            with open('setting.txt', 'r') as f:
                settings = {}

                # for 루프: 파일의 각 줄을 순서대로 처리하기 위해 사용한다.
                # 줄 수가 가변적이므로 반복 구조가 필요하다.
                for line in f:
                    # strip(): 줄 끝 개행 문자(\n)와 앞뒤 공백을 제거한다.
                    line = line.strip()

                    # 빈 줄이나 주석(#) 줄은 건너뛴다.
                    if not line or line.startswith('#'):
                        continue

                    # split('=', 1): '=' 기준으로 최대 1회 분리하여
                    # key와 value로 나눈다. maxsplit=1을 지정하는 이유는
                    # value 안에 '='이 포함될 경우에도 안전하게 처리하기 위해서다.
                    parts = line.split('=', 1)
                    if len(parts) != 2:
                        continue

                    # 변수명 key, value: 설정 파일의 키-값 쌍을 표현하는 가장 직관적인 이름
                    key = parts[0].strip()
                    value = parts[1].strip()

                    # lower() 비교: 'True', 'TRUE', 'true' 등 대소문자 변형을 모두 허용하기 위해
                    settings[key] = value.lower() == 'true'

            return settings

        except FileNotFoundError:
            # FileNotFoundError: setting.txt가 없을 경우 기본값 dict를 반환하여
            # 프로그램이 정상 동작을 유지하도록 한다.
            return default

    def get_mission_computer_info(self):
        # get_mission_computer_info: 정적 시스템 정보(OS, CPU, 메모리)를 수집하여
        # self.settings 필터를 적용한 뒤 JSON 형식으로 출력한다.
        # '정적'인 이유: 부팅 이후 거의 변하지 않는 하드웨어/OS 속성을 수집하기 때문

        # try-except Exception: platform/psutil 호출 중 예상치 못한 오류가 발생해도
        # 프로그램이 중단되지 않도록 전체 수집 블록을 감싼다.
        # 예외 발생 시 해당 값을 'N/A'로 대체하여 부분적 정보라도 출력한다.
        try:
            # 후보 데이터 dict: 모든 항목을 먼저 수집한 뒤 필터링하는 방식을 택한다.
            # 이유: 수집과 필터링 로직을 분리하여 코드 가독성을 높이기 위해
            candidates = {}

            # os_name: 현재 운영체제 이름 (예: 'Darwin', 'Linux', 'Windows')
            candidates['os_name'] = platform.system()

            # os_version: 커널/OS 세부 버전 문자열
            candidates['os_version'] = platform.version()

            # cpu_type: CPU 프로세서 아키텍처/모델명
            candidates['cpu_type'] = platform.processor()

            # cpu_core_count: 논리 CPU 코어 수 (os.cpu_count()가 None이면 'N/A' 대체)
            # or 연산자: None 반환 방어를 위해 사용
            candidates['cpu_core_count'] = os.cpu_count() or 'N/A'

            # memory_size: 전체 물리 메모리를 GB 단위로 환산하여 소수점 2자리로 반올림
            # 1024**3으로 나누는 이유: psutil은 바이트 단위로 반환하므로 GB 변환에 필요
            total_bytes = psutil.virtual_memory().total
            candidates['memory_size'] = round(total_bytes / (1024 ** 3), 2)

        except Exception:
            # 수집 중 예외 발생 시 모든 항목을 'N/A'로 초기화하여 빈 출력을 방지한다.
            candidates = {
                'os_name': 'N/A',
                'os_version': 'N/A',
                'cpu_type': 'N/A',
                'cpu_core_count': 'N/A',
                'memory_size': 'N/A',
            }

        # dict comprehension: self.settings[key]가 True인 항목만 결과에 포함시킨다.
        # dict comprehension을 사용하는 이유: 한 줄로 필터링된 dict를 생성할 수 있어 간결하다.
        # .get(key, False): settings에 해당 키가 없을 경우 False를 반환하여 KeyError를 방지한다.
        result = {
            key: value
            for key, value in candidates.items()
            if self.settings.get(key, False)
        }

        # json.dumps: Python dict를 들여쓰기 4칸의 사람이 읽기 좋은 JSON 문자열로 변환한다.
        print(json.dumps(result, indent=4))

    def get_mission_computer_load(self):
        # get_mission_computer_load: 5초마다 실시간 CPU 사용률과 메모리 사용률을 수집하여
        # JSON 형식으로 반복 출력한다.
        # 사용자가 Ctrl+C를 누를 때까지 무한 반복한다.

        # try-except KeyboardInterrupt: Ctrl+C 신호를 감지하여
        # while True 루프를 안전하게 종료하고 종료 메시지를 출력한다.
        try:
            # while True: 종료 신호(KeyboardInterrupt)가 오기 전까지 무한 반복한다.
            # 실시간 모니터링이므로 반복 횟수를 미리 알 수 없어 while True가 적합하다.
            while True:
                # 실시간 수집 후보 dict
                candidates = {}

                # cpu_percent(interval=1): 1초 동안 측정하여 CPU 사용률(%)을 반환한다.
                # interval 인수를 주는 이유: interval=0이면 이전 호출 이후 경과 시간 기준으로
                # 측정하여 부정확할 수 있기 때문에 명시적 측정 구간을 지정한다.
                candidates['cpu_usage'] = psutil.cpu_percent(interval=1)

                # virtual_memory().percent: 현재 메모리 사용률(%)을 반환한다.
                candidates['memory_usage'] = psutil.virtual_memory().percent

                # dict comprehension: settings 필터를 적용하여 활성화된 항목만 출력한다.
                result = {
                    key: value
                    for key, value in candidates.items()
                    if self.settings.get(key, False)
                }

                print(json.dumps(result, indent=4))

                # time.sleep(5): 다음 수집까지 5초 대기한다.
                # sleep을 사용하는 이유: CPU 자원을 과도하게 소비하지 않도록 수집 주기를 제한하기 위해
                time.sleep(5)

        except KeyboardInterrupt:
            # KeyboardInterrupt: 사용자가 Ctrl+C를 입력했을 때 발생하는 예외
            # 무한 루프를 정상 종료 경로로 빠져나오기 위해 사용한다.
            print('System stopped....')


# 모듈 수준 직접 호출: 과제 명세에 따라 if __name__ == '__main__': 없이 작성한다.
# 인스턴스 변수명 runComputer: 과제 명세에서 지정한 이름이므로 그대로 사용한다.
runComputer = MissionComputer()
runComputer.get_mission_computer_info()
runComputer.get_mission_computer_load()
