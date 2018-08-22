'''
    Protocollo di comunicazione della
    scheda SC635

    Il protocollo e' cosi' composto:
        0x8D    Inizio trama
        ...     Pacchetto (almeno 2 byte del comando)
        0xXXYY  crc
        0x8E    Fine trama
'''

import struct
import serial
import crcmod
import socket

class _SOCK(object):

    def __init__(self, ip, porta, timeout=1.0):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((ip, porta))
            self.s.settimeout(timeout)
        except:
            self.s = None

    def __del__(self):
        self.close()

    def a_posto(self):
        return self.s is not None

    def close(self):
        if self.s is not None:
            self.s.close()
            self.s = None

    def getSettingsDict(self):
        return {}

    def applySettingsDict(self, _):
        pass

    def flushInput(self):
        pass

    def write(self, dati):
        self.s.sendall(dati)

    def read(self, quanti):
        try:
            return self.s.recv(quanti)
        except socket.timeout:
            return None

    def inWaiting(self):
        return 0


class PROT(object):
    _INIZIO_TRAMA = 0x8D
    _FINE_TRAMA = 0x8E
    _CARATTERE_DI_FUGA = 0x8F

    _RSP_VALIDA = 0xC0

    def __init__(self, **cosa):
        crci = 22069
        self.crc = crcmod.Crc(0x11021, crci, False, 0)

        timeout = 1.0
        if 'timeout' in cosa:
            timeout = cosa['timeout']

        if 'indip' in cosa:
            # socket tcp
            self.mdp = 1400

            self.uart = _SOCK(cosa['indip'], 50741, timeout)
            if not self.uart.a_posto():
                self.uart.close()
                self.uart = None
        else:
            self.mdp = 1024

            # porta seriale
            brate = 115200
            if 'brate' in cosa:
                brate = cosa['brate']
            cfh = False
            if 'cfh' in cosa:
                cfh = cosa['cfh']

            if 'porta' in cosa:
                # classica
                try:
                    self.uart = serial.Serial(cosa['porta'],
                                              brate,
                                              serial.EIGHTBITS,
                                              serial.PARITY_NONE,
                                              serial.STOPBITS_ONE,
                                              timeout,
                                              rtscts=cfh)
                    self.prm = self.uart.getSettingsDict()
                except serial.SerialException as err:
                    print(err)
                    self.uart = None
                except ValueError as err:
                    print(err)
                    self.uart = None
            else:
                # usb
                try:
                    self.uart = serial.serial_for_url(
                        'hwgrep://%s:%s' %
                        (cosa['vid'], cosa['pid']),
                        baudrate=brate,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=timeout,
                        rtscts=cfh)
                    self.prm = self.uart.getSettingsDict()
                except serial.SerialException as err:
                    print(err)
                    self.uart = None

    def __del__(self):
        self.chiudi()

    def a_posto(self):
        return self.uart is not None

    def chiudi(self):
        if self.uart is not None:
            self.uart.close()
            self.uart = None

    def cambia(self, baud=None, tempo=None):
        imp = self.uart.getSettingsDict()
        if baud is not None:
            imp['baudrate'] = baud
        if tempo is not None:
            imp['timeout'] = tempo
        self.uart.applySettingsDict(imp)

    def ripristina(self):
        self.uart.applySettingsDict(self.prm)

    @staticmethod
    def _aggiungi(dove, cosa):
        if (cosa == PROT._INIZIO_TRAMA or
                cosa == PROT._FINE_TRAMA or
                cosa == PROT._CARATTERE_DI_FUGA):
            dove.append(PROT._CARATTERE_DI_FUGA)
            dove.append((~cosa) & 0xFF)
        else:
            dove.append(cosa)

    # Restituisce il numero di byte trasmissibili

    def dim_max(self, cmd, dati, extra=None):
        if cmd is None:
            return self.mdp - 2
        else:
            pkt = bytearray()

            tmp = bytearray(struct.pack('<H', cmd))
            for x in tmp:
                self._aggiungi(pkt, x)

            if extra is not None:
                for x in extra:
                    self._aggiungi(pkt, x)

            dim = 0
            for x in dati:
                self._aggiungi(pkt, x)

                if len(pkt) > self.mdp:
                    break
                else:
                    dim += 1

            return dim

    # ============================================
    # Spedisce il messaggio aggiungendo la parte mancante
    # ============================================

    def _trasmetti(self, msg):
        # Compongo il pacchetto
        pkt = bytearray([PROT._INIZIO_TRAMA])

        for x in msg:
            self._aggiungi(pkt, x)

        if len(pkt[1:]) > self.mdp:
            print('troppi byte')
            return False

        # Aggiungo il crc
        crc = self.crc.new()
        crc.update(msg)
        lCrc = crc.digest()
        self._aggiungi(pkt, lCrc[0])
        self._aggiungi(pkt, lCrc[1])

        # Finisco
        pkt.append(PROT._FINE_TRAMA)

        # Trasmetto
        self.uart.flushInput()
        self.uart.write(pkt)

        return True

    # ============================================
    # Restituisce il messaggio ricevuto o un bytearray vuoto
    # ============================================

    def _ricevi(self):
        pkt = bytearray()
        nega = False
        trovato = False
        # Mi aspetto almeno: inizio + comando[2] + crc[2] + fine
        daLeggere = 6
        while not trovato:
            sdati = self.uart.read(daLeggere)
            if sdati is None:
                continue
            letti = bytearray(sdati)
            if len(letti) == 0:
                break
            for rx in letti:
                if nega:
                    rx = ~rx & 0xFF
                    pkt.append(rx)
                    nega = False
                elif PROT._INIZIO_TRAMA == rx:
                    pkt = bytearray()
                elif PROT._FINE_TRAMA == rx:
                    if len(pkt) >= 4:
                        crc = self.crc.new()
                        crc.update(pkt)
                        x = crc.digest()
                        if x[0] == 0 and x[1] == 0:
                            trovato = True
                            # Tolgo il crc
                            del pkt[-1]
                            del pkt[-1]
                elif PROT._CARATTERE_DI_FUGA == rx:
                    nega = True
                else:
                    pkt.append(rx)
            daLeggere = self.uart.inWaiting()
            if daLeggere == 0:
                daLeggere = 1

        if not trovato:
            pkt = bytearray()

        return pkt

    def _risposta_void(self, cmd):
        rsp = self._ricevi()
        if len(rsp) != 2:
            return False
        elif rsp[0] != cmd[0]:
            return False
        else:
            return rsp[1] == cmd[1] | PROT._RSP_VALIDA

    def _risposta_prm(self, tx, dim):
        rsp = None
        tmp = self._ricevi()
        if len(tmp) < 2:
            pass
        elif tmp[0] != tx[0]:
            pass
        elif tmp[1] != tx[1] | PROT._RSP_VALIDA:
            pass
        elif dim is None:
            rsp = tmp[2:]
        elif len(tmp) != 2 + dim:
            pass
        else:
            rsp = tmp[2:]
        return rsp

    # ============================================
    # Comando senza parametri e senza risposta
    # ============================================

    def cmdVoidVoid(self, cmd):
        tx = bytearray(struct.pack('<H', cmd))
        if not self._trasmetti(tx):
            return False
        else:
            return self._risposta_void(tx)

    # ============================================
    # Comando con parametri e senza risposta
    # ============================================

    def cmdPrmVoid(self, cmd, prm):
        tx = bytearray(struct.pack('<H', cmd))
        tx += prm
        if not self._trasmetti(tx):
            return False
        else:
            return self._risposta_void(tx)

    # ============================================
    # Comando senza parametri ma con risposta
    # ============================================

    def cmdVoidRsp(self, cmd, dim=None):
        tx = bytearray(struct.pack('<H', cmd))
        if not self._trasmetti(tx):
            return None
        else:
            return self._risposta_prm(tx, dim)

    # ============================================
    # Comando con parametri e risposta
    # ============================================

    def cmdPrmRsp(self, cmd, prm, dim=None):
        tx = bytearray(struct.pack('<H', cmd))
        tx += prm
        if not self._trasmetti(tx):
            return None
        else:
            return self._risposta_prm(tx, dim)
