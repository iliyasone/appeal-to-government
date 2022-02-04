# %%
import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials
from pyasn1_modules.rfc2459 import DirectoryString
from s1 import AppealRosPotrebNadzor as Agency, Person
from time import time, sleep
from random import randint

# %%
TIME_UPDATE = 3 # как часто обновлять данные из таблицы (если нет других дел)

# %%
CREDENTIALS_FILE = 'creds.json'  # TODO: вставить свой файл
spreadsheet_id = "" # TODO: заполнить своим ключем
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets',
                                                                                  'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth)

# %%
def get(range, majorDimensionColumns: bool = False, table: str = None) -> list:
    if table != None:
        range = table + '!' + range
       

    return service.spreadsheets().values().get(
        spreadsheetId = spreadsheet_id,
        range = range,
        majorDimension = "COLUMNS" if majorDimensionColumns else "ROWS"
    ).execute()['values']

# %%
def update(range: str, data: list, majorDimensionColumns: bool = False, table: str = None):
    if table != None:
        range = table + '!' + range
    return service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, 
        range=range, 
        valueInputOption='USER_ENTERED', 
        body= {
            "range" :range,
            "majorDimension": "COLUMNS" if majorDimensionColumns else "ROWS",
            "values": data
            }
        ).execute()

# %%
text = get(range = 'B2:B100', majorDimensionColumns=True, table="'Текст обращений'")[0]

# %%
values = get(range = "B2:T1000")
n = len(values)
i = -1

last_time = time()

# %%
while i < n - 1:
    i += 1

    line = values[i]
    person: Person = Person(*line[:12])
    
    if person.text == '':
        person.text = text[i%len(text)]
    
    person.text = Agency.clear_name(person.text)

    if Agency.name_gov in person.recipients or Agency.all_gov in person.recipients:
        
        if (len(line) < 17 or line[17] == ''):
            print(person.name, person.surname, end=' ')
            person.text = Agency.randomize_text(person.text)
            request = Agency(person).send()

            if request == Agency.RequestCode.OK:

                update(
                    range = f"S{i+2}:S{i+2}",
                    data = [[Agency.ReturnSheetsValue.CHANGED]]
                )

                if time() - last_time > TIME_UPDATE:  # обновить value (вдруг в таблице какие-то изменения от других участников, новые заявки)
                    values = get(range = "B2:T1000")
                    n = len(values)
                    last_time = time()

            elif request == Agency.RequestCode.AGAIN_HIT:
                update(
                    range = f"S{i+2}:S{i+2}",
                    data = [[Agency.ReturnSheetsValue.NOT_CHANGED]]
                )
            elif request == Agency.RequestCode.ERROR_TO_MANY_HITS:
                update(
                    range = f"S{i+2}:S{i+2}",
                    data = [[Agency.ReturnSheetsValue.TRYING_CHANGE]]
                )
                i -= 1
                sleep(Agency.TIME_DELAY)
                
                continue
            else:
                print(request)


