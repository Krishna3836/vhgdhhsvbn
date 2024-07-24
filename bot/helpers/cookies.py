from http.cookiejar import MozillaCookieJar
from requests import utils

def get_cookies(path):
    cookies = MozillaCookieJar(path)
    cookies.load()
    dict_cookies = utils.dict_from_cookiejar(cookies)
    return cookies, dict_cookies