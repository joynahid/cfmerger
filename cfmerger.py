import time
import sys
import os
import io
import asyncio
import json
from aiohttp import ClientSession
from robobrowser import RoboBrowser
from prettytable import PrettyTable
import tqdm, bs4
from getpass import getpass

LANG_CODE = {
    'gnu': ('54', '.cpp'),
    'python': ('31', '.py'),
    'pypy': ('41', '.py'),
    'java': ('36', '.java'),
    'kotlin': ('48', '.kt')
}

DOWNLOAD_LIMIT = 25
WAIT_PER_HUNDRED = 4*60  # seconds

table = PrettyTable()

cnt = 0
total_prob = 0


def login(handle):
    password = getpass('[Secured] Password of {}: '.format(handle))

    print('> Signing in...')

    try:
        browser = RoboBrowser(parser='lxml')
        browser.open('http://codeforces.com/enter')
        enter_form = browser.get_form('enterForm')
        enter_form['handleOrEmail'] = handle
        enter_form['password'] = password
        browser.submit_form(enter_form)

        checks = list(map(lambda x: x.getText()[
                      1:].strip(), browser.select('div.caption.titled')))

        if handle.lower() not in str(checks).lower():
            print('> !!! Login Failed. Please enter valid credentials')
            return None
        else:
            print('> Success!')
            return browser
    except Exception as e:
        print('>', e)
        return None


def getSubmissions(browser, handle):
    print('> Fetching submissions of', handle)

    browser.open(
        'https://codeforces.com/api/user.status?handle={}'.format(handle))

    res = json.load(io.BytesIO(browser.response.content))

    print('>', res['status'], '\n')

    return res


def uniqueAcSubmissions(handleA, handleB, browserA, browserB):
    resA = getSubmissions(browserA, handleA)['result']
    resB = getSubmissions(browserB, handleB)['result']

    is_solved = {}

    ac_problems = []

    for each in resB:
        if each['verdict'] == 'OK':
            key = json.dumps(each['problem'])
            is_solved[key] = True

    for each in resA:
        each['problem'] = json.dumps(each['problem'])

        if 'contestId' in each and each['problem'] not in is_solved and each['verdict'] == 'OK':
            each['problem'] = json.loads(each['problem'])
            ac_problems.append({
                'id': str(each['id']),
                'contestId': str(each['contestId']),
                'lang': each['programmingLanguage'],
                'code': str(each['problem']['index']),
                'name': each['problem']['name']
            })

    if not os.system('clear'):
        pass
    elif not os.system('cls'):
        pass

    global total_prob

    total_prob = len(ac_problems)
    return ac_problems


async def fetch(each, ctyp, session):
    try:
        submission_url = 'https://codeforces.com/{}/{}/submission/{}'.format(
            ctyp, each['contestId'], each['id'])

        async with session.get(submission_url) as response:
            html = await response.read()
            sp = bs4.BeautifulSoup(html, 'html.parser')

            code = sp.find('pre')

            if code:
                res = {
                    'code': code.get_text(),
                    'type': 'contest',
                    'contest': each['contestId'],
                    'problemCode': each['code'],
                    'language': each['lang'],
                    'name': each['name']
                }

                return res

        # print(submission_url)

    except Exception as e:
        print(e)
        return None


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def getCodesOfA(ac_data, hA, hB, browser):
    tot = len(ac_data)
    ac_data_chunked = list(chunks(ac_data, DOWNLOAD_LIMIT))
    print('\n> Number of Phases', len(ac_data_chunked))
    print('----------------------')

    sofar = 0
    async with ClientSession() as session:
        with tqdm.tqdm(total=tot) as pbar:
            for ac_data in ac_data_chunked:
                sofar += 25
                tasks = []
                data = []
                for each in ac_data:
                    task = asyncio.create_task(fetch(each, 'contest', session))
                    tasks.append(task)

                for f in asyncio.as_completed(tasks):
                    dd = await f
                    if dd:
                        data.append(dd)
                    time.sleep(0.1)
                    pbar.update(1)

                submitCodes(data, browser)

                # Avoid Throttling

                if sofar % 100 == 0:
                    for remaining in range(WAIT_PER_HUNDRED, 0, -1):
                        sys.stdout.write("\r")
                        sys.stdout.write(
                            "> Idle. Waking up again after {} seconds to avoid Throttling".format(remaining))
                        sys.stdout.write("\r")
                        sys.stdout.flush()
                        time.sleep(1)

                time.sleep(5)

    return data


def submitCodes(codes, browser):
    lang_code = ('54', '.cpp')

    global table
    global cnt

    table.field_names = ["Problem", "Title", "Language", "Status", "Time (s)"]

    sys.stdout.write("\r")
    sys.stdout.write("> Starting submission...")
    sys.stdout.write("\r")
    sys.stdout.flush()
    time.sleep(1)

    for each in codes:
        cnt += 1
        for key in LANG_CODE:
            if key in each['language'].lower():
                lang_code = LANG_CODE[key]
                break

        url = 'http://codeforces.com/{}/{}/submit/{}'.format(
            each['type'], each['contest'], each['problemCode'].upper())

        yo_time = time.time()

        browser.open(url)

        submission = browser.get_form(class_='submit-form')
        if submission is None:
            print('Cannot find problem')
            return False

        submission['programTypeId'] = lang_code[0]

        file_name = 'file'+lang_code[1]

        file = open(file_name, "w", encoding="utf-8")
        file.write(each['code'])
        file.close()

        submission['sourceFile'] = os.getcwd() + "/" + file_name

        browser.submit_form(submission)

        if 'my' in str(browser.url[-3:]):
            sys.stdout.write("\r")
            sys.stdout.write(
                "> {}/{} {} submitted successfully  ".format(cnt, total_prob, each['name']))
            sys.stdout.flush()
            time.sleep(0.1)
            table.add_row([each['contest']+each['problemCode'], each['name'],
                           each['language'], 'OK', round(time.time()-yo_time)])
        else:
            table.add_row([each['contest']+each['problemCode'], each['name'],
                           each['language'], 'FAILED', round(time.time()-yo_time)])

    sys.stdout.write("\r")


async def main():
    global table
    global cnt
    global total_prob

    st_time = time.time()
    bighr = '\n\n'
    hr = '---------------------------------------'

    print("""


        +------+
        |      |
    +   |      |
    |   |      |
    |   |      |   CF Marger
    +----------------------+
        |      |   https://github.com/joynahid/cfmarger
        +------+

    Welcome to CF Merger!

    It will help to submit already ACed problems
    of an account to other account of yours.

    Press anykey to continue...
""")
    sys.stdin.read(1)
    os.system('clear')
    print(
        'Login to the account [A]:\nAll the codes from this account will be copied to Account [A].')
    print(hr)
    print()

    handleA = input('Account [A] CF Handle: ')
    browserA = login(handleA)

    print(bighr)
    if not browserA:
        return None
    print(
        'Login to the account [B]:\nAll the AC codes of account [A] will be submitted here.')
    print(hr)

    handleB = input('Account [B] CF Handle: ')
    browserB = login(handleB)
    print(bighr)
    if not browserB:
        return None

    os.system('clear')

    ac = uniqueAcSubmissions(handleA, handleB, browserA, browserB)
    print()
    print(f'Pushing {handleA} -> {handleB}, {total_prob} problems')
    await asyncio.create_task(getCodesOfA(ac, handleA, handleB, browserB))
    print()

    print(table)
    print()

    print(f'Submitted {cnt} problems out of {total_prob} successfully')
    print()
    print('----Execution time', round(time.time() - st_time), 'seconds----\n\n\n')

asyncio.run(main())
