# Pixiv Auto Downloader

Pixiv Auto Downloader is a tool I wrote in Python to **remind** and **download** works of my favorite artists from `pixiv`.

## How to use

If you already know how to build a `docker` image and to typically run a container with `docker-compose`, then it could be significantly easy to deploy such an ordinary service.

For example, you can build your own docker image with following commands

```bash
git clone https://github.com/NobeKanai/pixiv-auto-downloader.git pad
# git clone -b task-mode https://github.com/NobeKanai/pixiv-auto-downloader.git pad
cd pad
docker build -t pad .
```

Perfer any path to copy `docker-compose.yml` to. Almost all configuration options are easy to understand and contain necessary annotations.

Just run `docker-compose up -d` to start a service which gonna run forever unless you shutdown it if you build image with `main` branch. You may perfer to run with `task-mode`, which will perform only one task any time it starts, so to configure with some tools like `crontab` would be helpful.

