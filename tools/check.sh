#!/bin/sh

FLAKE8="flake8 vino"
MYPY="mypy --show-error-codes vino"

GREEN='\033[0;32m'
NC='\033[0m'

echo "∙ $FLAKE8"
$FLAKE8 && echo "${GREEN}OK!${NC}"
echo

echo "∙ $MYPY"
$MYPY && echo "${GREEN}OK!${NC}" || exit 1
echo
