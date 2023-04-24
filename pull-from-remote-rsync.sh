# sshpass -f password.txt rsync -rtvz --dry-run  choosf@192.168.145.25:/home/choosf/devcontainer/djangotiledb_project/tilequery/ djangotiledb_project/tilequery/ && echo "finished"
sshpass -f password.txt rsync -rtvz choosf@192.168.145.25:/home/choosf/devcontainer/djangotiledb_project/tilequery/ djangotiledb_project/tilequery/ && echo "finished"
