#!/usr/bin/env python3
"""Download and verify the original Martini 3 parameter bundle."""
import hashlib
from pathlib import Path
import sys
import urllib.request

URL = ('https://cgmartini-library.s3.ca-central-1.amazonaws.com/'
       '1_Downloads/ff_parameters/martini3/martini_v300.zip')
SHA256 = '204d83592ab46f0fd98358d98fc47dfabf3a0cc031bc422dcfe2929a56d1ccf2'


def main(destination):
    with urllib.request.urlopen(URL, timeout=120) as response:
        payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != SHA256:
        raise ValueError(f'Martini archive checksum mismatch: {digest}')
    Path(destination).write_bytes(payload)


if __name__ == '__main__':
    main(sys.argv[1])
