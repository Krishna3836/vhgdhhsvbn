from os import path as ospath, environ, remove
from logging import FileHandler, StreamHandler, INFO, basicConfig, error as log_error, info as log_info
#from logging import FileHandler, StreamHandler, INFO, basicConfig, error as log_error, info as log_info
from subprocess import run as srun, call as scall
from config.py import TG_CONFIG
if ospath.exists('log.txt'):
    with open('log.txt', 'r+') as f:
        f.truncate(0)

if ospath.exists('rlog.txt'):
    remove('rlog.txt')
UPSTREAM_REPO=TG_CONFIG.UPSTREAM_REPO
UPSTREAM_BRANCH=TG_CONFIG.UPSTREAM_BRANCH
if UPSTREAM_REPO is not None:
    if ospath.exists('.git'):
        srun(["rm", "-rf", ".git"])

    update = srun([f"git init -q \
                     && git config --global user.email pogodrawings@gmail.com \
                     && git config --global user.name Mahesh \
                     && git add . \
                     && git commit -sm update -q \
                     && git remote add origin {UPSTREAM_REPO} \
                     && git fetch origin -q \
                     && git reset --hard origin/{UPSTREAM_BRANCH} -q"], shell=True)

    repo = UPSTREAM_REPO.split('/')
    UPSTREAM_REPO = f"https://github.com/{repo[-2]}/{repo[-1]}"
    if update.returncode == 0:
        log_info('Successfully updated with latest commits !!')
    else:
        log_error('Something went Wrong ! Retry or Ask Support !')
    log_info(f'UPSTREAM_REPO: {UPSTREAM_REPO} | UPSTREAM_BRANCH: {UPSTREAM_BRANCH}')
