FROM nextcloud:30-apache

ENV NEXTCLOUD_ADMIN_USER admin
ENV NEXTCLOUD_ADMIN_PASSWORD password
ENV SQLITE_DATABASE nextcloud

RUN apt-get update -y && apt-get install -y sqlite3
COPY ./setup-nextcloud-music.sh /docker-entrypoint-hooks.d/post-installation/
COPY ./musics /var/sample-musics
