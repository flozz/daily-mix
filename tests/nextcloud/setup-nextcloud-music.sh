#!/bin/bash

# Install Nextcloud Music app
php /var/www/html/occ app:install music

# Add a test user for Nextcloud Music Ampache & Subsonic APIs (admin:password)
sqlite3 /var/www/html/data/nextcloud.db "\
    INSERT INTO oc_music_ampache_users ( \
        user_id, \
        description, \
        hash \
    ) \
    VALUES ( \
        'admin', \
        'APIs Test (admin:password)', \
        '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8' \
    );"

# Copy musics to the Nextcloud files of the "admin" user and fix permissions
cp -r /var/sample-musics /var/www/html/data/admin/files/musics
chown -R www-data:www-data /var/www/html/data/admin/files/musics

# Trigger file scan (allow Nextcloud to find the new files)
php /var/www/html/occ files:scan --verbose --path /admin/files/musics

# Trigger music scan (allow Nextcloud Music to index new musics)
php /var/www/html/occ music:scan --verbose admin
