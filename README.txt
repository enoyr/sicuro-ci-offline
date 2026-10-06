SICURO — PACCHETTO RUNNER CI OFFLINE

Scarica il pacchetto completo (circa 246 MB), senza account:
https://github.com/enoyr/sicuro-ci-offline/releases/download/v2026.10.06/sicuro-code-fix-runner-offline-2026-10-06.zip

Contiene l’immagine CI linux/amd64 già pronta, i due file da sostituire
nel repository sicuro-code e le istruzioni per importarli nell’intranet.

1. Scaricare lo ZIP e trasferirlo nella rete del cliente.
2. Importare l’immagine in Harbor seguendo INSTALLAZIONE.txt.
3. Sostituire .gitlab-ci.yml e ci/build-site.py in sicuro-code.
4. Eseguire la pipeline; build_publish resta manuale.

Non occorre un account GitHub. Nessun accesso a GitHub è richiesto
alla pipeline o ai server del cliente: il pacchetto si trasferisce offline.

SHA256 dello ZIP:
a7c68db5336b84002a6627ab9ec35eb19bb2125f5633e14940b233497c0236b5
