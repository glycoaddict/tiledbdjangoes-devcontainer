(for f in .offlinedev djangotiledb_project; do sshpass -f password.txt rsync -rtvz ${f} choosf@192.168.145.25:/home/choosf/devcontainer/ && echo Sent ${f} & done ; wait)  ; echo "finished";
# (for f in .offlinedev .devcontainer djangotiledb_project; do sshpass -f password.txt rsync -rtvz ${f} choosf@192.168.145.25:/home/choosf/devcontainer/ && echo Sent ${f} & done ; wait)  ; echo "finished";


