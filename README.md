# pushing to remote server

Rebuild the image using the modified yml file: 
in `.offlinedev` or `.devcontainer`, run `docker-compose -f docker-compose-build*.yml build`
Export the docker image (and postgres if using):
- `docker save -o djangotile_v0.1.tar djtdb-1:latest`
- `docker save -o djangotile_v0.2.tar djtdb-dev:latest`
- `docker save -o djangotile_postgres_v0.2.tar postgres:latest`
- `docker save -o djtdb-remote-dev.tar djtdb-remote-dev:latest`

I made a script that automates the sending of the docker image tar in smaller chunks.
`bash split_transfer.sh <image_name>`

# on the remote server

- Load the image from tar:
 - `sudo docker load -i djangotile_v0.1.tar`
- From the remote .offlinedev folder, docker-compose the container. This will end in sleep infinity as specified by the yml:
 - `sudo docker-compose up -d`
 -(-d for detached)
- Note that because the directory for my dev files are the same as the prod files, namely .offlinedev, the resultant dev docker container would overwrite the prod one. The solution is to introduce a different project name:
 - [Docker compose up keep replace existing container - Stack Overflow] (https://stackoverflow.com/questions/48557607/docker-compose-up-keep-replace-existing-container)
 - `sudo docker-compose --project-name offlinedev-dev up -d`
- Find out the container’s ID and copy it:
 - `sudo docker ps`
- Make it execute a bash command. If you attempt to attach to it, you will be stuck in an infinity loop and have to close the connection.
 - `sudo docker exec -it 6e0f17a43b45 bash`
- Once inside the container, navigate to the django project and run the web server as normal:
 - `python manage.py runserver 0.0.0.0:8000 &`
 - (& ensured it runs in the background and won’t terminate when you leave the console)
- Test it out by pointing your browser to the IP address!

# Remote development using VSCode

I wanted to shorten the dev cycle instead of having to push the docker image each time I made a small change.

Install Remote -SSH Extension and Connect to SSH using choosf@192.168.145.25 and password. It will install VS Code Server on the linux remote machine.
I may then open any remote folder!
I need to revamp my docker-compose.yml to create on the remote server the container and use a bound folder on the remote. Then VSCode open that remote folder and dev from there.
Redid local yml file to use a modified dockerfile that does not copy the project files. Modified remote-executed yml file to bind mount the project files from `/home/choosf/devcontainer/djangotiledb_project`
Rebuilt the docker image, now named `djtdb-remote-dev` (note new -remote name): `C:\Users\choosf\Documents\pyprojects\alltiledbs\devcontainer\.offlinedev>docker-compose -f docker-compose-build-without-copy.yml build`
Export and scp the docker file to remote and load it.
Scp the project files and .offlinedev to remote:/home/choosf/devcontainer
In .offlinedev, run `docker-compose --project-name djtdb-remote-dev -f docker-compose-remote.yml up -d`
In VSCode, Ctrl-P + > then SSH into the remote host, then Attach to running container `djtdb-remote-dev_web_1`.
From there, terminal and runserver.
