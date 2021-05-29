from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta
import calendar
import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


base = datetime.today()
current_month = datetime.today().strftime("%m")
current_year = datetime.today().strftime("%Y")
current_date = datetime.today().strftime("%d")
last_day = calendar.monthrange(int(current_year), int(current_month))[1]
num_days = 3#int(last_day) - int(current_date) + 1
dist_cd_list = ['603', '581', '595', '596', '605']

url = 'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByDistrict'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
}

input_list = [item for sublist in [
    [(url, headers, (('district_id', dist_cd), ('date', (base + timedelta(days=x)).strftime("%d-%m-%Y"))
                     )) for x in range(num_days)] for dist_cd in dist_cd_list] for item in sublist]

# print(input_list)

all_result = []


def get_resp(url, headers, params):

    s = requests.Session()
    retries = Retry(total=5, backoff_factor=0.5)
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))
    response = s.get(url, headers=headers, params=params)
    if response.status_code == 200:
        if response.json()['sessions']:
            return response.json()['sessions']


def send_email(message):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Vaccine Slots Found"
    email_list = ['put_your_email1@gmail.com', 'put_your_email2@gmail.com']
    sender = "put_sender_email@gmail.com"
    msg['To'] = ', '.join(email_list)
    msg['From'] = sender
    msg.attach(MIMEText(message, 'html'))

    s = smtplib.SMTP_SSL('smtp.gmail.com:465')
    s.login('put_sender_email@gmail.com', "PutSenderPassword")
    s.sendmail(msg['From'], email_list, msg.as_string())
    s.quit()
    print("Email Sent")

if __name__ == '__main__':
    with ProcessPoolExecutor(max_workers=None) as executor:
        for result in executor.map(get_resp, *zip(*input_list)):
            if result:
                all_result.append(result)

    all_result = [item for sublist in all_result for item in sublist]
    df = pd.DataFrame(all_result)

    if not df.empty:
        df = df[["center_id", "name", "address", "state_name", "district_name", "pincode", "fee_type", "date",
                 "available_capacity_dose1", "available_capacity_dose2", "fee", "min_age_limit", "vaccine", "slots"]]
        slot_df = df[(df['available_capacity_dose1'] > 0) & (df['min_age_limit'] == 18)]
        # slot_df = df[(df['available_capacity_dose1'] > 0) | (df['available_capacity_dose2'] > 0)]
        if not slot_df.empty:
            print("Slots Found")
            # slot_df.to_csv('slot_df.csv', header=1, index=False)
            send_email(slot_df.to_html())
        else:
            print("Slot nahin mila")
    else:
        print("Data Nahin aaya")
