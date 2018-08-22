#! /usr/bin/env python

"""
    Racchiude tutto quanto serve per la prova dell'eco
    L'applicazione deve avere:
        *) Un bottone per iniziare e terminare la prova
        *) Una edit col numero di prove
        *) Una edit con la dimensione (opzionale)
        *) Una etichetta per i messaggi
        *) Una progressbar
        *) Una coda dove inviare i messaggi di aggiornamento grafica ...
        *) ... e le funzioni che gestiscono i messaggi:
              *) ecoFinePerErrore(quanti)
              *) ecoInfinito()
              *) ecoFinito(quanti)
           Queste funzioni devono invocare quelle omonime dell'oggetto passando
           il dispositivo
"""

import threading
import time
import random

import utili


class ECO(object):

    def __init__(self, bottone,
                 numeco,
                 dimeco,
                 msg,
                 progBar,
                 coda):
        self.bottone = bottone
        self.numEco = numeco
        self.dimEco = dimeco
        self.msg = msg
        self.progBar = progBar
        self.coda = coda

        self.continuaEco = False

        self.ecoConta = 0
        self.ecoTot = 0
        self.ecoInizio = 0
        self.ecoMux = threading.Lock()

        self.timerEco = None
        self.durataTimer = None

        self.dimdati = 0

    def _genera_dati_bin(self, dispo):
        if self.dimdati <= 0:
            self.dimdati = dispo.dim_max(None, None)

        dati = [None, None]
        dim = (self.dimdati + 256 - 1) // 256

        dato = bytearray(range(256))
        dim -= 1
        while dim:
            dato += bytearray(range(256))
            dim -= 1
        random.shuffle(dato)
        dimp = dispo.dim_max(0x0000, dato[:self.dimdati])
        dati[0] = dato[:dimp]
        random.shuffle(dato)
        dimp = dispo.dim_max(0x0000, dato[:self.dimdati])
        dati[1] = dato[:dimp]

        return dati

    def _genera_dati(self, dispo):
        if self.dimdati <= 0:
            self.dimdati = dispo.dim_max(None, None)

        return utili.genera_dati(self.dimdati)

    def aggiornaEco(self):
        if self.continuaEco:
            self.ecoMux.acquire()
            durata = time.clock() - self.ecoInizio
            self.ecoMux.release()

            self.msg.set(utili.stampaDurata(int(round(durata * 1000.0, 0))))

            self.timerEco = self.bottone.after(
                self.durataTimer, self.aggiornaEco)
        else:
            self.bottone.after_cancel(self.timerEco)

    # GUI

    def Bottone(self):
        if "Basta" == self.bottone["text"]:
            self.continuaEco = False
            self.bottone.after_cancel(self.timerEco)
        else:
            dimeco = 4
            if self.dimEco is not None:
                esito, dimeco = utili.validaCampo(self.dimEco.get(), None, None)
                if not esito:
                    dimeco = 4
            self.dimdati = dimeco
            esito, quanti = utili.validaCampo(self.numEco.get(), None, None)
            if esito:
                self.continuaEco = True
                self.bottone["text"] = "Basta"

                self.msg.set("Aspetta ...")

                if quanti < 0:
                    self.coda.put(("ecoFinePerErrore", self, -quanti))
                elif 0 == quanti:
                    self.coda.put(("ecoInfinito", self))
                else:
                    self.coda.put(("ecoFinito", self, quanti))

                # Imposto un timer per le prove lunghe
                self.durataTimer = 60 * 1000
                self.timerEco = self.bottone.after(
                    self.durataTimer, self.aggiornaEco)
            else:
                self.msg.set("Quanti echi ???")

    # Esegui

    def ecoFinePerErrore(self, quanti, dispo):
        dati = self._genera_dati(dispo)
        dato = dati[0]

        self.progBar.start(10)

        self.ecoConta = 0
        self.ecoTot = 0

        self.ecoInizio = time.clock()

        while self.ecoConta < quanti and self.continuaEco:
            self.ecoMux.acquire()

            self.ecoTot += 1
            if not dispo.Eco(dato):
                self.ecoConta += 1
            self.ecoMux.release()

            if dato is dati[0]:
                dato = dati[1]
            else:
                dato = dati[0]

        self.continuaEco = False
        durata = time.clock() - self.ecoInizio
        sdurata = utili.stampaDurata(int(round(durata * 1000.0, 0)))

        if 0 == self.ecoConta:
            milli = round(1000.0 * durata / self.ecoTot, 3)
            self.msg.set(
                "Eco: OK %d in %s (%.3f ms)" %
                (self.ecoTot, sdurata, milli))
        else:
            self.msg.set(
                "Eco: %d errori su %d [%s]" %
                (self.ecoConta, self.ecoTot, sdurata))

        self.progBar.stop()
        self.bottone["text"] = "Eco"

    def ecoInfinito(self, dispo):
        dati = self._genera_dati(dispo)
        dato = dati[0]

        self.progBar.start(10)

        self.ecoConta = 0
        self.ecoTot = 0

        self.ecoInizio = time.clock()

        while self.continuaEco:
            self.ecoMux.acquire()

            self.ecoTot += 1
            if dispo.Eco(dato):
                self.ecoConta += 1

            self.ecoMux.release()

            if dato is dati[0]:
                dato = dati[1]
            else:
                dato = dati[0]

        durata = time.clock() - self.ecoInizio
        sdurata = utili.stampaDurata(int(round(durata * 1000.0, 0)))

        if self.ecoConta == self.ecoTot:
            milli = round(1000.0 * durata / self.ecoConta, 3)
            self.msg.set(
                "Eco: OK %d in %s (%.3f ms)" %
                (self.ecoConta, sdurata, milli))
        elif 0 == self.ecoConta:
            self.msg.set("Eco: ERR %d in %s" % (self.ecoTot, sdurata))
        else:
            self.msg.set(
                "Eco: OK %d / %d in %s" %
                (self.ecoConta, self.ecoTot, sdurata))

        self.progBar.stop()
        self.bottone["text"] = "Eco"

    def ecoFinito(self, quanti, dispo):
        dati = self._genera_dati(dispo)
        dato = dati[0]

        self.progBar.start(10)

        self.ecoConta = 0
        self.ecoTot = 0
        tot = 0

        self.ecoInizio = time.clock()

        while self.ecoTot < quanti and self.continuaEco:
            self.ecoMux.acquire()

            self.ecoTot += 1
            if dispo.Eco(dato):
                self.ecoConta += 1
                tot += len(dato)

            self.ecoMux.release()

            if dato is dati[0]:
                dato = dati[1]
            else:
                dato = dati[0]

        self.continuaEco = False
        durata = time.clock() - self.ecoInizio
        sdurata = utili.stampaDurata(int(round(durata * 1000.0, 0)))

        if self.ecoConta == self.ecoTot:
            milli = round(1000.0 * durata / self.ecoConta, 3)
            tput = round(tot / durata, 1)
            kib = round(tot / (durata * 1024), 1)
            self.msg.set(
                "Eco: OK %d in %s (%.3f ms = %.1f B/s = %.1f KiB/s)" %
                (self.ecoConta, sdurata, milli, tput, kib))
        elif 0 == self.ecoConta:
            self.msg.set("Eco: ERR %d in %s" % (self.ecoTot, sdurata))
        else:
            self.msg.set(
                "Eco: OK %d / %d in %s" %
                (self.ecoConta, self.ecoTot, sdurata))

        self.progBar.stop()
        self.bottone["text"] = "Eco"
