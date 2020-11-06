# CF Merger
This tool is just another 'toy' console app that I made to make life easier. If you have two or more accounts on Codeforces and want to merge all aced problem from those account to your main account or :whatever: then you are at the right place. It will help you to do the job.

## Good to know
- It will push aced problems from one account to another codeforces account
- Only "contest" submission will work. If you want to implement other features like gym, acmguru, welcome send pull request
- To avoid throttling, the script will idle for 4 minutes after submitting hundred problems each
- Password is not visible in the console and not stored anywhere in the world

## Dependencies
- aiohttp, robobrowser, prettytable, tqdm

## Installation
Just like other python installation.
```bash

$ git clone https://github.com/joynahid/cfmerger.git
$ pip3 install pipenv
$ cd cfmerger
$ pipenv shell
$ pipenv sync

```