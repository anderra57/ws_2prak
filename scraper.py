import getpass
import signal
import sys
import urllib
import re
from bs4 import BeautifulSoup
import requests

# ALDAGAIAK

user = ''
passw = ''
cookie = ''
goiburuak = {'Host': 'egela.ehu.eus'}
metodoa = 'GET'
eskaera_kop = 1


# 1. ZEREGINA

def request_get(uq, gq, ct):
    print_request('GET', uq, None)
    erantzuna = requests.request('GET', uq, headers=gq, allow_redirects=False)
    print_response(erantzuna, 'GET', ct)
    return erantzuna


def cnt_censor():
    cen_pass = ''
    for i in range(0, len(passw)):
        if i == 0 or i == (len(passw) - 1):
            cen_pass += passw[i]
        else:
            cen_pass += 'x'

    edukia = {'username': user, 'password': cen_pass}
    return urllib.parse.urlencode(edukia)


def request_post(uq, gq, ct):
    gq['Content-Type'] = 'application/x-www-form-urlencoded'
    edukia = {'username': user, 'password': passw}
    edukia_encoded = urllib.parse.urlencode(edukia)
    gq['Content-Length'] = str(len(edukia_encoded))

    print_request('POST', uq, cnt_censor())

    erantzuna = requests.request('POST', uq, data=edukia_encoded, headers=gq, allow_redirects=False)

    print_response(erantzuna, 'POST', ct)
    return erantzuna


def print_request(mt, ut, ct):
    global eskaera_kop
    print("\n\n--------", end=" ")
    print(str(eskaera_kop) + '. ESKAERA', end=" ")
    print("--------")
    eskaera_kop += 1
    print('\n\nMetodoa: ' + mt)
    print('URIa: ' + ut)
    if ct is not None:
        print("Edukia (pasahitza babestuta): " + ct)
    return


def print_response(erantzuna, mt, ct):
    print("\n" + str(erantzuna.status_code) + " " + erantzuna.reason)
    print(erantzuna.headers, )
    if ct is True:
        # print(erantzuna.content)
        print('\n\nAktibatzen denean, hemen edukia agertuko da.')
    return


def lortu_saioa():  # !!!!!!!!!!!!!!
    global cookie
    uria = 'https://egela.ehu.eus/login/index.php'

    # # # # # # # #
    # # Azalpena:
    # # 1) Login orrialdean sartu (GET, 200)
    # # 2) Erabiltzailea eta pasahitza sartu (POST, 303)
    # # 3) Aurreko erantzunetik cookiea lortu eta test orrialdean sartu (GET, 303)
    # # 4) Dena ondo badabil, https://egela.ehu.eus/ orrialdera berbidaliko digu (GET, 200)
    # # # # # # # #

    # 1. eskaera: GET, /login/index.php, 200 OK
    erantzuna = request_get(uria, goiburuak, False)
    try:
        cookie = erantzuna.headers["Set-Cookie"].split(';')[0]
    except KeyError:
        berrizlortu()
    goiburuak["Cookie"] = cookie

    # 2. eskaera: POST, /login/index.php, 303 See other

    erantzuna = request_post(uria, dict(goiburuak), False)

    # 3. eskaera: GET, /login/index.php, 303 See other

    uria = erantzuna.headers['Location']
    try:
        cookie = erantzuna.headers["Set-Cookie"].split(';')[0]
    except KeyError:
        berrizlortu()
    goiburuak["Cookie"] = cookie
    erantzuna = request_get(uria, goiburuak, False)

    # 4. eskaera: GET, /, 200 OK
    print(erantzuna.headers)
    request_get(erantzuna.headers['Location'], goiburuak, True)

    print("\nZuzen kautotu zara. Enter sakatu Web Sistemak ikastaroko fitxategiak jeisteko.")
    input()
    return


# 2. ZEREGINA

def format_bytes(size):
    # 2**10 = 1024
    power = 2 ** 10
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    size_ret = str("{:.2f}".format(size)) + ' ' + power_labels[n] + 'B'
    return size_ret


def get_valid_filename(s):
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def down_pdf(uri, filename):
    goiburuak["Cookie"] = cookie
    erantzuna = requests.request(metodoa, uri, headers=goiburuak, allow_redirects=False)

    erantzuna = requests.request(metodoa, erantzuna.headers['Location'], headers=goiburuak, allow_redirects=False)
    print("Jeitsita!", end='')
    size = format_bytes(int(erantzuna.headers["content-length"]))
    print(' (' + size + ')', end='\n\n')
    with open('./pdfs/' + filename, 'wb') as f:
        f.write(erantzuna.content)
    return


def kurtsoko_pdfak_jeitsi():  # !!!!!!!!!!!!!!
    erantzuna = request_get("https://egela.ehu.eus/course/view.php?id=42336", goiburuak, False)
    soup = BeautifulSoup(erantzuna.content, 'html.parser')
    ain = soup.find_all("div", {"class": "activityinstance"})
    print("\n")
    for elem in ain:
        if elem.find("img", {"src": "https://egela.ehu.eus/theme/image.php/fordson/core/1611567512/f/pdf"}):
            download = elem.find('a', href=True)['href'] + '&redirect=1'
            filename = get_valid_filename(elem.find("span", {"class": "instancename"}).text) + '.pdf'
            print(filename + ' jeisten...')
            down_pdf(download, filename)
    return


# ZEREGIN NAGUSIA

def berrizlortu():
    global goiburuak
    goiburuak = {'Host': 'egela.ehu.eus'}
    global eskaera_kop
    eskaera_kop = 1
    print("\n⚠ KONTUZ ⚠")
    print("Gaizki sartu dituzu kredentzialak. Saiatu berriro.")
    login()
    lortu_saioa()
    kurtsoko_pdfak_jeitsi()


def handler(sig_num, frame):
    print('\nBezerotik ateratzen...')
    sys.exit(0)


def login():
    print("Sartu erabiltzailea:")
    global user
    user = input()
    print("Sartu pasahitza:")
    global passw
    passw = getpass.getpass('')


def intro():
    print("")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handler)
    intro()
    login()
    lortu_saioa()
    kurtsoko_pdfak_jeitsi()
