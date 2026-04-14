import random  # 센서 랜덤값 생성을 위한 표준 라이브러리
import json    # 환경값을 JSON 형태로 출력하기 위한 표준 라이브러리
import time    # 5초 주기 대기(sleep)를 위한 표준 라이브러리


class DummySensor:
    # 실제 센서 대신 랜덤 값을 생성하는 더미 센서 클래스
    # Projects/3의 DummySensor에서 log_env/datetime 관련 코드를 제거한 버전

    def __init__(self):
        # 인스턴스 생성 시 6개의 환경 센서 항목을 딕셔너리로 초기화
        # dict를 사용하는 이유: 키-값 쌍으로 센서 이름과 측정값을 명확하게 연결
        # 초기값은 0 — set_env() 호출 전까지의 플레이스홀더
        self.env_values = {
            'mars_base_internal_temperature': 0,  # 기지 내부 온도 (도)
            'mars_base_external_temperature': 0,  # 기지 외부 온도 (도)
            'mars_base_internal_humidity': 0,     # 기지 내부 습도 (%)
            'mars_base_external_illuminance': 0,  # 기지 외부 광량 (W/m2)
            'mars_base_internal_co2': 0,          # 기지 내부 CO2 농도 (%)
            'mars_base_internal_oxygen': 0,       # 기지 내부 산소 농도 (%)
        }

    def set_env(self):
        # 각 센서 항목에 지정된 범위 내의 랜덤 실수 값을 생성하여 저장
        # random.uniform(a, b): a 이상 b 이하의 임의 실수 반환
        # round(값, 자릿수): 부동소수점 오차를 줄이고 가독성 있는 정밀도로 반올림
        self.env_values['mars_base_internal_temperature'] = round(random.uniform(18, 30), 1)   # 18~30도, 소수 1자리
        self.env_values['mars_base_external_temperature'] = round(random.uniform(0, 21), 1)    # 0~21도, 소수 1자리
        self.env_values['mars_base_internal_humidity'] = round(random.uniform(50, 60), 1)      # 50~60%, 소수 1자리
        self.env_values['mars_base_external_illuminance'] = round(random.uniform(500, 715), 1) # 500~715 W/m2, 소수 1자리
        self.env_values['mars_base_internal_co2'] = round(random.uniform(0.02, 0.1), 2)        # 0.02~0.1%, 소수 2자리
        self.env_values['mars_base_internal_oxygen'] = round(random.uniform(4, 7), 2)          # 4~7%, 소수 2자리

    def get_env(self):
        # 현재 env_values 딕셔너리를 반환
        # log_env/datetime 의존성 없이 순수하게 값만 반환
        return self.env_values


class MissionComputer:
    # 더미 센서로부터 데이터를 수집하고 주기적으로 평균을 출력하는 미션 컴퓨터 클래스

    def __init__(self):
        # 미션 컴퓨터가 관리하는 6개의 환경값 딕셔너리 초기화
        # self.env_values: 현재 사이클의 최신 센서값을 보관
        # self.ds: DummySensor 인스턴스 — 실제 센서 역할 수행
        self.env_values = {
            'mars_base_internal_temperature': 0,
            'mars_base_external_temperature': 0,
            'mars_base_internal_humidity': 0,
            'mars_base_external_illuminance': 0,
            'mars_base_internal_co2': 0,
            'mars_base_internal_oxygen': 0,
        }
        self.ds = DummySensor()  # 센서 인스턴스를 속성으로 보관해 재사용

    def get_sensor_data(self):
        # 5초 간격으로 센서 데이터를 읽고 JSON 출력, 60회마다 평균을 출력하는 메서드
        # cycle: 몇 번 읽었는지 카운트하는 변수명 — 반복 횟수를 명시적으로 표현
        # accumulator: 평균 계산을 위해 값을 누산(accumulate)하는 딕셔너리
        cycle = 0
        accumulator = {key: 0 for key in self.env_values}
        # dict comprehension을 사용하는 이유: env_values 키 목록과 동기화된
        # 누산 딕셔너리를 한 줄로 간결하게 초기화

        # try-except를 사용하는 이유: Ctrl+C(KeyboardInterrupt) 발생 시
        # 프로그램이 강제 종료되기 전에 종료 메시지를 출력하기 위함
        try:
            # while True를 사용하는 이유: 사용자가 직접 중단할 때까지
            # 무한 반복으로 센서 데이터를 지속 수집해야 하기 때문
            while True:
                # 센서에서 새로운 랜덤값 생성
                self.ds.set_env()

                # dict.copy()를 사용하는 이유: DummySensor의 env_values를
                # 직접 참조하지 않고 독립적인 복사본으로 저장해 나중에
                # 센서값이 변경되어도 이번 사이클 값이 보존되도록 함
                self.env_values = self.ds.get_env().copy()

                # json.dumps로 indent=4 적용해 사람이 읽기 쉬운 JSON 형식 출력
                print(json.dumps(self.env_values, indent = 4))

                # for 루프를 사용하는 이유: 6개의 키 각각에 대해
                # 동일한 누산 연산을 반복하므로 코드 중복 없이 처리
                for key in self.env_values:
                    accumulator[key] += self.env_values[key]

                cycle += 1  # 읽기 완료 후 카운트 증가

                # 60회마다 평균 출력 후 누산기 초기화
                # cycle % 60 == 0: 나머지 연산으로 60의 배수 판별
                if cycle % 60 == 0:
                    # dict comprehension으로 각 키의 평균값을 담은 딕셔너리 생성
                    # round 소수 2자리: 평균값의 정밀도를 적절히 유지
                    average = {key: round(accumulator[key] / 60, 2) for key in accumulator}
                    print('---sensor average (last 60 cycles)---')
                    print(json.dumps(average, indent = 4))

                    # 평균 출력 후 누산기 초기화 — 다음 60사이클을 위해 0으로 리셋
                    accumulator = {key: 0 for key in self.env_values}

                # time.sleep을 사용하는 이유: 5초 주기로 센서를 읽어
                # CPU 자원을 낭비하지 않으면서 실시간 모니터링 구현
                time.sleep(5)

        except KeyboardInterrupt:
            # Ctrl+C 입력 시 루프를 탈출하고 종료 메시지 출력
            # 오탈자 'Sytem'은 과제 명세에 명시된 그대로 유지
            print('Sytem stoped....')


# 모듈 수준에서 인스턴스화 — if __name__ == '__main__': 없이 직접 실행
# RunComputer: 미션 컴퓨터 실행 인스턴스임을 명확히 표현하는 변수명
RunComputer = MissionComputer()
RunComputer.get_sensor_data()
