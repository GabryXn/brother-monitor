# Troubleshooting Report: Problema di Scaling (Super-Zoom) su Brother DCP-L2550DN

## 1. Problema Rilevato dall'Utente
L'utente ha segnalato un malfunzionamento critico durante la stampa da questo computer:
- **Sintomo:** Qualunque documento inviato alla stampante Brother (sia pagina di test che documenti reali) risultava "super zoommato".
- **Effetto:** Il contenuto stampato era così ingrandito da non entrare nei fogli A4, nonostante l'anteprima di stampa sul computer fosse corretta.
- **Ambito:** Il problema sembrava limitato a questo specifico computer, suggerendo un errore di configurazione driver o parametri di invio del job.

---

## 2. Strategia di Debug e Ragionamento

### Ipotesi Iniziali (Sospetti)
1.  **Driver Incompatibile:** Il driver `brlaser` (open source) è ottimo ma talvolta ha problemi con le risoluzioni HQ1200 sui nuovi modelli.
2.  **Mismatch di Risoluzione:** Un classico nei sistemi CUPS: se il computer invia un raster a 1200 DPI ma la stampante lo interpreta come 600 DPI, l'immagine raddoppia di dimensione (effetto zoom 2x).
3.  **Configurazione Regionale:** Mismatch tra "Letter" (USA) e "A4" (Europe), che causa offset e scaling errati.
4.  **Interferenza `ipp-usb`:** La stampante è connessa via USB ma esposta via IPP su `localhost:60000`. Il passaggio attraverso questo proxy poteva corrompere i metadati del job.

### Comandi Utilizzati e Percorso di Investigazione
Il debug è stato condotto analizzando i vari strati del sottosistema di stampa Linux (CUPS):

1.  **Analisi Stato CUPS:**
    ```bash
    lpstat -p -d  # Verifica stampante predefinita e stato.
    lpoptions -l  # Elenco opzioni disponibili nel PPD corrente.
    ```
    *Risultato:* La stampante usava il driver `brlaser` v6.2.7.

2.  **Ispezione del file PPD (PostScript Printer Description):**
    ```bash
    sudo cat /etc/cups/ppd/Brother_DCP_L2550DN.ppd
    ```
    Ho cercato definizioni di `Resolution` e `PageSize`. Ho notato che il driver `brlaser` definiva risoluzioni specifiche (`600dpi`, `1200dpi`) con comandi `setpagedevice` custom.

3.  **Analisi delle Opzioni Utente (Il "Colpevole" n.1):**
    ```bash
    cat ~/.cups/lpoptions
    ```
    *Sorpresa:* Ho trovato `Resolution=1200dpi` forzato a livello utente. In combinazione con il driver `brlaser`, questo è un trigger noto per l'errore di scaling sui modelli L2550.

4.  **Verifica dell'Infrastruttura di Rete/USB:**
    ```bash
    sudo lsof -i :60000
    ipp-usb status
    ```
    Ho confermato che `ipp-usb` stava gestendo la comunicazione. Questo è stato un punto di svolta: se la stampante supporta IPP via USB, i driver tradizionali come `brlaser` sono spesso ridondanti o dannosi.

5.  **Test Driverless (La Svolta):**
    ```bash
    driverless ipp://localhost:60000/ipp/print
    ```
    Questo comando ha confermato che la stampante è perfettamente compatibile con lo standard **IPP Everywhere**.

---

## 3. Analisi del Problema (I Colpevoli)

Perché è stato un debug complesso? Il problema non era in un singolo file, ma nell'interazione tra tre componenti:
1.  **Driver `brlaser`:** Inviava dati raster in un formato che la stampante, quando interrogata via IPP (tramite `ipp-usb`), non scalava correttamente.
2.  **Opzioni Utente (`~/.cups/lpoptions`):** L'impostazione manuale `Resolution=1200dpi` sovrascriveva i default di sistema, forzando un campionamento che la stampante interpretava come "zoom 2x".
3.  **Mancanza di Scaling Dinamico:** Il comando di stampa non specificava esplicitamente `print-scaling=fit`, lasciando che driver e stampante "decidessero" autonomamente, fallendo.

---

## 4. Soluzione Applicata

La risoluzione ha richiesto un approccio radicale: **abbandonare i driver legacy a favore degli standard moderni.**

1.  **Migrazione a IPP Everywhere:**
    Ho riconfigurato la stampante per usare il driver "driverless" nativo di CUPS:
    ```bash
    sudo lpadmin -p Brother_DCP_L2550DN -m everywhere
    ```
    Questo elimina la dipendenza da `brlaser` e usa il motore di rendering interno della stampante (PWG Raster).

2.  **Pulizia delle Opzioni Locali:**
    Ho rimosso le impostazioni forzate che causavano il conflitto:
    ```bash
    lpoptions -p Brother_DCP_L2550DN -r Resolution
    lpoptions -p Brother_DCP_L2550DN -r brlaserEconomode
    ```

3.  **Normalizzazione A4:**
    Ho verificato che `PageSize=A4` fosse impostato correttamente sia nel nuovo PPD che nelle opzioni utente.

---

## 5. Architettura e Gestione Stampanti

### Struttura del Sistema
L'integrazione su questo computer segue un modello moderno di "Driverless Printing over USB":

-   **Connessione Fisica:** USB.
-   **Strato IPP-over-USB (`ipp-usb`):** Un demone di sistema intercetta la connessione USB e la espone come un server HTTP locale sulla porta `60000`. Questo permette al computer di parlare con la stampante usando il protocollo IPP (Internet Printing Protocol) come se fosse in rete.
-   **CUPS (Common UNIX Printing System):** Il gestore di stampa che invia i job al proxy `60000`.
-   **Monitoraggio (`brother-monitor`):** Il progetto Python corrente interroga l'interfaccia web della stampante (sempre tramite il proxy su `60000`) per estrarre livelli di toner e stato del tamburo.

### Altre Stampanti
È presente anche una **HP Color LaserJet MFP M281fdn**, configurata anch'essa con driverless (`HP Printer, driverless`). Ho uniformato la configurazione portando anche la Brother su questo standard (`IPP Everywhere`) per garantire stabilità a lungo termine.

### Criticità Identificate
-   **Conflitto Driver/Protocollo:** L'uso di driver specifici (`brlaser`, `hl1250`, etc.) su stampanti moderne che supportano IPP Everywhere è la causa principale di problemi di scaling e qualità.
-   **Aggiornamenti CUPS:** Le future versioni di CUPS rimuoveranno il supporto ai driver PPD classici; la soluzione "everywhere" applicata oggi rende il sistema già compatibile con il futuro della stampa su Linux.
---

## 6. Appendice: Ripristino Opzioni di Risoluzione (DPI)

### Il Problema della "Qualità Semplificata"
Dopo il passaggio al driver **IPP Everywhere**, l'utente ha notato la scomparsa del selettore numerico della risoluzione (300, 600, 1200 DPI), sostituito da un generico selettore di qualità (*Draft*, *Normal*, *High*). 
Inoltre, per questo specifico modello, il driver automatico mappava erroneamente la modalità "Normal" a 300 DPI, riducendo la nitidezza standard dei documenti.

### Intervento Tecnico (Patch del PPD)
Per restituire il controllo totale all'utente senza rinunciare alla stabilità del driverless, ho modificato manualmente il file PPD della stampante:
1.  Ho inserito un nuovo blocco `OpenUI *Resolution` direttamente nel file `/etc/cups/ppd/Brother_DCP_L2550DN.ppd`.
2.  Ho mappato le risoluzioni native supportate dalla stampante (estratte tramite `ipptool`) ai relativi comandi `setpagedevice` di CUPS.
3.  Ho impostato **600 DPI** come valore predefinito di sistema.

### Guida alle Risoluzioni Ripristinate
Ogni livello di DPI è ora selezionabile individualmente ed è indicato per scopi diversi:

-   **300 DPI (Draft/Bozza):** 
    -   *Uso:* Stampa di documenti interni, testi lunghi senza grafiche complesse, prove di layout.
    -   *Vantaggi:* Massima velocità di stampa, minor consumo di toner, file spool più leggeri.
-   **600 DPI (Standard/Default):** 
    -   *Uso:* Documenti professionali, fatture, corrispondenza ufficiale.
    -   *Vantaggi:* È la risoluzione nativa del tamburo; offre il miglior bilanciamento tra nitidezza del testo e fedeltà dei grigi.
-   **1200 DPI (High Quality):** 
    -   *Uso:* Grafiche vettoriali fini, documenti con piccoli font (sotto i 6pt), loghi con sfumature delicate.
    -   *Vantaggi:* Massima precisione possibile per la meccanica della L2550DN.
    -   *Nota:* La velocità di stampa potrebbe diminuire leggermente a causa del maggior carico di elaborazione del raster.
