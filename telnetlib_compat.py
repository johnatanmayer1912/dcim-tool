"""
telnetlib_compat.py
-------------------
Compatibility shim for telnetlib which was removed in Python 3.13+.
Netmiko and other network libraries depend on this module.

This provides a minimal stub that satisfies imports without full telnet functionality
(since we only use SSH in this application).
"""

import sys

# Telnet protocol constants - defined at module level for direct import
IAC = bytes([255])  # Interpret As Command
DONT = bytes([254])
DO = bytes([253])
WONT = bytes([252])
WILL = bytes([251])
SB = bytes([250])  # Subnegotiation Begin
GA = bytes([249])  # Go Ahead
EL = bytes([248])  # Erase Line
EC = bytes([247])  # Erase Character
AYT = bytes([246])  # Are You There
AO = bytes([245])  # Abort Output
IP = bytes([244])  # Interrupt Process
BREAK = bytes([243])
DM = bytes([242])  # Data Mark
NOP = bytes([241])  # No Operation
SE = bytes([240])  # Subnegotiation End
EOR = bytes([239])  # End of Record
ABORT = bytes([238])
SUSP = bytes([237])
EOF = bytes([236])

SYNCH = bytes([242])

# Telnet options
BINARY = bytes([0])
ECHO = bytes([1])
RCP = bytes([2])
SGA = bytes([3])  # Suppress Go Ahead
NAMS = bytes([4])
STATUS = bytes([5])
TM = bytes([6])
RCTE = bytes([7])
NAOL = bytes([8])
NAOP = bytes([9])
NAOCRD = bytes([10])
NAOHTS = bytes([11])
NAOHTD = bytes([12])
NAOFFD = bytes([13])
NAOVTS = bytes([14])
NAOVTD = bytes([15])
NAOLFD = bytes([16])
XASCII = bytes([17])
LOGOUT = bytes([18])
BM = bytes([19])
DET = bytes([20])
SUPDUP = bytes([21])
SUPDUPOUTPUT = bytes([22])
SNDLOC = bytes([23])
TTYPE = bytes([24])
EOR_OPT = bytes([25])
TUID = bytes([26])
OUTMRK = bytes([27])
TTYLOC = bytes([28])
VT3270REGIME = bytes([29])
X3PAD = bytes([30])
NAWS = bytes([31])
TSPEED = bytes([32])
LFLOW = bytes([33])
LINEMODE = bytes([34])
XDISPLOC = bytes([35])
OLD_ENVIRON = bytes([36])
AUTHENTICATION = bytes([37])
ENCRYPT = bytes([38])
NEW_ENVIRON = bytes([39])
TN3270E = bytes([40])
XAUTH = bytes([41])
CHARSET = bytes([42])
RSP = bytes([43])
COM_PORT_OPTION = bytes([44])
SUPPRESS_LOCAL_ECHO = bytes([45])
TLS = bytes([46])
KERMIT = bytes([47])
SEND_URL = bytes([48])
FORWARD_X = bytes([49])

# Authentication types
AUTHENTICATION_NULL = bytes([0])
AUTHENTICATION_KERBEROS_V4 = bytes([1])
AUTHENTICATION_KERBEROS_V5 = bytes([2])
AUTHENTICATION_SPX = bytes([3])
AUTHENTICATION_MINK = bytes([4])
AUTHENTICATION_SRP = bytes([5])
AUTHENTICATION_RSA = bytes([6])
AUTHENTICATION_SSL = bytes([7])

# Encryption types
ENCRYPT_NULL = bytes([0])
ENCRYPT_DES = bytes([1])
ENCRYPT_3DES = bytes([2])
ENCRYPT_RC4_40 = bytes([3])
ENCRYPT_RC4_56 = bytes([4])
ENCRYPT_RC4_128 = bytes([5])
ENCRYPT_RC2_40 = bytes([6])
ENCRYPT_RC2_56 = bytes([7])
ENCRYPT_RC2_128 = bytes([8])


class Telnet:
    """Stub Telnet class for compatibility."""
    
    def __init__(self, host=None, port=23, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        raise NotImplementedError(
            "Telnet is not supported in this application. "
            "Please use SSH connections only."
        )
    
    def open(self, host, port=23, timeout=None):
        pass
    
    def close(self):
        pass
    
    def read_until(self, match, timeout=None):
        return b""
    
    def read_all(self):
        return b""
    
    def write(self, buffer):
        pass
    
    def read_very_lazy(self):
        return b""
    
    def set_debuglevel(self, debuglevel):
        pass
    
    def set_option_negotiation_callback(self, callback):
        pass


# Only install fake telnetlib if it's missing
try:
    import telnetlib
except ImportError:
    # Create fake module with all constants
    class FakeTelnetlib:
        Telnet = Telnet
        
        # Copy all module-level constants
        IAC = IAC
        DONT = DONT
        DO = DO
        WONT = WONT
        WILL = WILL
        SB = SB
        GA = GA
        EL = EL
        EC = EC
        AYT = AYT
        AO = AO
        IP = IP
        BREAK = BREAK
        DM = DM
        NOP = NOP
        SE = SE
        EOR = EOR
        ABORT = ABORT
        SUSP = SUSP
        EOF = EOF
        SYNCH = SYNCH
        BINARY = BINARY
        ECHO = ECHO
        RCP = RCP
        SGA = SGA
        NAMS = NAMS
        STATUS = STATUS
        TM = TM
        RCTE = RCTE
        NAOL = NAOL
        NAOP = NAOP
        NAOCRD = NAOCRD
        NAOHTS = NAOHTS
        NAOHTD = NAOHTD
        NAOFFD = NAOFFD
        NAOVTS = NAOVTS
        NAOVTD = NAOVTD
        NAOLFD = NAOLFD
        XASCII = XASCII
        LOGOUT = LOGOUT
        BM = BM
        DET = DET
        SUPDUP = SUPDUP
        SUPDUPOUTPUT = SUPDUPOUTPUT
        SNDLOC = SNDLOC
        TTYPE = TTYPE
        EOR_OPT = EOR_OPT
        TUID = TUID
        OUTMRK = OUTMRK
        TTYLOC = TTYLOC
        VT3270REGIME = VT3270REGIME
        X3PAD = X3PAD
        NAWS = NAWS
        TSPEED = TSPEED
        LFLOW = LFLOW
        LINEMODE = LINEMODE
        XDISPLOC = XDISPLOC
        OLD_ENVIRON = OLD_ENVIRON
        AUTHENTICATION = AUTHENTICATION
        ENCRYPT = ENCRYPT
        NEW_ENVIRON = NEW_ENVIRON
        TN3270E = TN3270E
        XAUTH = XAUTH
        CHARSET = CHARSET
        RSP = RSP
        COM_PORT_OPTION = COM_PORT_OPTION
        SUPPRESS_LOCAL_ECHO = SUPPRESS_LOCAL_ECHO
        TLS = TLS
        KERMIT = KERMIT
        SEND_URL = SEND_URL
        FORWARD_X = FORWARD_X
        AUTHENTICATION_NULL = AUTHENTICATION_NULL
        AUTHENTICATION_KERBEROS_V4 = AUTHENTICATION_KERBEROS_V4
        AUTHENTICATION_KERBEROS_V5 = AUTHENTICATION_KERBEROS_V5
        AUTHENTICATION_SPX = AUTHENTICATION_SPX
        AUTHENTICATION_MINK = AUTHENTICATION_MINK
        AUTHENTICATION_SRP = AUTHENTICATION_SRP
        AUTHENTICATION_RSA = AUTHENTICATION_RSA
        AUTHENTICATION_SSL = AUTHENTICATION_SSL
        ENCRYPT_NULL = ENCRYPT_NULL
        ENCRYPT_DES = ENCRYPT_DES
        ENCRYPT_3DES = ENCRYPT_3DES
        ENCRYPT_RC4_40 = ENCRYPT_RC4_40
        ENCRYPT_RC4_56 = ENCRYPT_RC4_56
        ENCRYPT_RC4_128 = ENCRYPT_RC4_128
        ENCRYPT_RC2_40 = ENCRYPT_RC2_40
        ENCRYPT_RC2_56 = ENCRYPT_RC2_56
        ENCRYPT_RC2_128 = ENCRYPT_RC2_128
    
    # Install fake module
    sys.modules['telnetlib'] = FakeTelnetlib()
    
    print("[INFO] telnetlib compatibility shim installed (Python 3.13+ support)")
