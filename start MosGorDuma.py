import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials
from s1 import AppealMosGorDuma as Agency, Person

CREDENTIALS_FILE = 'creds.json'  # TODO: вставить свой файл
spreadsheet_id = "" # TODO: заполнить своим ключем
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets',
                                                                                  'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth)

text = service.spreadsheets().values().get(
    spreadsheetId = spreadsheet_id,
    range = "M1:M1",
    majorDimension = "ROWS"
).execute()['values'][0][0][25:]

value = service.spreadsheets().values().get(
    spreadsheetId = spreadsheet_id,
    range = "B2:M1000",
    majorDimension = "ROWS"
).execute()

find = input("Введите фамилию человека: ")
dep = input("Введите фамилию депутата: ")

for line in value['values']:
    person = Person(*line)
    if find.lower() in person.surname.lower():
        if person.text == '':
            person.text = text
        Agency(person, dep).send()