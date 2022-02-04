# %%
import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials
from s1 import AppealMosGov as Agency, Person
from time import time, sleep
import traceback
# %%
TIME_UPDATE = 3  # как часто обновлять данные из таблицы (если нет других дел)

# %%
CREDENTIALS_FILE = 'creds.json'  # TODO: вставить свой файл
spreadsheet_id = "" # TODO: заполнить своим ключем
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE,
                                                               ['https://www.googleapis.com/auth/spreadsheets',
                                                                'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)

print('Приостанавливать выполнение если анкета не отправилась из-за непредвиденной ошибки?')
print('напишите ДА или НЕТ: ',end='')
inp = input()
if inp.upper() == 'ДА':
    SHOULD_STOP = True
    print('Принято ДА')
else:
    SHOULD_STOP = False
    print('Принято НЕТ')

# %%
def get(range, majorDimensionColumns: bool = False, table: str = None) -> list:
    if table is not None:
        range = table + '!' + range

    return service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range,
        majorDimension="COLUMNS" if majorDimensionColumns else "ROWS"
    ).execute()['values']


# %%
def update(range: str, data: list, majorDimensionColumns: bool = False, table: str = None):
    if table is not None:
        range = table + '!' + range
    return service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range,
        valueInputOption='USER_ENTERED',
        body={
            "range": range,
            "majorDimension": "COLUMNS" if majorDimensionColumns else "ROWS",
            "values": data
        }
    ).execute()


# %%
texts, heads = get(range='C2:D100', majorDimensionColumns=True, table="'Текст обращений'")

# %%
values = get(range="B2:T1000")
n = len(values)
i = -1

last_time = time()

# %%
while i < n - 1:
    i += 1

    line = values[i]
    person: Person = Person(*line[:12])

    if person.text == '':
        person.text = texts[i % len(texts)]

    person.text = Agency.clear_name(person.text)
    L = Agency.LETTER
    if Agency.name_gov in person.recipients or Agency.all_gov in person.recipients:

        if len(line) < Agency.INDEX or line[Agency.INDEX] == '':
            print(person.name, person.surname, end=' ')
            person.text = Agency.randomize_text(person.text)

            update(
                range=f"{L}{i + 2}:{L}{i + 2}",

                data=[[f"Sending now..."]]
            )
            try:
                request: Agency.Request.RequestCode = Agency(person).send(head=heads[i % len(heads)])
            except Exception as e:
                traceback.print_tb()

                print(e)


                update(
                    range=f"{L}{i + 2}:{L}{i + 2}",

                    data=[[str(e)]]
                )
                if SHOULD_STOP:
                    input('Случилось что-то плохое с этим обращением. Продолжить? ')
                continue

            if isinstance(request, Agency.Request.OK):

                update(
                    range=f"{L}{i + 2}:{L}{i + 2}",

                    data=[[f"Собянина, номер обращения {request.ID}"]]
                )

                if time() - last_time > TIME_UPDATE:  # обновить value (вдруг в таблице какие-то изменения от других участников, новые заявки)
                    values = get(range="B2:T1000")
                    n = len(values)
                    last_time = time()
            #input('print ENTER for next')
"""
            elif False and request == RequestCode.AGAIN_HIT:
                update(
                    range=f"{L}{i + 2}:{L}{i + 2}",
                    data=[[Agency.ReturnSheetsValue.NOT_CHANGED]]
                )
            elif False and  request == RequestCode.ERROR_TO_MANY_HITS:
                update(
                    range=f"{L}{i + 2}:{L}{i + 2}",
                    data=[[Agency.ReturnSheetsValue.TRYING_CHANGE]]
                )
                i -= 1
                sleep(Agency.TIME_DELAY)

                continue
            else:
                print(request)
            """