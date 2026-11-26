# GnmScale Game Profiles

*[English](README.md)*

Profili di impostazioni per gioco di **GnmScale**, l'app homebrew per PS4 e
plugin GoldHEN per upscaling e frame generation. Sono i profili scelti dallo
sviluppatore. L'app li scarica da questo repository, e puoi sceglierne uno
dall'app o dal menu in gioco.

Questo repository contiene solo i profili. GnmScale è distribuito a parte.

## Usare i profili

1. Apri GnmScale e scegli un gioco.
2. Vai nella scheda **Profili** e scegli **Scarica i profili dello
   sviluppatore**. Scarica in un solo file tutti i profili pubblicati, per
   tutti i giochi, al posto di quelli dello sviluppatore scaricati prima.
3. Seleziona un profilo e premi **X** per applicarlo. L'app lo salva come
   impostazioni del gioco, quindi è attivo dal prossimo avvio.

In gioco, apri il menu di GnmScale (L3 + R3 di default). La scheda
**Profili** elenca gli stessi profili; premi → su uno per applicarlo mentre
giochi.

I tuoi profili (creati nell'app o con "Salva come nuovo profilo" in gioco)
sono salvati a parte, e un download non li tocca mai.

I profili segnati **Da verificare** non sono ancora stati provati su console
dall'autore. Sono un punto di partenza, non una garanzia. L'elenco completo è
in [GAMES.md](GAMES.md).

## Aggiungere un profilo

1. In `games/` crea una cartella per il gioco, col titolo e i suoi TITLE_ID
   (tutte le edizioni che devono avere gli stessi profili):

   ```
   games/Bloodborne [CUSA00900 CUSA00207 CUSA03173 CUSA03023]/
   ```

2. Mettici dentro il profilo come file `.ini`. Il nome del file è il nome
   mostrato sulla console:

   ```
   games/Bloodborne [CUSA00900 CUSA00207 CUSA03173 CUSA03023]/PS4 Slim - Frame Gen.ini
   ```

   Il contenuto è un `config.ini` di GnmScale (`chiave=valore`), quindi puoi
   copiare la configurazione del gioco dalla console così com'è. Le chiavi che
   un profilo non porta (lingua, diagnostica) vengono ignorate dall'app.

3. Fai commit e push su `main`. La GitHub Action genera
   `dist/profiles.bundle` e `GAMES.md`, e l'app scarica il nuovo profilo la
   prossima volta che scegli **Scarica i profili dello sviluppatore**.

Nient'altro. Un profilo cambia solo le voci che elenca, e tutte le altre
impostazioni del gioco restano come sono.

### Righe facoltative

```ini
description=Frame generation 2x: da 30 a 60 fps a schermo.
author=FrankBarretta
order=1
status=tested
```

`name` sostituisce il nome del file (max 47 byte), `description` è una riga
(max 255 byte), `order` è la posizione nell'elenco (altrimenti in ordine di
nome), `status=tested` segna il profilo come verificato su console.

### Controllo in locale

`python tools/build_bundle.py` fa quello che fa la Action: segnala i problemi
(nessun TITLE_ID nel nome della cartella, lo stesso TITLE_ID in due giochi, un
nome troppo lungo) e rigenera `dist/profiles.bundle` e `GAMES.md`. Non è
obbligatorio lanciarlo. Su una pull request la Action si limita a controllare.
Il formato del pacchetto è descritto nel [README in inglese](README.md#bundle-format).
