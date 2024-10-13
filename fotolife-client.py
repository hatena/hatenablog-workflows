import sys
import re
import os
from hashlib import sha1
from base64 import b64encode
from datetime import datetime
import secrets
import mimetypes
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from xml.etree import ElementTree

ATOM_TEMPLATE = """
POST /atom/post

<entry xmlns="http://purl.org/atom/ns#">
  <title>uploaded by fotolife-client.py</title>
  <content mode="base64" type="{}">{}</content>
  <generator>hatena/hatenablog-workflows</generator>
</entry>
"""

wsse_value = ""
base_dir = ""

def wsse(username, api_key):
    """
    ユーザのIDとAPIキーからX-WSSEヘッダの値を生成する
    """
    nonce = sha1(secrets.token_bytes(16)).digest()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    digest = sha1(nonce + now.encode() + api_key.encode()).digest()
    return 'UsernameToken Username="{}", PasswordDigest="{}", Nonce="{}", Created="{}"'.format(
        username,
        b64encode(digest).decode(),
        b64encode(nonce).decode(),
        now,
    )

def upload_to_fotolife(path: str) -> str|None:
    """
    画像のパスを受け取って、その画像ファイルをFotolifeにアップロードする
    その画像をFotolife記法として埋め込むための文字列を返す。
    """
    mime = mimetypes.guess_type(path)[0]
    with open(path, "rb") as f:
        imgbuf = f.read()

    body = ATOM_TEMPLATE.format(mime, b64encode(imgbuf).decode())
    req = Request("https://f.hatena.ne.jp/atom/post", method="POST", headers={
        "X-WSSE": wsse_value,
    }, data=body.encode())
    try:
        with urlopen(req) as res:
            if not 200 <= res.status < 300:
                print(f"[-] failed to request: {res.url}, reason: {res.reason}")
                return None

            resbuf = res.read()
            tree = ElementTree.fromstring(resbuf)
            ns = {
                "hatena": "http://www.hatena.ne.jp/info/xmlns#"
            }
            syntaxes = tree.findall("hatena:syntax", ns)
            syntax = re.sub(r':image$', ':plain', syntaxes[0].text)
            print(f"[+] uploaded {path}")
            return syntax
    except HTTPError as e:
        print(f"[-] failed to request: {e.url}, reason: {e.reason}")
        return None


def replace_to_fotolife_syntax(match: re.Match) -> str:
    """
    Markdownの画像記法で参照されている画像をFotolifeにアップロードしつつ、Fotolife記法に置き換える
    """
    alt = match.group("alt")
    path = match.group("path")
    title = match.group("quot") or match.group("squot")

    # pathがローカルのファイルを指していなければ何もしない
    path = os.path.join(base_dir, path)
    if not os.path.exists(path):
        print(f"[-] Skipped: file not found: {path}")
        return match[0]

    syntax = upload_to_fotolife(path)
    if syntax is None:
        return match[0]

    if alt and title:
        return f"[{syntax}:title={title}:alt={alt}]"
    elif (not alt) and title:
        return f"[{syntax}:title={title}]"
    elif alt and (not title):
        return f"[{syntax}:alt={alt}]"
    elif (not alt) and (not title):
        return f"[{syntax}]"

def main():
    """
    usage: python3 fotolife-client.py <file>
    """
    global wsse_value
    global base_dir


    hatena_id = os.getenv("HATENA_ID")
    owner_api_key = os.getenv("OWNER_API_KEY")
    if not hatena_id or not owner_api_key:
        print("please set environment variables: HATENA_ID, OWNER_API_KEY")
        sys.exit(1)
    wsse_value = wsse(hatena_id, owner_api_key)

    if len(sys.argv) == 1:
        print(f"usage: python3 {sys.argv[0]} <file>")
        sys.exit(1)
    target = sys.argv[1]
    with open(target, "r", encoding="utf-8") as f:
        buf = f.read()
    base_dir = os.path.dirname(target)

    pattern = re.compile(r"""!\[(?P<alt>[^\]]*)\]\((?P<path>[^\)]*?)\s*("(?P<quot>[^"]*)"\s*)?('(?P<squot>[^']*)'\s*)?\)""")
    res = pattern.sub(replace_to_fotolife_syntax, buf)
    with open(target, "w", encoding="utf-8") as f:
        f.write(res)

if __name__ == "__main__":
    main()
