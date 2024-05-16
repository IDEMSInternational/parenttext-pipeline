from argparse import ArgumentParser
from pprint import pprint
from re import sub

from bs4 import BeautifulSoup
from requests import Session


class ImporterError(Exception):
    pass


def import_definition(host, username, password, definitions):
    with Session() as session:
        try:
            login(session, host, username, password)
            for fp in definitions:
                upload(session, host, fp)
            logout(session, host)
        except ImporterError as e:
            print_error(e)


def login(session, host, username, password):
    url = f"{host}/users/login/"
    r = session.post(
        url,
        headers={
            "Referer": url,
        },
        data={
            "username": username,
            "password": password,
            "csrfmiddlewaretoken": extract_csrf_token(session, url),
        },
    )

    if r.status_code == 200 and r.url == f"{host}/msg/inbox/":
        print(f"Login completed, url={url}, username={username}")
    else:
        raise ImporterError("Login failed", r)


def upload(session, host, definition_fp):
    url = f"{host}/org/import/"

    with open(definition_fp, "rb") as definition_file:
        r = session.post(
            url,
            headers={
                "Referer": url,
            },
            data={
                "csrfmiddlewaretoken": extract_csrf_token(session, url),
            },
            files={
                "import_file": definition_file,
            },
        )

    if r.status_code == 200 and "Import successful" in r.text:
        print(f"Import completed, url={url}, file={definition_fp}")
    else:
        raise ImporterError("Import failed", r)


def logout(session, host):
    url = f"{host}/users/logout/"
    r = session.get(url)

    if r.status_code == 200:
        print(f"Logout completed, url={url}")
    else:
        raise ImporterError("Logout failed", r)


def extract_csrf_token(session, url):
    return BeautifulSoup(session.get(url).text, features="html.parser",).select_one(
        "input[name=csrfmiddlewaretoken]"
    )["value"]


def print_error(e: ImporterError):
    msg, r = e.args
    print("# ERROR")
    print(msg)
    print("## REQUEST ")
    pprint(
        {
            "url": r.request.url,
            "method": r.request.method,
            "headers": dict(r.request.headers),
            "body": sub(r"password=.*&", "password=(hidden)&", r.request.body or ""),
        }
    )
    print("## RESPONSE")
    pprint(
        {
            "url": r.url,
            "status": r.status_code,
            "headers": dict(r.headers),
        }
    )
    print("### BODY")
    print(r.text)


def cli():
    parser = ArgumentParser(description="Import a flow definition into RapidPro")
    parser.add_argument(
        "-H",
        "--host",
        required=True,
        help="URL of the RapidPro server to upload to e.g. https://rp.example.com",
    )
    parser.add_argument(
        "-u",
        "--username",
        required=True,
    )
    parser.add_argument(
        "-p",
        "--password",
        required=True,
    )
    parser.add_argument(
        "definition_file",
        nargs="+",
        help="File containing flow definition to upload",
    )
    args = parser.parse_args()
    import_definition(
        args.host,
        args.username,
        args.password,
        args.definition_file,
    )


if __name__ == "__main__":
    cli()
