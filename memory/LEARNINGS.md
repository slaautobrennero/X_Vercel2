# Learnings
- requirements.txt: dopo `pip freeze > requirements.txt` RIMUOVERE la riga `emergentintegrations==...` (non esiste per il Pi, rompe la build Docker). Successo a v0.14.3.
- Il backend sul Pi gira in Docker: nuove variabili .env -> aggiungerle anche a docker/docker-comp.yml (environment) e chiedere `docker compose up -d --force-recreate backend`.
