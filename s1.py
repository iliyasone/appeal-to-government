# %%
from logging import PercentStyle
from os import device_encoding, waitpid
import re
from pyasn1_modules.rfc2459 import DistributionPoint, PresentationAddress
from selenium import webdriver
import selenium
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from deps import MosGorDuma
from time import sleep
from random import randint
from captcha import solve_image_captcha

class Person:
    def __init__(self, name, surname, father_name, email, phone_number, city, address, index, telegram, recipients,
                 stuff, text=''):
        self.name: str = str.strip(name)
        self.surname: str = str.strip(surname)
        self.father_name: str = str.strip(father_name)
        self.email: str = str.strip(email)
        self.phone_number: str = phone_number
        self.index: str = index
        self.city: str = str.strip(city)
        self.address: str = Person.clear_adress(city, address)
        self.text: str = text
        self.telegram: str = telegram
        self.recipients: str = recipients

    def clear_number(number: str) -> str:
        for stuff in ('+7', '8'):
            if stuff in number[:2]:
                number = number.replace(stuff, '', 1)

        result = ''

        for i in number:
            if i.isdigit():
                result += i
        return result

    def clear_adress(city: str, adress: str):
        for some_staff in (
                f'Г. {city}, ',
                f'Г. {city},',
                f'Город {city}, ',
                f'Город {city},',
                f'г. {city}, ',
                f'г. {city},',
                f'город {city}, ',
                f'город {city},',
                f'Г. {city} ',
                f'Г. {city}',
                f'Город {city} ',
                f'Город {city}',
                f'г. {city} ',
                f'г. {city}',
                f'город {city} ',
                f'город {city}',
                f'{city}, ',
                f'{city},',
                f'{city} ',
                f'{city}'):
            if some_staff in adress:
                adress = adress.replace(some_staff, '')
                break

        return adress


class Appeal(object):
    def __init__(self, person: Person):
        self.person = person

    all_gov = 'Во все органы РФ'
    name_gov = 'Во все органы РФ'

    def send(self) -> str:
        pass

    @staticmethod
    def wait():
        print("Нажмите ENTER для продолжения")
        input()

    @classmethod
    def clear_name(cls, text: str):
        for some_staff in (
                'представитель власти',
                'адресат'
        ):
            if some_staff in text.lower():
                start = text.lower().find(some_staff)
                text = text[:start] + cls.name_gov + text[start + len(some_staff):]
                break

        return text

    @staticmethod
    def randomize_text(text: str) -> str:
        stuff = ('а', 'a'), ('о', 'o'), ('с', 'c'), ('е', 'e'), ('р', 'p'), ('у', 'y'), ('к', 'k')
        n = randint(1, 2 ** (len(stuff) - 1))
        for i in range(len(stuff)):
            if (n % 2 ** (i + 1)) // (2 ** i) == 1:
                k = text.count(stuff[i][0])
                if k > 1:
                    r = randint(0, k - 1)
                    text = text.replace(stuff[i][0], stuff[i][1], r)
        return text


class TooManyHits(Exception):
    """
    Слишком много обращений подано за последнее время.

    """


class AppealMosGorDuma(Appeal):
    name_gov = "Московская городская дума"

    def __init__(self, person: Person, recipient: str):
        self.person = person
        self.recipient = recipient

    def send(self):
        driver = webdriver.Chrome()
        driver.get("https://duma.mos.ru/ru/feedback/form")
        driver.find_element(By.XPATH, '/html/body/main/div[3]/div/div[2]/div[2]/form/button')
        el = driver.find_element("xpath", "/html/body/main/div[3]/div/div[2]/div[2]/form/button")
        el.click()

        # print(f"//*[@id=\"internet_person_to\"]/optgroup[1]/option[{MosGorDuma.find(self.recipient)+1}]")
        driver.find_element("xpath",
                            f"//*[@id=\"internet_person_to\"]/optgroup[1]/option[{MosGorDuma.find(self.recipient) + 1}]").click()

        driver.find_element("xpath", "//*[@id=\"internet_person_first_name\"]").send_keys(self.person.name)
        driver.find_element("xpath", "//*[@id=\"internet_person_surname\"]").send_keys(self.person.surname)
        driver.find_element("xpath", "//*[@id=\"internet_person_second_name\"]").send_keys(self.person.father_name)
        driver.find_element("xpath", "//*[@id=\"internet_person_mail\"]").send_keys(self.person.email)
        driver.find_element("xpath", "//*[@id=\"internet_person_email_repeat\"]").send_keys(self.person.email)
        driver.find_element("xpath", "//*[@id=\"internet_person_phone\"]").send_keys(self.person.phone_number)

        driver.find_element("xpath", "//*[@id=\"internet_person_city\"]").send_keys(self.person.city)
        driver.find_element("xpath", "//*[@id=\"internet_person_address\"]").send_keys(self.person.address)
        driver.find_element("xpath", "//*[@id=\"internet_person_content\"]").send_keys(self.person.text)

        driver.find_element("xpath", "//*[@id=\"for-natural\"]/form/div[4]/div/div[3]/div").click()

        self.wait()


class AppealRosPotrebNadzor(Appeal):
    class RequestCode:
        OK = 'OK'
        """
        Обнаружена фраза "Принято к рассмотрению"
        """

        AGAIN_HIT = 'AGAIN_HIT'
        """
        Данное обращение уже было отправлено
        """

        ERROR_TO_MANY_HITS = 'ERROR_TO_MANY_HITS'

    TIME_DELAY = 5
    name_gov = 'Роспотребнадзор'

    def send(self) -> str:
        global driver
        driver = webdriver.Chrome()
        driver.get("https://petition.rospotrebnadzor.ru/petition/oper_msg_create/")

        driver.find_element(By.XPATH, '/html/body/div[2]/div/div/form/table/tbody/tr[2]/td[2]/span/input').send_keys(
            self.person.surname)
        driver.find_element(By.XPATH, '/html/body/div[2]/div/div/form/table/tbody/tr[3]/td[2]/span/input').send_keys(
            self.person.name)
        driver.find_element(By.XPATH, '/html/body/div[2]/div/div/form/table/tbody/tr[4]/td[2]/span/input').send_keys(
            self.person.father_name)

        driver.find_element(By.XPATH, '/html/body/div[2]/div/div/form/table/tbody/tr[7]/td[2]/span/input').send_keys(
            self.person.phone_number)
        driver.find_element(By.XPATH, '/html/body/div[2]/div/div/form/table/tbody/tr[9]/td[2]/span/input').send_keys(
            self.person.email)

        driver.find_element(By.XPATH,
                            '/html/body/div[2]/div/div/form/table/tbody/tr[13]/td[2]/select/option[87]').click()

        driver.find_element(By.XPATH, '/html/body/div[2]/div/div/form/table/tbody/tr[14]/td[2]/textarea').send_keys(
            self.person.text)
        driver.find_element(By.XPATH, '/html/body/div[2]/div/div/form/table/tbody/tr[10]/td[2]/span/input').send_keys(
            self.person.city + ', ' + self.person.address
        )
        input()
        driver.find_element(By.XPATH, '/html/body/div[2]/div/div/form/table/tbody/tr[19]/td[2]/input').click()
        
        try:
            driver.find_element(By.XPATH, '/html/body/div[2]/div/p[2]/a')
            print(driver.find_element(By.XPATH, '/html/body/div[2]/div/p[1]').text)
            print('Продолжение через час! (5 минут)')
            sleep(5)
            return self.RequestCode.ERROR_TO_MANY_HITS
            # raise TooManyHits
        except NoSuchElementException:
            if 'Ваше обращение принято' in driver.find_element(By.XPATH, '/html/body/div[2]/div/p').text:
                print(driver.find_element(By.XPATH, '/html/body/div[2]/div/p').text)
                sleep(5)
                return self.RequestCode.OK
            else:
                print(driver.find_element(By.XPATH, '/html/body/div[2]/div/p').text)
                sleep(5)
                return self.RequestCode.AGAIN_HIT

    class ReturnSheetsValue:
        CHANGED = '2'
        """
        Успешно изменено значение
        """

        NOT_CHANGED = '3'
        """
        Значение не изменилось. Вероятно из-за текстового ограничения
        """
        TRYING_CHANGE = '4'
        """
        Не удалось изменить значение, однако прямо сейчас выполняется часовой цикл, после которого попытка повториться
        """




class AppealMosGov(Appeal):
    class Request:
        class RequestCode:
            pass

        class OK(RequestCode):
            def __init__(self, ID):
                self.ID = ID

    LETTER: str = 'Q'
    INDEX: int = 15
    name_gov = 'Мэрия Москвы'
    name_SSS = 'Сергей Семёнович Собянин'

    def send(self, head: str = None) -> Request.RequestCode:
        driver = webdriver.Chrome()
        driver.get('https://www.mos.ru/feedback/reception/')

        driver.find_element(By.XPATH,
                            '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[1]/div[2]/div/div/div[1]/div/label/input').click()
        driver.find_element(By.XPATH,
                            '/html/body/div[7]/div/div[2]/div[2]/div/div/div[1]/div/div[1]/button/div').click()

        driver.find_element(By.XPATH,
                            '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[1]/div[2]/div/div/div[3]/label/span[1]/span').click()

        driver.find_element(By.XPATH,
                            '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[1]/div[2]/div/div/div[4]/div/div/label/input').click()
        driver.find_element(By.XPATH,
                            '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[1]/div[2]/div/div/div[4]/div/div/div/div[2]/div[1]/ul/li[1]').click()

        driver.find_element(By.XPATH,
                            '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div[2]/div[2]/div/div/div[1]/div[1]/div/label').send_keys(
            self.person.surname)
        driver.find_element(By.XPATH,
                            '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div[2]/div[2]/div/div/div[1]/div[2]/div/label').send_keys(
            self.person.name)
        driver.find_element(By.XPATH,
                            '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div[2]/div[2]/div/div/div[1]/div[3]/div/div/label/div[1]/input').send_keys(
            self.person.father_name)
        driver.find_element(By.XPATH,
                            '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div[2]/div[2]/div/div/div[2]/div[1]/div/label/input').send_keys(
            Person.clear_number(self.person.phone_number))
        driver.find_element(By.XPATH,
                            '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div[2]/div[2]/div/div/div[2]/div[2]/div/label/input').send_keys(
            self.person.email)
        driver.find_element(By.XPATH,
                            '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div[3]/div/div/div/div[1]/div/div/label/input').send_keys(
            self.person.city)
        # driver.find_element(By.XPATH, '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div[3]/div/div/div/div[3]/div[1]/div/label/input').send_keys(person.adress)
        driver.find_element(By.XPATH,
                            '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[3]/div[2]/div/div/div[2]/div/div/label/textarea').send_keys(
            head)
        driver.find_element(By.XPATH,
                            '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[3]/div[2]/div/div/div[3]/div/div/label/textarea').send_keys(
            self.person.text)
        driver.find_element(By.XPATH,
                            '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[4]/div[2]/div/div/div[1]/label/span[1]').click()
        driver.find_element(By.XPATH,
                            '/html/body/div[3]/div/div[1]/div/div/div/div[2]/div[4]/div[2]/div/div/div[2]/button').click()

        sleep(1)
        url = driver.find_element(By.XPATH,
                                  '/html/body/div[3]/div/div[1]/div/div/div/div/div/div[4]/div/div[2]/div/img'
                                  )

        url.screenshot('screen.png')

        sleep(1)

        # проходим капчу
        driver.find_element(By.XPATH, '/html/body/div[3]/div/div[1]/div/div/div/div/div/div[4]/div/div[1]/label/input').send_keys(
            solve_image_captcha()
        )
        driver.find_element(By.XPATH,'/html/body/div[3]/div/div[1]/div/div/div/div/div/div[5]/div/button[1]').click()

        # для успокоения ждём 1 секунду, чтобы успела прогрузиться страница
        sleep(1)
        times = 0
        i = 0
        while True:
            # начинаем попытки поиска ID
            sleep(1)
            print('.',end='')
            try:
                text = driver.find_element(By.XPATH, '/html/body/div[3]/div/div[1]/div/div/div/div/div/div').text
                if 'ID' in text:
                    print('Ee')
                    i = text.find('ID')
                    
                    sleep(1)
                    return self.Request.OK(ID=text[i:i+11])
                else:
                    raise NoSuchElementException
            except NoSuchElementException:
                times += 1

                # В случае если в течение 3 секунд не находится ID, попытка ещё раз ввести капчу и нажать на кнопку
                if times > 3:
                    times = 0
                    print('another cheak captha')
                    if self.get_safe_captcha_input(driver) == '':
                        url = driver.find_element(By.XPATH,'/html/body/div[3]/div/div[1]/div/div/div/div/div/div[4]/div/div[2]/div/img')
                        url.screenshot('screen.png')
                        driver.find_element(By.XPATH,'/html/body/div[3]/div/div[1]/div/div/div/div/div/div[4]/div/div[1]/label/input').\
                            send_keys(solve_image_captcha())
                        driver.find_element(By.XPATH,'/html/body/div[3]/div/div[1]/div/div/div/div/div/div[5]/div/button[1]'
                            ).click()
            except StaleElementReferenceException:
                times += 1

        # Элемент с текстом:
        # /html/body/div[3]/div/div[1]/div/div/div/div/div/div
        # Пример обращения:
        #
        # Ваше обращение отправлено 10.11.2021 через электронную
        # приёмную на официальном портале Мэра и Правительства Москвы за номером ID=2897742 и подлежит обязательной
        # регистрации в течение трёх дней с момента поступления в Правительство Москвы.

    def get_safe_captcha_input(self, driver: selenium.webdriver.Chrome) -> str:
        try:
            return driver.find_element(By.XPATH,
                                       '/html/body/div[3]/div/div[1]/div/div/div/div/div/div[4]/div/div[1]/label/input').text
        except NoSuchElementException:
            return "Can't get it"
        except StaleElementReferenceException:
            return "Can't get it"


def main():
    person = Person(
        "Иван", "Иванов", "Иванович", "testemail@test.com", "+79296917999", "Москва", "ул Бочкова, д 11, кв 5",
        "", "", "", "", "Прошу ускорить процесс одобрения иностранный вакцины Pfizer для вакцинирования несовершеннолетних!")
    AppealMosGorDuma(person, recipient="Беседина").send()


if __name__ == "__main__":
    main()
    pass


# %%
# Person.clear_number('+7(929)-671-(75)-93')

# %%
