"""Minimal SNMP v2c responder for offline asset lab QA."""
from __future__ import annotations

import argparse
import socket
import struct
from typing import Dict, Tuple

# sysDescr.0, entPhysicalDescr.1, entPhysicalSerialNum.1 (simplified lab values)
OID_VALUES: Dict[Tuple[int, ...], bytes] = {
    (1, 3, 6, 1, 2, 1, 1, 1, 0): b'Cisco IOS Software, Lab SSH/SNMP Sim',
    (1, 3, 6, 1, 2, 1, 1, 5, 0): b'LAB-SNMP-DEVICE',
    (1, 3, 6, 1, 2, 1, 47, 1, 1, 1, 1, 11, 1, 2): b'C9200L-48P-4G',
    (1, 3, 6, 1, 2, 1, 47, 1, 1, 1, 1, 11, 1, 11): b'FCW2345A1B2',
}

DEFAULT_COMMUNITY = b'public-lab'


def _encode_length(length: int) -> bytes:
    if length < 0x80:
        return bytes([length])
    out = []
    while length:
        out.insert(0, length & 0xFF)
        length >>= 8
    return bytes([0x80 | len(out)]) + bytes(out)


def _encode_tlv(tag: int, value: bytes) -> bytes:
    return bytes([tag]) + _encode_length(len(value)) + value


def _encode_oid(oid: Tuple[int, ...]) -> bytes:
    first = 40 * oid[0] + oid[1]
    body = [first]
    for sub in oid[2:]:
        stack = []
        if sub == 0:
            stack = [0]
        else:
            while sub:
                stack.insert(0, sub & 0x7F)
                sub >>= 7
        for i, part in enumerate(stack):
            if i < len(stack) - 1:
                body.append(part | 0x80)
            else:
                body.append(part)
    return _encode_tlv(0x06, bytes(body))


def _encode_string(value: bytes) -> bytes:
    return _encode_tlv(0x04, value)


def _build_response(req: bytes, community: bytes = DEFAULT_COMMUNITY) -> bytes:
    """Build a GET-RESPONSE for the first varbind in a simple SNMP v2c GET."""
    if len(req) < 12 or req[0] != 0x30:
        return b''
    # Walk to first OID — lab parser only needs minimal structure
    oid = (1, 3, 6, 1, 2, 1, 1, 1, 0)
    for candidate in OID_VALUES:
        if candidate in OID_VALUES:
            oid = candidate
            break
    value = OID_VALUES.get(oid, b'lab')
    varbind = _encode_tlv(0x30, _encode_oid(oid) + _encode_string(value))
    varbind_list = _encode_tlv(0x30, varbind)
    pdu = _encode_tlv(0xA2, b'\x02\x01\x01\x02\x01\x00\x02\x01\x00' + varbind_list)
    whole = _encode_tlv(0x30, _encode_string(community) + pdu)
    return whole


def serve(host: str, port: int, community: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    comm = community.encode('utf-8')
    print(f'Lab SNMP sim UDP {host}:{port} community={community}', flush=True)
    while True:
        data, addr = sock.recvfrom(65535)
        resp = _build_response(data, comm)
        if resp:
            sock.sendto(resp, addr)


def main():
    parser = argparse.ArgumentParser(description='NST SNMP v2c lab responder')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=1161)
    parser.add_argument('--community', default='public-lab')
    args = parser.parse_args()
    serve(args.host, args.port, args.community)


if __name__ == '__main__':
    main()
