"""
Script to download hourly power usage for the previous day from BCHydro website
"""


from datetime import (
    datetime,
    timedelta
)
import os
import re
import requests


# Email/password used to login to BCHydro
EMAIL = ''
PASSWORD = ''

# Account ID can be found by logging in, going to the export data section
# and inspecing the accounts HTML under "Choose Accounts"
#
# E.g.,
#<tr data-accounttype="ST" data-accountid="YOUR_ACCOUNT_ID" ...>
ACCOUNTID = ''

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
LOGFILE = os.path.join(BASE_DIR, 'bchydro.log')


def log(msg):
    with open(LOGFILE, 'a') as _file:
        _file.write('[%s] %s\n' % (datetime.now(), msg))


def downloadHourlyDataAndWriteToFile(startDate, endDate):
    assert EMAIL, 'fill in EMAIL variable'
    assert PASSWORD, 'fill in PASSWORD variable'
    assert ACCOUNTID, 'fill in ACCOUNTID variable'

    session = requests.Session()

    # This can be anything for the login request
    bchydroparam = 'b4d390ef-c148-4127-95e4-756b0ed88dd7'

    data = {
        'realm': 'bch-ps',
        'gotoUrl': 'https://app.bchydro.com/datadownload/web/download-centre.html',
        'tpsLogin': 'false',
        'email': EMAIL,
        'password': PASSWORD,
        'submit': 'Log in',
        'bchydroparam': bchydroparam,
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'keep-alive'
    }


    log('logging in')
    addr = 'https://app.bchydro.com/sso/UI/Login'
    resp = session.post(addr, data=data, headers=headers)
    if resp.status_code == 200:
        log('Successfully logged in')
    else:
        log('Error logging in: %s: %s' % (resp.status_code, resp.content))
        return None

    # Have to download the download-centre webpage in order to get the 'datadownload' cookie
    log('Downloading session cookies')
    addr = 'https://app.bchydro.com/datadownload/web/download-centre.html'
    resp = session.get(addr)
    if resp.status_code != 200:
        log('Error downloading session cookie: %s %s' % (resp.status_code, resp.content))
        return None

    # The webpage has an HTML span tag designating the bchydroparam value. This value must be present
    # in the POST headers to download the data, as well as in the corresponding cookie
    webpageContent = resp.content.decode()
    if 'bchydroparam' in webpageContent:
        regex = re.compile(r'.*bchydroparam.*')
        m = regex.search(webpageContent)
        if m:
            val = m.group(0)
            bchydroparam = val.split('>', 1)[1].replace('</span>\r', '')
            log('bchydroparam: %s' % bchydroparam)
        else:
            log('Unable to find \'bchydroparam\' value in download webpage content: {}'.format(webpageContent))
            return None

    headers = {
        'bchydroparam': bchydroparam,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'keep-alive',
        'X-CSRF-Token': bchydroparam,
        'Referrer': 'https://app.bchydro.com/datadownload/web/download-centre.html',
        'Host': 'app.bchydro.com',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
        'Origin': 'https://app.bchydro.com'
    }

    data = {
        'accountId': ACCOUNTID,
        'fromDate': startDate,
        'toDate': endDate,
        'downloadInterval': 'HOURLY',
        'downloadType': 'CNSMPHSTRY',
        'downloadFormat': 'CSVFILE',
    }

    log('Creating download request')
    addr = 'https://app.bchydro.com/datadownload/web/create-download-request.html'
    resp = session.post(addr, data=data, headers=headers, cookies={'bchydroparam': bchydroparam})
    if resp.status_code != 200:
        log('Error creating download request: %s %s' % (resp.status_code, resp.content))
        return None

    log('Downloading data')
    addr = 'https://app.bchydro.com/datadownload/web/download-file.html?requestId=recent'
    resp = session.get(addr, cookies={'bchydroparam': bchydroparam})
    if resp.status_code != 200:
        log('Error downloading data: %s %s' % (resp.status_code, resp.content))
        return None

    def _getFilename(disposition):
        values = disposition.split('; ')
        for entry in values:
            if 'filename' in entry:
                key, value = entry.split('=', 1)
                if key == 'filename':
                    return value.replace('"', '')

        filename = '{}_{}'.format(bchydroparam, datetime.today())
        return filename

    filename = _getFilename(resp.headers['Content-Disposition'])
    filepath = os.path.join(BASE_DIR, filename)
    with open(filepath, 'wb') as _file:
        _file.write(resp.content)

    log('Successfully downloaded data for {} to "{}"'.format(startDate, filename))

    return filepath


def main():
    endDate = datetime.today()
    startDate = endDate.date() - timedelta(days=1)
    endDateStr = endDate.strftime('%b %d, %Y')
    startDateStr = startDate.strftime('%b %d, %Y')

    downloadHourlyDataAndWriteToFile(startDateStr, endDateStr)


if __name__ == '__main__':
    main()
