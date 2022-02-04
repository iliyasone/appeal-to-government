from python_rucaptcha import ImageCaptcha
import base64


def solve_image_captcha(file: str = "screen.png") -> str:
    with open(file, "rb") as img_file:
        my_string = base64.b64encode(img_file.read())

    # TODO: Введите ключ от сервиса RuCaptcha, из своего аккаунта
    RUCAPTCHA_KEY = ""

    # Возвращается JSON содержащий информацию для решения капчи
    user_answer = ImageCaptcha.ImageCaptcha(rucaptcha_key=RUCAPTCHA_KEY).captcha_handler(captcha_base64=my_string)

    if not user_answer['error']:
        # решение капчи
        print(user_answer['taskId'])
        return user_answer['captchaSolve']

    elif user_answer['error']:
        # Тело ошибки, если есть
        print(user_answer['errorBody'])
        print(user_answer['errorBody'])


if __name__ == "__main__":
    print(solve_image_captcha())