import random   # 난수 생성을 위한 표준 라이브러리
import datetime  # 현재 날짜/시간 기록을 위한 표준 라이브러리


class DummySensor:
    # 실제 센서 대신 랜덤 값을 생성하는 더미 센서 클래스

    def __init__(self):
        # 인스턴스 생성 시 6개의 환경 센서 항목을 딕셔너리로 초기화
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

    def log_env(self):
        # 현재 env_values와 타임스탬프를 sensor_log.csv 파일에 한 줄 추가
        # 파일이 없으면 헤더를 먼저 작성한 뒤 데이터 행을 추가
        log_file = 'sensor_log.csv'
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        v = self.env_values

        headers = [
            'date_time',
            'mars_base_internal_temperature',
            'mars_base_external_temperature',
            'mars_base_internal_humidity',
            'mars_base_external_illuminance',
            'mars_base_internal_co2',
            'mars_base_internal_oxygen',
        ]
        row = [
            now,
            v['mars_base_internal_temperature'],
            v['mars_base_external_temperature'],
            v['mars_base_internal_humidity'],
            v['mars_base_external_illuminance'],
            v['mars_base_internal_co2'],
            v['mars_base_internal_oxygen'],
        ]

        try:
            with open(log_file, 'r') as f:
                has_header = f.readline().strip() != ''
        except FileNotFoundError:
            has_header = False

        with open(log_file, 'a') as f:
            if not has_header:
                f.write(','.join(headers) + '\n')
            f.write(','.join(str(val) for val in row) + '\n')

    def get_env(self):
        # 현재 env_values 딕셔너리를 반환하고 로그 파일에 기록
        self.log_env()
        return self.env_values


if __name__ == '__main__':
    # 이 파일을 직접 실행할 때만 아래 코드가 동작
    # (다른 파일에서 import할 경우 자동 실행되지 않음)

    ds = DummySensor()  # DummySensor 인스턴스 생성
    ds.set_env()        # 랜덤 환경 값 생성 및 저장
    env = ds.get_env()  # 저장된 환경 값 딕셔너리 가져오기
    print(env)          # 결과 출력
