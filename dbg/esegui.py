#! /usr/bin/env python

"""
    Per non bloccare la grafica viene creato un task
    che aspetta i comandi e li esegue
"""

from __future__ import print_function

import threading

import gui_support
import utili


class taskEsecutore(threading.Thread):

    def __init__(self, codaEXE, codaGUI):
        threading.Thread.__init__(self)

        self.coda_exe = codaEXE
        self.coda_gui = codaGUI

        self.dispo = None

        self.comando = {
            'ecoFinito': self._eco_limite,
            'ecoInfinito': self._eco_8,
            'ecoFinePerErrore': self._eco_fine_x_errore,

            'eco': self._eco,
            'aggiorna': self._aggiorna,
            'ver': self._versione,

            'leggi_cp': self._cod_prod_l,
            'scrivi_cp': self._cod_prod_s,
            'leggi_cs': self._cod_schd_l,
            'scrivi_cs': self._cod_schd_s,

            'tst_zero': self._tst_azzera,
            'tst_lgg': self._tst_leggi,
            'cavo': self._cavo_presente,
            'mobd': self._mobd,
            'eth': self._ethernet,
            'led': self._led,
            'rid_ini': self._rileva_doip_inizio,
            'rid_fin': self._rileva_doip_fine,
            'rid_esi': self._rileva_doip_esito,
            'phy_reset': self._resetta_phy
        }

    def run(self):
        while True:
            lavoro = self.coda_exe.get()
            if "esci" == lavoro[0]:
                break
            elif "Dispositivo" == lavoro[0]:
                self.dispo = lavoro[1]
            elif not lavoro[0] in self.comando:
                gui_support.Messaggio.set("? comando sconosciuto ?")
            else:
                self.comando[lavoro[0]](lavoro)

    def _manda_alla_grafica(self, x, y=None):
        if y is None:
            self.coda_gui.put((x))
        else:
            self.coda_gui.put((x, y))

    # Invocati dall'eco
    def _eco_8(self, prm):
        prm[1].ecoInfinito(self.dispo)

    def _eco_limite(self, prm):
        prm[1].ecoFinito(prm[2], self.dispo)

    def _eco_fine_x_errore(self, prm):
        prm[1].ecoFinePerErrore(prm[2], self.dispo)

    # ========== VARIE ========================================================

    def _eco(self, dummy):
        if self.dispo.Eco():
            gui_support.Messaggio.set("Eco: OK")
        else:
            gui_support.Messaggio.set("Eco: ERRORE")

    def _aggiorna(self, prm):
        try:
            dati = None
            with open(prm[1], "rb") as fileBIN:
                dati = fileBIN.read()

            if dati is None:
                raise utili.problema("Aggiorna: file illeggibile")

            dimdati = len(dati)
            if not self.dispo.agg_inizio(dimdati):
                raise utili.problema("Aggiorna: ERRORE inizio")

            # cinema
            prog = 0
            gui_support.aggiorna.set(0)

            while len(dati):
                dimcorr = self.dispo.agg_dati(prog, dati)
                if dimcorr == 0:
                    raise utili.problema("Aggiorna: ERRORE dati")
                prog += dimcorr
                perc = 100.0 * float(prog) / float(dimdati)
                gui_support.aggiorna.set(int(perc))
                dati = dati[dimcorr:]

            if not self.dispo.agg_fine():
                raise utili.problema("Aggiorna: ERRORE fine")

            gui_support.Messaggio.set("Aggiorna: OK")

        except utili.problema as err:
            gui_support.Messaggio.set(str(err))

    def _versione(self, _):
        conta = 0

        ver = self.dispo.agg_ver()
        if ver is not None:
            gui_support.veri.set(utili.strVer(ver))
            conta += 1

        data = self.dispo.agg_data()
        if data is not None:
            gui_support.verd.set(data)
            conta += 1

        if conta == 2:
            gui_support.Messaggio.set("Versione: OK")
        elif conta == 1:
            gui_support.Messaggio.set("Versione: QUASI")
        else:
            gui_support.Messaggio.set("Versione: ERRORE")

    # ========== PRODUZIONE ===================================================

    def _cod_prod_l(self, _):
        ns = self.dispo.leggi_prodotto()
        if ns is None:
            gui_support.Messaggio.set("Cod. prodotto: ERRORE")
        else:
            gui_support.cp.set(ns)
            gui_support.Messaggio.set("Cod. prodotto: OK")

    def _cod_prod_s(self, prm):
        if self.dispo.scrivi_prodotto(prm[1]):
            gui_support.Messaggio.set("Cod. prodotto: OK")
        else:
            gui_support.Messaggio.set("Cod. prodotto: ERRORE")

    def _cod_schd_l(self, _):
        ns = self.dispo.leggi_scheda()
        if ns is None:
            gui_support.Messaggio.set("Cod. scheda: ERRORE")
        else:
            gui_support.cs.set(ns)
            gui_support.Messaggio.set("Cod. scheda: OK")

    def _cod_schd_s(self, prm):
        if self.dispo.scrivi_scheda(prm[1]):
            gui_support.Messaggio.set("Cod. scheda: OK")
        else:
            gui_support.Messaggio.set("Cod. scheda: ERRORE")

    # ========== HW ===========================================================

    def _tst_azzera(self, _):
        if self.dispo.azzera_tasto():
            gui_support.Messaggio.set("Tasto: OK")
        else:
            gui_support.Messaggio.set("Tasto: ERRORE")

    def _tst_leggi(self, _):
        cnt = self.dispo.leggi_tasto()
        if cnt is None:
            gui_support.Messaggio.set("Tasto: ERRORE")
        else:
            gui_support.tst.set(cnt)
            gui_support.Messaggio.set("Tasto: OK")

    def _cavo_presente(self, _):
        cavo = self.dispo.cavo_in_rj45()
        if cavo is None:
            gui_support.Messaggio.set("Cavo: ERRORE")
        else:
            gui_support.cavo.set(cavo)
            gui_support.Messaggio.set("Cavo: OK")

    def _mobd(self, prm):
        if self.dispo.mobd(prm[1]):
            gui_support.Messaggio.set("MOBD: OK")
        else:
            gui_support.Messaggio.set("MOBD: ERRORE")

    def _ethernet(self, prm):
        if self.dispo.ethernet(prm[1]):
            gui_support.Messaggio.set("Eth: OK")
        else:
            gui_support.Messaggio.set("Eth: ERRORE")

    def _led(self, prm):
        if self.dispo.led(prm[1]):
            gui_support.Messaggio.set("Led: OK")
        else:
            gui_support.Messaggio.set("Led: ERRORE")

    def _rileva_doip_inizio(self, _):
        if self.dispo.ril_doip_ini():
            gui_support.Messaggio.set("Rileva DoIP: OK")
        else:
            gui_support.Messaggio.set("Rileva DoIP: ERRORE")

    def _rileva_doip_fine(self, _):
        if self.dispo.ril_doip_fin():
            gui_support.Messaggio.set("Rileva DoIP: OK")
        else:
            gui_support.Messaggio.set("Rileva DoIP: ERRORE")

    def _rileva_doip_esito(self, _):
        doip = self.dispo.ril_doip_ris()
        if doip is None:
            gui_support.Messaggio.set("Rileva DoIP: ERRORE")
        else:
            gui_support.doip.set(doip)
            gui_support.Messaggio.set("Rileva DoIP: OK")

    def _resetta_phy(self, prm):
        if self.dispo.phy_reset(prm[1]):
            gui_support.Messaggio.set("Reset PHY: OK")
        else:
            gui_support.Messaggio.set("Reset PHY: ERRORE")