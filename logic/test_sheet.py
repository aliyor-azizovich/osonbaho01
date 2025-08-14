import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("osonbaholicensing-b9bf7d3e1b19.json", scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1BkfdRE2ZIVXRmigefS4J0K5IsmZyBqjpDuCjU-qHZTA").sheet1
print(sheet.get_all_records())
