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
import xml.etree.ElementTree as ElementTree

ATOM_TEMPLATE = """
POST /atom/post

<entry xmlns="http://purl.org/atom/ns#">
  <title>uploaded by fotolife-client.py</title>
  <content mode="base64" type="{}">{}</content>
  <generator>fotolife-client.py</generator>
</entry>
"""

def wsse(username, api_key):
    nonce = sha1(secrets.token_bytes(16)).digest()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    digest = sha1(nonce + now.encode() + api_key.encode()).digest()
    return 'UsernameToken Username="{}", PasswordDigest="{}", Nonce="{}", Created="{}"'.format(
        username,
        b64encode(digest).decode(),
        b64encode(nonce).decode(),
        now,
    )

def upload_to_fotolife(match):
    alt, path, _, _ = match.groups()

    # pathがローカルのファイルを指していなければ何もしない
    path = os.path.join(base_dir, path)
    if not os.path.exists(path):
        return match[0]

    mime = mimetypes.guess_type(path)[0]
    with open(path, "rb") as f:
        imgbuf = f.read()

    body = ATOM_TEMPLATE.format(mime, b64encode(imgbuf).decode())
    req = Request("https://f.hatena.ne.jp/atom/post", method="POST", headers={
        "X-WSSE": wsseValue,
    }, data=body.encode())
    try:
        with urlopen(req) as res:
            if not 200 <= res.status < 300:
                print("[-] failed to request: {}, reason: {}".format(res.url, res.reason))
                return match[0]

            resbuf = res.read()
            tree = ElementTree.fromstring(resbuf)
            ns = {
                "hatena": "http://www.hatena.ne.jp/info/xmlns#"
            }
            urls = tree.findall("hatena:syntax", ns)
            url = urls[0].text
            print("[+] uploaded {}".format(path))
    except HTTPError as e:
        print(e)
        return match[0]


    if not alt:
        return "[{}]".format(url)
    else:
        return "[{}:title={}]".format(url, alt)

if len(sys.argv) == 1:
    print("Usage: {} <file>".format(sys.argv[0]))
    exit(1)

wsseValue = wsse(os.getenv("HATENA_ID"), os.getenv("OWNER_API_KEY"))

target = sys.argv[1]
buf = open(target, "r").read()
base_dir = os.path.dirname(target)
pattern = re.compile(r"""!\[([^\]]*)\]\(([^\)]*)\s*(?:"([^"]*)"\s*)?(?:"([^"]*)"\s*)?\)""")

res = pattern.sub(upload_to_fotolife, buf)
with open(target, "w") as f:
    f.write(res)
