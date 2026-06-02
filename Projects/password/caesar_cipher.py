"""
caesar_cipher.py
================
카이사르 암호 해독기
- password.txt를 읽어 26가지 자리수(shift)로 해독 결과를 출력한다.
- 사전 단어가 발견되면 자동으로 반복을 멈춘다.
- 눈으로 확인 후 자리수를 입력하면 result.txt에 저장한다.
"""

# 텍스트 사전 - 이 단어 중 하나가 해독 결과에 포함되면 반복 중단
DICTIONARY = [
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "her",
    "was", "one", "our", "out", "day", "get", "has", "him", "his", "how",
    "man", "new", "now", "old", "see", "two", "way", "who", "boy", "did",
    "its", "let", "put", "say", "she", "too", "use", "open", "door", "key",
    "password", "access", "code", "mars", "base", "storage", "emergency"
]


def caesar_cipher_decode(target_text):
    """
    카이사르 암호를 해독한다.

    파라메터:
        target_text (str): 해독할 암호 문자열

    반환값:
        tuple: (자동 감지된 자리수 또는 None, 해독된 텍스트 또는 None)
    """
    print("=" * 60)
    print("카이사르 암호 해독 시작")
    print(f"원본 암호문: {target_text}")
    print("=" * 60)

    auto_detected_shift = None
    auto_detected_text = None

    # 알파벳 수(26)만큼 자리수를 반복
    for shift in range(1, 27):
        decoded_chars = []

        for char in target_text:
            if char.isalpha():
                # 대소문자 구분하여 기준 아스키 설정
                base = ord('A') if char.isupper() else ord('a')
                # 카이사르 복호화: (문자 - 기준 - shift) mod 26 + 기준
                decoded_char = chr((ord(char) - base - shift) % 26 + base)
                decoded_chars.append(decoded_char)
            else:
                # 알파벳이 아닌 문자(숫자, 공백, 특수문자)는 그대로 유지
                decoded_chars.append(char)

        decoded_text = ''.join(decoded_chars)
        print(f"[자리수 {shift:2d}] {decoded_text}")

        # 사전 단어 검사 - 소문자로 변환 후 단어 단위로 비교
        decoded_lower = decoded_text.lower()
        for word in DICTIONARY:
            if word in decoded_lower:
                print(f"\n>>> 사전 단어 '{word}' 발견! (자리수: {shift})")
                auto_detected_shift = shift
                auto_detected_text = decoded_text
                break

        # 사전 단어가 발견되면 반복 중단
        if auto_detected_shift is not None:
            break

    print("=" * 60)
    return auto_detected_shift, auto_detected_text


def save_result(text, shift):
    """
    해독 결과를 result.txt에 저장한다.

    파라메터:
        text  (str): 저장할 해독 텍스트
        shift (int): 사용된 자리수
    """
    try:
        with open("result.txt", "w", encoding="utf-8") as f:
            f.write(f"자리수(shift): {shift}\n")
            f.write(f"해독 결과: {text}\n")
        print(f"[저장 완료] result.txt에 결과가 저장되었습니다.")
    except FileNotFoundError:
        print("[오류] 저장 경로를 찾을 수 없습니다.")
    except PermissionError:
        print("[오류] 파일 쓰기 권한이 없습니다.")
    except OSError as e:
        print(f"[오류] 파일 저장 실패: {e}")


def main():
    # password.txt 읽기
    try:
        with open("password.txt", "r", encoding="utf-8") as f:
            password_text = f.read().strip()
    except FileNotFoundError:
        print("[오류] password.txt 파일을 찾을 수 없습니다.")
        return
    except PermissionError:
        print("[오류] password.txt 파일에 접근 권한이 없습니다.")
        return
    except OSError as e:
        print(f"[오류] 파일 읽기 실패: {e}")
        return

    if not password_text:
        print("[오류] password.txt 파일이 비어 있습니다.")
        return

    # 카이사르 암호 해독 실행
    auto_shift, auto_text = caesar_cipher_decode(password_text)

    # 자동 감지된 경우 먼저 안내
    if auto_shift is not None:
        print(f"\n자동 감지된 자리수: {auto_shift}")
        print(f"해독 결과: {auto_text}")
        print("\n이 결과를 저장하려면 Enter, 다른 자리수를 입력하려면 숫자를 입력하세요.")

    # 사용자 입력으로 저장할 자리수 결정
    while True:
        try:
            if auto_shift is not None:
                user_input = input(f"자리수 입력 (기본값 {auto_shift}, 종료: q): ").strip()
            else:
                user_input = input("저장할 자리수 입력 (1~26, 종료: q): ").strip()

            if user_input.lower() == 'q':
                print("종료합니다.")
                break

            # Enter만 누르면 자동 감지 값 사용
            if user_input == "" and auto_shift is not None:
                save_result(auto_text, auto_shift)
                break

            shift_input = int(user_input)
            if not (1 <= shift_input <= 26):
                print("1~26 사이의 숫자를 입력하세요.")
                continue

            # 입력한 자리수로 다시 해독하여 저장
            decoded_chars = []
            for char in password_text:
                if char.isalpha():
                    base = ord('A') if char.isupper() else ord('a')
                    decoded_chars.append(chr((ord(char) - base - shift_input) % 26 + base))
                else:
                    decoded_chars.append(char)

            final_text = ''.join(decoded_chars)
            save_result(final_text, shift_input)
            break

        except ValueError:
            print("올바른 숫자를 입력하세요.")


if __name__ == "__main__":
    main()
