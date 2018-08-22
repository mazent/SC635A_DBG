#!/usr/bin/env python

"""
    Varie
"""
from __future__ import print_function

import binascii
import threading
import struct
import os
#import psutil
#import webbrowser
import random
import string


import crcmod


def validaStringa(x, dimmin=None, dimmax=None):
    """
        Usata sui campi testo per validare che la
        lunghezza sia fra un minimo e un massimo
    """
    esito = False

    if x is None:
        pass
    elif dimmin is None:
        if dimmax is None:
            # Accetto qls dimensione
            esito = True
        elif len(x) > dimmax:
            pass
        else:
            esito = True
    elif len(x) < dimmin:
        pass
    elif dimmax is None:
        esito = True
    elif len(x) > dimmax:
        pass
    else:
        esito = True

    return esito


def validaCampo(x, mini=None, maxi=None):
    """
        Se la stringa x e' un intero, controlla
        che sia tra i due estremi inclusi
    """
    esito = False
    val = None
    while True:
        if x is None:
            break

        if len(x) == 0:
            break

        try:
            val = int(x)
        except ValueError:
            try:
                val = int(x, 16)
            except ValueError:
                pass

        if val is None:
            break

        # Entro i limiti?
        if mini is None:
            pass
        elif val < mini:
            break
        else:
            pass

        if maxi is None:
            pass
        elif val > maxi:
            break
        else:
            pass

        esito = True
        break

    return esito, val


def strVer(v):
    """
        Converte la versione del fw in stringa
    """
    ver = ""

    if v == 0:
        ver = '???'
    else:
        vmag = v >> 24
        vmin = v & 0xFFFFFF

        if vmag == 0:
            ver += "(dbg) "
        else:
            ver += str(vmag)
            ver += "."

        ver += str(vmin)

    return ver


def verStr(v):
    """
        Converte una stringa x.y nella versione del fw
    """
    magg, dummy, mino = v.partition('.')

    esito, ver = validaCampo(magg, 0, 255)

    if not esito:
        return False, 0

    esito, v2 = validaCampo(mino, 0, 0xFFFFFF)
    if not esito:
        return False, 0

    ver <<= 24
    ver += v2

    return True, ver


def intEsa(val, cifre=8):
    """
        Converte un valore in stringa esadecimale senza 0x iniziale
    """
    x = hex(val)
    s = x[2:]
    ver = ""
    dim = len(s)
    while dim < cifre:
        ver += "0"
        dim += 1

    ver += s.upper()

    return ver


def StampaEsa(cosa, titolo=''):
    """
        Stampa un dato binario
    """
    if cosa is None:
        print('<vuoto>')
    else:
        print(titolo, binascii.hexlify(cosa))
        # print ''.join('{:02X.}'.format(x) for x in cosa)


def gomsm(conv, div):
    """
        Converte un tempo in millisecondi in una stringa
    """
    if conv[-1] < div[0]:
        return conv
    else:
        r = conv[-1] % div[0]
        v = conv[-1] // div[0]

        conv = conv[:len(conv) - 1]
        conv = conv + (r, v)

        div = div[1:]

        if len(div):
            return gomsm(conv, div)
        else:
            return conv


def stampaDurata(milli):
    """
        Converte un numero di millisecondi in una stringa
        (giorni, ore, minuti, secondi millisecondi)
    """
    x = gomsm((milli,), (1000, 60, 60, 24))
    u = ('ms', 's', 'm', 'o', 'g')

    durata = ""
    for i in range(0, len(x)):
        if len(durata):
            durata = ' ' + durata
        durata = str(x[i]) + u[i] + durata
    return durata


def baMac(mac):
    """
        Converte da mac a bytearray
    """
    componenti = mac.split(':')
    if len(componenti) != 6:
        return None
    else:
        mac = bytearray()
        for elem in componenti:
            esito, val = validaCampo('0x' + elem, 0, 255)
            if esito:
                mac += bytearray([val])
            else:
                mac = None
                break

        return mac


class problema(Exception):

    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


class periodico(threading.Thread):

    def __init__(self, funzione, param=None):
        threading.Thread.__init__(self)

        self.secondi = None
        self.funzione = funzione
        self.param = param

        self.evento = threading.Event()

    def run(self):
        while True:
            esci = self.evento.wait(self.secondi)
            if esci:
                break

            if self.param is not None:
                self.funzione(self.param)
            else:
                self.funzione()

    def avvia(self, secondi):
        if self.secondi is None:
            self.secondi = secondi
            self.start()

    def termina(self):
        if self.secondi is not None:
            self.evento.set()
            self.join()
            self.secondi = None

    def attivo(self):
        return self.secondi is not None


def crcSTM32(dati, crc=0xFFFFFFFF):
    """
        Calcola il crc come il processore
    """
    calcola = crcmod.mkCrcFun(0x104C11DB7, 0xFFFFFFFF, False)

    while len(dati):
        gira = struct.unpack('>I', dati[0:4])[0]
        dati = dati[4:]
        girati = struct.pack('<I', gira)
        crc = calcola(girati, crc)

    return crc


def stampaTabulare(pos, dati, prec=4):
    """
        Stampa il bytearray dati incolonnando per 16
        prec e' il numero di cifre di pos
    """
    testa_riga = '%0' + str(prec) + 'X '

    print('00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F'.rjust(prec + (3 * 16)))
    primo = pos & 0xFFFFFFF0

    bianchi = pos & 0x0000000F
    riga = testa_riga % primo
    while bianchi:
        riga += '   '
        bianchi -= 1

    conta = pos & 0x0000000F
    for x in dati:
        riga += '%02X ' % (x)
        conta += 1
        if conta == 16:
            print(riga)
            primo += 16
            riga = testa_riga % primo
            conta = 0
    if conta:
        print(riga)


def converti_ba(ba):
    """
        Converte un bytearray in un long
    """
    x = int(0)
    for idx in range(0, len(ba)):
        elem = len(ba) - 1 - idx
        x <<= 8
        x += ba[elem]

    return x


def gira_ba(ba):
    """
        Inverte i byte: gli ultimi saranno i primi
    """
    girato = bytearray()

    for idx in range(0, len(ba)):
        elem = len(ba) - 1 - idx
        girato.append(ba[elem])

    return girato


def converti_long(l):
    """
        Converte un long in un bytearray
    """
    x = bytearray()

    while l:
        x.append(l & 0xFF)
        l >>= 8

    return x


def elimina_estensione(completo):
    path, nomest = os.path.split(completo)
    nome, est = os.path.splitext(nomest)
    return os.path.join(path, nome)

# dato il nome del programma, restituisce il nome col percorso
# (se e' in esecuzione)

# def trova_nome_exe(prog):
#     for p in psutil.process_iter(attrs=["name", "exe", "cmdline"]):
#         if prog == p.info['name']:
#             return p.exe()
#
#     return None

# apre l'indirizzo con chrome o col predefinito
# restituisce il percorso completo di chrome

# def http(indirizzo, crome):
#     if crome is not None:
#         # gia' registrato
#         c = webbrowser.get('chrome')
#         c.open(indirizzo)
#     else:
#         # lo cerco
#         crome = trova_nome_exe('chrome.exe')
#         try:
#             if crome is None:
#                 # apro col predefinito
#                 webbrowser.open(indirizzo)
#             else:
#                 webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(crome))
#                 c = webbrowser.get('chrome')
#                 c.open(indirizzo)
#         except webbrowser.Error:
#             crome = None
#
#     return crome

def cod_finto(dim):
    base = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
    cod = ''
    while dim > 0:
        random.shuffle(base)
        dimp = min(dim, len(base))
        cod = cod + ''.join(base[:dimp])
        dim -= dimp

    return cod

# Crea un finto codice scheda

def cod_scheda(pre):
    return pre + 'py' + cod_finto(6)

# Crea un finto codice prodotto

def cod_prod():
    return cod_finto(12)

# Genera due bytearray con dimdati lettere/cifre casuali
def genera_dati(dimdati):
    dati = [None, None]

    stampabili = string.ascii_letters + string.digits
    base = bytearray(stampabili.encode('ascii'))
    # arrotondo dimdati al numero di caratteri base
    dim = (dimdati + len(base) - 1) // len(base)

    # creo un vettore con tante base quante me ne servono
    dato = bytearray(base)
    dim -= 1
    while dim:
        dato += base
        dim -= 1

    # mescolo ...
    random.shuffle(dato)
    # ... ed estraggo quelli che servono
    dati[0] = dato[:dimdati]

    random.shuffle(dato)
    dati[1] = dato[:dimdati]

    return dati
