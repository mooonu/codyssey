import csv
import logging
import pickle # 객체 -> 바이트 변환 , 이진 파일로 저장할 수 있는 모듈

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('mars_inventory.log', encoding='utf-8'),
        logging.StreamHandler(),
    ]
)

CSV_FILE = 'Mars_Base_Inventory_List.csv'
DANGER_CSV_FILE = 'Mars_Base_Inventory_danger.csv'
BIN_FILE = 'Mars_Base_Inventory_List.bin'
FLAMMABILITY_THRESHOLD = 0.7


def read_csv():
    """STEP 1: CSV 파일 내용을 읽어서 화면에 출력한다.

    파일이 없거나 읽을 수 없을 때는 오류 메시지를 로그에 기록하고 종료한다.
    """
    try:
        with open(CSV_FILE, encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                print(row)
        logging.info('CSV 파일 읽기 완료: %s', CSV_FILE)
    except FileNotFoundError:
        logging.error('파일을 찾을 수 없습니다: %s', CSV_FILE)
    except IOError as e:
        logging.error('파일 읽기 오류: %s', e)


def load_csv_as_list():
    """STEP 2: CSV 파일 내용을 읽어서 Python 리스트로 변환한다.

    각 행은 딕셔너리로 저장되고, Flammability 값은 숫자(float)로 변환된다.
    변환에 실패한 값은 0.0으로 처리된다.
    오류 발생 시 빈 리스트를 반환한다.
    """
    inventory = []
    try:
        with open(CSV_FILE, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row['Flammability'] = float(row['Flammability'])
                except ValueError:
                    logging.warning(
                        '인화성 지수 변환 실패, 0.0으로 처리: %s', row.get('Substance')
                    )
                    row['Flammability'] = 0.0
                inventory.append(row)
        logging.info('리스트 변환 완료: 총 %d개 항목', len(inventory))
    except FileNotFoundError:
        logging.error('파일을 찾을 수 없습니다: %s', CSV_FILE)
    except IOError as e:
        logging.error('파일 읽기 오류: %s', e)
    return inventory


def sort_by_flammability(inventory):
    """STEP 3: 인화성 지수가 높은 순서로 리스트를 정렬한다.

    원본 리스트는 변경하지 않고 새로운 정렬된 리스트를 반환한다.
    """
    sorted_inventory = sorted(
        inventory,
        key=lambda item: item['Flammability'],
        reverse=True
    )
    if sorted_inventory:
        highest = sorted_inventory[0]['Flammability']
        lowest = sorted_inventory[-1]['Flammability']
        logging.info('정렬 완료: 최고 인화성 %.2f, 최저 인화성 %.2f', highest, lowest)
    return sorted_inventory


def filter_dangerous(sorted_inventory):
    """STEP 4: 인화성 지수가 0.7 이상인 물질만 골라서 화면에 출력한다.

    FLAMMABILITY_THRESHOLD(0.7) 이상인 항목만 포함된 새 리스트를 반환한다.
    해당 항목이 없으면 안내 메시지를 출력한다.
    """
    dangerous = [
        item for item in sorted_inventory
        if item['Flammability'] >= FLAMMABILITY_THRESHOLD
    ]
    if dangerous:
        for item in dangerous:
            print(item)
        logging.info('위험 물질 필터링 완료: %d개 항목', len(dangerous))
    else:
        print('인화성 지수 0.7 이상 항목 없음')
        logging.warning('인화성 지수 %.1f 이상 항목이 없습니다.', FLAMMABILITY_THRESHOLD)
    return dangerous


def save_dangerous_csv(dangerous):
    """STEP 5: 인화성 지수 0.7 이상인 목록을 CSV 파일로 저장한다.

    저장 파일명: Mars_Base_Inventory_danger.csv
    파일 저장에 실패하면 오류 메시지를 로그에 기록한다.
    """
    if not dangerous:
        logging.warning('저장할 위험 물질 데이터가 없습니다.')
        return
    try:
        with open(DANGER_CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=dangerous[0].keys())
            writer.writeheader()
            writer.writerows(dangerous)
        logging.info('위험 물질 CSV 저장 완료: %s', DANGER_CSV_FILE)
    except IOError as e:
        logging.error('CSV 저장 오류: %s', e)
    except PermissionError as e:
        logging.error('파일 쓰기 권한 없음: %s', e)


def save_binary(sorted_inventory):
    """STEP 6: 인화성 순으로 정렬된 리스트를 이진 파일로 저장한다.

    저장 파일명: Mars_Base_Inventory_List.bin
    pickle 모듈을 사용해 리스트 전체를 바이너리 형태로 저장한다.
    """
    try:
        with open(BIN_FILE, 'wb') as f:
            pickle.dump(sorted_inventory, f)
        logging.info('이진 파일 저장 완료: %s', BIN_FILE)
    except IOError as e:
        logging.error('이진 파일 저장 오류: %s', e)


def load_binary():
    """STEP 7: 이진 파일을 읽어서 내용을 화면에 출력한다.

    Mars_Base_Inventory_List.bin 파일을 열어 저장된 리스트를 복원하고 출력한다.
    파일이 없거나 손상된 경우 오류 메시지를 로그에 기록한다.
    """
    try:
        with open(BIN_FILE, 'rb') as f:
            data = pickle.load(f)
        for item in data:
            print(item)
        logging.info('이진 파일 읽기 완료: %d개 항목', len(data))
    except FileNotFoundError:
        logging.error('이진 파일을 찾을 수 없습니다: %s', BIN_FILE)
    except pickle.UnpicklingError as e:
        logging.error('이진 파일 읽기 오류 (파일 손상): %s', e)


def main():
    """전체 STEP 1~7을 순서대로 실행한다."""
    read_csv()

    inventory = load_csv_as_list()
    print(inventory)

    sorted_inventory = sort_by_flammability(inventory)

    dangerous = filter_dangerous(sorted_inventory)

    save_dangerous_csv(dangerous)

    save_binary(sorted_inventory)

    load_binary()


if __name__ == '__main__':
    main()
