#! /usr/bin/env python

"""
    Implementa i metodi ereditati dalla grafica
"""

import sys
import time

try:
    # 2
    import Queue as coda
    import tkFileDialog as dialogo
except ImportError:
    # 3
    import queue as coda
    import tkinter.filedialog as dialogo

import gui
import gui_support

import esegui
import eco
import dispositivo
import utili

NOME_UART = None
if sys.platform.startswith("win32"):
    NOME_UART = "COM"
else:
    NOME_UART = "/dev/ttyUSB"

INDIRIZZO_IP = "192.168.4.1"

TAB_CHIUSA = {1: False, 2: False, 3: False}
TAB_APERTA = {1: True, 2: True, 3: True}


class SC635(gui.New_Toplevel_1):
    def __init__(self, master=None):
        self.master = master
        gui.New_Toplevel_1.__init__(self, master)

        gui_support.portaSeriale.set(NOME_UART)
        gui_support.indirizzoIP.set(INDIRIZZO_IP)

        self._imposta_tab(TAB_CHIUSA)

        self.dispo = None
        self.timerLed = None

        # Code per la comunicazione fra grafica e ciccia
        self.codaEXE = coda.Queue()
        self.codaGUI = coda.Queue()

        self.task = esegui.taskEsecutore(self.codaEXE, self.codaGUI)
        self.task.start()

        self.eco = eco.ECO(self.Button3,
                           gui_support.numEco,
                           gui_support.dimEco,
                           gui_support.Messaggio,
                           self.TProgressbar1,
                           self.codaEXE)

        # Comandi dall'esecutore
        self.cmd = {
        }
        self._esegui_GUI()

    def __del__(self):
        pass

    def chiudi(self):
        self.codaEXE.put(("esci",))
        self.task.join()

        if self.dispo is not None:
            self.dispo.Chiudi()
            self.dispo = None

    def _imposta_tab(self, lista):
        for tab in lista:
            stato = 'disabled'
            if lista[tab]:
                stato = 'normal'

            self.TNotebook1.tab(tab, state=stato)

    def _esegui_GUI(self):
        try:
            msg = self.codaGUI.get(0)

            if msg[0] in self.cmd:
                if 2 == len(msg):
                    self.cmd[msg[0]](msg[1])
                else:
                    self.cmd[msg[0]]()
        except coda.Empty:
            pass

        self.master.after(300, self._esegui_GUI)

    #========== SERIALE ======================================================

    def apriFTDI(self):
        if self.dispo is None:
            self.dispo = dispositivo.DISPOSITIVO(vid='0403', pid='6010')
            if not self.dispo.a_posto():
                del self.dispo
                self.dispo = None
            else:
                self.codaEXE.put(("Dispositivo", self.dispo))

                self.Button47['text'] = 'Mollala'

                self.Entry1['state'] = 'readonly'
                self.Button1['state'] = 'disabled'
                self.Entry4['state'] = 'readonly'
                self.Button4['state'] = 'disabled'

                self._imposta_tab(TAB_APERTA)
        else:
            self.dispo.Chiudi()
            self.dispo = None
            self.codaEXE.put(("Dispositivo", self.dispo))

            self.Button47['text'] = 'Usa FTDI'

            self.Button1['state'] = 'normal'
            self.Entry1['state'] = 'normal'
            self.Button4['state'] = 'normal'
            self.Entry4['state'] = 'normal'

            self._imposta_tab(TAB_CHIUSA)

    def apriSeriale(self):
        if self.dispo is None:
            porta = gui_support.portaSeriale.get()
            if porta is None:
                gui_support.portaSeriale.set(NOME_UART)
            elif 0 == len(porta):
                gui_support.portaSeriale.set(NOME_UART)
            else:
                self.dispo = dispositivo.DISPOSITIVO(porta=porta)
                if not self.dispo.a_posto():
                    del self.dispo
                    self.dispo = None
                    gui_support.portaSeriale.set(NOME_UART)
                else:
                    self.codaEXE.put(("Dispositivo", self.dispo))

                    self.Entry1['state'] = 'readonly'
                    self.Button1['text'] = 'Mollala'

                    self.Button47['state'] = 'disabled'
                    self.Entry4['state'] = 'readonly'
                    self.Button4['state'] = 'disabled'

                    self._imposta_tab(TAB_APERTA)
        else:
            self.dispo.Chiudi()
            self.dispo = None
            self.codaEXE.put(("Dispositivo", self.dispo))

            self.Button1['text'] = 'Usa questa'
            self.Entry1['state'] = 'normal'

            self.Button47['state'] = 'normal'
            self.Button4['state'] = 'normal'
            self.Entry4['state'] = 'normal'

            gui_support.portaSeriale.set(NOME_UART)
            self._imposta_tab(TAB_CHIUSA)

    def apriSocket(self):
        if self.dispo is None:
            indip = gui_support.indirizzoIP.get()
            if indip is None:
                gui_support.indirizzoIP.set(INDIRIZZO_IP)
            elif len(indip) < 7:
                gui_support.indirizzoIP.set(INDIRIZZO_IP)
            else:
                self.dispo = dispositivo.DISPOSITIVO(indip=indip)
                if not self.dispo.a_posto():
                    del self.dispo
                    self.dispo = None
                    gui_support.indirizzoIP.set(INDIRIZZO_IP)
                else:
                    self.codaEXE.put(("Dispositivo", self.dispo))

                    self.Entry4['state'] = 'readonly'
                    self.Button4['text'] = 'Mollalo'

                    self.Button47['state'] = 'disabled'
                    self.Entry1['state'] = 'readonly'
                    self.Button1['state'] = 'disabled'

                    self._imposta_tab(TAB_APERTA)
        else:
            self.dispo.Chiudi()
            self.dispo = None
            self.codaEXE.put(("Dispositivo", self.dispo))

            self.Button4['text'] = 'TCP'
            self.Entry4['state'] = 'normal'

            self.Button47['state'] = 'normal'
            self.Button1['state'] = 'normal'
            self.Entry1['state'] = 'normal'

            gui_support.indirizzoIP.set(INDIRIZZO_IP)
            self._imposta_tab(TAB_CHIUSA)

    # ========== VARIE ========================================================

    def Eco(self):
        gui_support.Messaggio.set("Aspetta ...")
        self.codaEXE.put(("eco",))

    def ecoProva(self, dummy):
        self.eco.Bottone()

    def aggiorna(self):
        opzioni = {
            'parent': self.master,
            'filetypes': [('DoIP', '.agg')],
            'title': 'Scegli il file'
        }
        filename = dialogo.askopenfilename(**opzioni)
        if filename is None:
            gui_support.Messaggio.set("Hai cambiato idea?")
        elif 0 == len(filename):
            gui_support.Messaggio.set("Hai cambiato idea?")
        else:
            gui_support.Messaggio.set("Aspetta ...")
            self.codaEXE.put(("aggiorna", filename))

    def ver(self):
        gui_support.veri.set('---')
        gui_support.verd.set('---')
        gui_support.Messaggio.set("Aspetta ...")
        self.codaEXE.put(("ver", ))

    # ========== PRODUZIONE ===================================================

    def leggi_cp(self):
        gui_support.cp.set("---")
        gui_support.Messaggio.set("Aspetta ...")
        self.codaEXE.put(("leggi_cp",))

    def inventa_cp(self):
        gui_support.cp.set(utili.cod_prod())

    def scrivi_cp(self):
        ns = gui_support.cp.get()
        if len(ns) == 0 or len(ns) > 12:
            gui_support.Messaggio.set("? 1 <= cod. prodotto <= 12 ?")
        else:
            gui_support.Messaggio.set("Aspetta ...")
            self.codaEXE.put(("scrivi_cp", ns))

    def leggi_cs(self):
        gui_support.cs.set("---")
        gui_support.Messaggio.set("Aspetta ...")
        self.codaEXE.put(("leggi_cs",))

    def inventa_cs(self):
        gui_support.cs.set(utili.cod_scheda('???'))

    def scrivi_cs(self):
        ns = gui_support.cs.get()
        if len(ns) == 0 or len(ns) > 11:
            gui_support.Messaggio.set("? 1 <= cod. scheda <= 11 ?")
        else:
            gui_support.Messaggio.set("Aspetta ...")
            self.codaEXE.put(("scrivi_cs", ns))

    # ========== HW ===========================================================

    def tst_zero(self):
        gui_support.Messaggio.set("Aspetta ...")
        self.codaEXE.put(("tst_zero",))

    def tst_lgg(self):
        gui_support.tst.set("---")
        gui_support.Messaggio.set("Aspetta ...")
        self.codaEXE.put(("tst_lgg",))

    def cavo(self):
        gui_support.Messaggio.set("Aspetta ...")
        self.codaEXE.put(("cavo",))

    def mobd(self):
        eth = '1' == gui_support.io33.get()
        gui_support.Messaggio.set("Aspetta ...")
        self.codaEXE.put(("mobd", eth))

    def eth(self):
        esp32 = '1' == gui_support.io5.get()
        gui_support.Messaggio.set("Aspetta ...")
        self.codaEXE.put(("eth", esp32))

    def led(self):
        rosso = '1' == gui_support.led.get()
        gui_support.Messaggio.set("Aspetta ...")
        self.codaEXE.put(("led", rosso))

    def _led_ripetuto(self):
        rosso = '1' == gui_support.led.get()
        gui_support.led.set(not rosso)
        gui_support.Messaggio.set("Aspetta ...")
        self.codaEXE.put(("led", not rosso))

        self.timerLed = self.Button21.after(1000, self._led_ripetuto)

    def ledr(self):
        if self.Button21['text'] == 'Ripetutamente':
            # Inizio prova
            self.Button21['text'] = 'Basta'
            self.timerLed = self.Button21.after(1000, self._led_ripetuto)
        else:
            self.Button21.after_cancel(self.timerLed)
            self.Button21['text'] = 'Ripetutamente'

    def rid_ini(self):
        gui_support.Messaggio.set("Aspetta ...")
        self.codaEXE.put(("rid_ini", ))

    def rid_fin(self):
        gui_support.Messaggio.set("Aspetta ...")
        self.codaEXE.put(("rid_fin", ))

    def rid_esi(self):
        gui_support.Messaggio.set("Aspetta ...")
        self.codaEXE.put(("rid_esi", ))

    def phy_reset(self):
        esito, ms = utili.validaCampo(gui_support.phy_ms.get(), 1, 2550)
        if esito:
            ms = (ms + 9) // 10
            ms *= 10
            gui_support.phy_ms.set(ms)
            gui_support.Messaggio.set("Aspetta ...")
            self.codaEXE.put(("phy_reset", ms))
        else:
            gui_support.Messaggio.set("? 10, 20, ... 2550 ?")


if __name__ == '__main__':
    ROOT = gui.Tk()
    ROOT.title('Test SC635')
    ROOT.geometry("603x581+292+128")

    gui_support.set_Tk_var()

    gui_support.Messaggio.set("Pronto!")
    gui_support.cavo.set(0)
    gui_support.io33.set(0)
    gui_support.io5.set(0)
    gui_support.led.set(0)

    FINESTRA = SC635(ROOT)
    gui_support.init(ROOT, FINESTRA)
    ROOT.mainloop()

    FINESTRA.chiudi()
