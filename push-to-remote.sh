(for f in .offlinedev/ .devcontainer/ djangotiledb_project/; do sshpass -f password.txt scp -r ${f} choosf@192.168.145.25:/home/choosf/devcontainer & done ; wait)  ; echo "finished";
