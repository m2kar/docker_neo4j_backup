#! python3
"""
docker_neo4j_backup.py 
backup and restore neo4j database
usage:
    docker_neo4j_backup.py backup container_name backup_dir
    docker_neo4j_backup.py restore container_name backup_file_path 

Create Time: Oct. 20, 2020
Author: zhiqing <zhiqing.rui@gmail.com>
"""
import logging
import random
import datetime
import docker
import argparse
import sys
import os

HELP = """
docker_neo4j_backup.py 
Usage:
    docker_neo4j_backup.py backup container_name backup_dir [-f] [--debug]
    docker_neo4j_backup.py restore container_name backup_file_path [-f] [--debug]

Args:
    -f : force stop container or delete old data without prompt
    --debug : debug mode, print more details

"""
# %%

# %%
docker_client = docker.from_env()


def container(container_name):
    return docker_client.containers.get(container_name)


def backup(container_name, backup_dir, force=False):
    backup_dir = os.path.realpath(backup_dir)
    print(f"[~] backup {container_name} to {backup_dir}")
    # get data volume id
    for volume in container(container_name).attrs["Mounts"]:
        if volume["Destination"] == "/data":
            source = volume["Source"]
            break
    else:
        raise ValueError("Not found /data volume")
    running = (container(container_name).status == "running")
    if running:
        if not force:
            s = input(
                f"container {container_name} will be stopped, continue? Y/N")
            if not s.strip().upper()[0] == "Y":
                os.exit()
        container(container_name).stop()
    image = container(container_name).image.tags[0]

    # backup
    date_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_file = f"{container_name}_{date_str}.dump"

    # docker run -it --rm -v ~min/vulgraphDB_data:/data -v ~min/vulgraphDB_backup:/backup
    # --name vulgraphDB_backup vulgraphdb:20200707 neo4j-admin dump --database=graph.db --to="/backup/vulgraph_$(date).dump"

    backup_container = docker_client.containers.run(
        image=image,
        # command="bash",
        command=f'sleep inf',
        volumes={
            source: {'bind': '/data', 'mode': 'rw'},
            backup_dir: {'bind': '/backup', 'mode': 'rw'}
        },
        name=f"neo4j_backup_{container_name}_{date_str}",
        user="root",
        detach=True,
        # tty=True,
        # stdin_open=True,
        # stdout=True,
        # stderr=True,
        remove=True,
    )
    backup_container.exec_run(
        cmd=f'neo4j-admin dump --database=graph.db --to="/backup/{backup_file}"',
        stdout=True,
        stderr=True,
    )
    print("[+] backup done")
    print(f"[+] backup file: {backup_file}")
    backup_container.stop()
    if running:
        container(container_name).start()
    return backup_file


def restore(container_name, backup_file_path, force=False):
    if os.getenv("DEBUG"):
        DEBUG = True

    print(f"[~] restore to {container_name} "
          f"from {os.path.realpath(backup_file_path)}")
    backup_dir, backup_file = os.path.split(os.path.realpath(backup_file_path))

    if not force:
        s = input(f"container {container_name} will be stopped, \n"
                  " and the data will be removed !!! \n"
                  " and the data will be removed !!! \n"
                  " and the data will be removed !!! \n"
                  " continue? Y/N")
        if not s.strip().upper()[0] == "Y":
            os.exit()

    # get data volume id
    for volume in container(container_name).attrs["Mounts"]:
        if volume["Destination"] == "/data":
            # source destination
            source = volume["Source"]
            logging.debug(f"destination volume: {source}")
            break
    else:
        raise ValueError("Not found /data volume")
    running = (container(container_name).status == "running")
    if running:
        container(container_name).stop()
    image = container(container_name).image.tags[0]

    date_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    if DEBUG:
        remove = False
    else:
        remove = True
    restore_container = docker_client.containers.run(
        image=image,
        # command="bash",
        command=f'sleep inf',
        volumes={
            source: {'bind': '/data', 'mode': 'rw'},
            backup_dir: {'bind': '/backup', 'mode': 'rw'}
        },
        name=f"neo4j_restore_{container_name}_{backup_file}_{date_str}",
        # user="root",
        detach=True,
        # tty=True,
        # stdin_open=True,
        # stdout=True,
        # stderr=True,
        remove=remove,
    )
    logging.debug(f"restore container name: {restore_container.name}")

    restore_container.exec_run(
        cmd=f'rm -rf /data/databases/graph.db',
        user="root",
        stdout=True,
        stderr=True,
    )

    restore_container.exec_run(
        cmd=f'neo4j-admin load --database=graph.db --from="/backup/{backup_file}"',
        user="root",
        stdout=True,
        stderr=True,
    )
    logging.debug("restore success")

    restore_container.exec_run(
        cmd=f'chown -R neo4j:neo4j /data/databases/graph.db && chmod -R u=rw,g=r,o=r /data/databases/graph.db',
        user="root",
        stdout=True,
        stderr=True,
    )
    logging.debug("change file privilege succuss ")
    date_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    logstr = f"{date_str}:restore to {container_name} from {os.path.realpath(backup_file_path)} \n"
    restore_container.exec_run(
        cmd=f'echo "{logstr}" >> /data/restore.log',
        user="root",
        stdout=True,
        stderr=True,
    )
    print("[+] restore done")
    # print(f"[+] backup file: {backup_file}")
    restore_container.stop()
    if running:
        container(container_name).start()
    return


if __name__ == "__main__":
    for arg in sys.argv:
        if arg.lower() == "--debug":
            logging.basicConfig(level=logging.DEBUG)
            os.environ["DEBUG"] = "1"
            DEBUG = True
            sys.argv.remove(arg)
            break
    else:
        DEBUG = False

    force = "-f" in sys.argv
    if sys.argv[1] == "backup":
        backup(sys.argv[2], sys.argv[3], force=force)
    elif sys.argv[1] == "restore":
        restore(sys.argv[2], sys.argv[3], force=force)
    else:
        print(HELP)
#    restore()


# %%
