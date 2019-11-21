#!/bin/sh

CONF_DIR=tools/conf

DOTENV=.env
SECRETS=.secrets.yaml
SETTINGS=settings.yaml

DOTENV_DIST=$CONF_DIR/env.dist
SECRETS_DIST=$CONF_DIR/secrets.yaml.dist
SETTINGS_DIST=$CONF_DIR/settings.yaml.dist

cp -n "$DOTENV_DIST" "$DOTENV"
cp -n "$SETTINGS_DIST" "$SETTINGS"
[ ! -e "$SECRETS" ] && \
    SECRET_KEY=`tr -dc 'a-zA-Z0-9!@#$%^&*(_=+)-' < /dev/urandom | head -c50` \
    envsubst < "$SECRETS_DIST" > "$SECRETS"

exit 0
