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

## Struttura

```
games/
  <gioco>/               una cartella per gioco, nome [a-z0-9_-]
    game.ini             il nome del gioco e tutti i suoi TITLE_ID
    <profilo>.ini        un file per profilo
templates/               da copiare per un gioco o un profilo nuovo
tools/build_bundle.py    controlla tutto e genera il pacchetto
dist/profiles.bundle     quello che l'app scarica (generato, non modificarlo)
GAMES.md                 elenco di giochi e profili (generato)
```

Un profilo vale per tutti i TITLE_ID del `game.ini` del suo gioco: le
edizioni regionali condividono gli stessi file.

Il formato dei file, l'elenco completo delle chiavi e dei valori ammessi e il
formato del pacchetto sono descritti nel [README in inglese](README.md#layout).
Le chiavi sono le stesse di `config.ini` di GnmScale. Un profilo cambia solo le
voci che elenca, e tutte le altre impostazioni del gioco restano come sono.

## Aggiungere o modificare profili

1. Copia `templates/` in `games/<gioco>/` (o modifica un file esistente).
2. Lancia `python tools/build_bundle.py`. Controlla ogni file, poi rigenera
   `dist/profiles.bundle` e `GAMES.md`. Correggi quello che segnala.
3. Fai il commit di tutto, compresi `dist/` e `GAMES.md`.

A ogni push su `main` la GitHub Action lancia lo stesso script, e se il
pacchetto non è aggiornato lo rigenera e fa il commit. Su una pull request si
limita a controllare.
