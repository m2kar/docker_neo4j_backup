# 备份还原neo4j docker中的数据库

## 依赖

```bash
# python==3
pip3 install docker=4.3.1
```

## 使用方法

```raw
docker_neo4j_backup.py
Usage:
    docker_neo4j_backup.py backup container_name backup_dir [-f] [--debug]
    docker_neo4j_backup.py restore container_name backup_file_path [-f] [--debug]

Args:
    -f : force stop container or delete old data without prompt.
    --debug : debug mode, print more details.
```

**注意：还原时会将原docker中的数据清除.**


### 示例

#### 备份

```bash
$ python3 docker_neo4j_backup.py backup neo4j_test /tmp/backuptest/ 
[~] backup neo4j_test to /tmp/backuptest
[+] backup done
[+] backup file: neo4j_test_20201020-171900.dump

```

#### 还原

```bash
$ python3 docker_neo4j_backup.py restore neo4j_test /tmp/backuptest/neo4j_test_20201020-155312.dump 
restore to neo4j_test from /tmp/backuptest/neo4j_test_20201020-155312.dump
container neo4j_test will be stopped, 
 and the data will be removed !!! 
 and the data will be removed !!! 
 and the data will be removed !!! 
 continue? Y/Ny
[+] restore done
```
## 定时备份

```bash
0 3 * * 7 python3 docker_neo4j_backup.py backup <container_name> <backup_dir> -f
```

> 注意python3应该替换为合适的解释器
