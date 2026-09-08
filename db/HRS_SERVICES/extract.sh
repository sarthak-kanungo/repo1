#!/usr/bin/env bash
# Pull the relational schema out of HRS_SERVICES and build the draw.io diagram.
#
#   export HRS_PASSWORD='...'         # keep the password out of the repo & shell history
#   ./extract.sh
#
# Override any of these via the environment:
#   HRS_SERVER   default 192.168.17.1,1433
#   HRS_DB       default HRS_SERVICES
#   HRS_USER     default admin
#   HRS_OUT      default HRS_SERVICES.drawio
set -euo pipefail

cd "$(dirname "$0")"

SERVER=${HRS_SERVER:-192.168.17.1,1433}
DB=${HRS_DB:-HRS_SERVICES}
USER=${HRS_USER:-admin}
OUT=${HRS_OUT:-HRS_SERVICES.drawio}
DUMP=${HRS_DUMP:-schema.txt}

if [[ -z ${HRS_PASSWORD:-} ]]; then
  read -r -s -p "Password for ${USER}@${SERVER}: " HRS_PASSWORD
  echo
fi

# -h -1  no headers      -W  trim padding      -w  don't wrap long lines
# -C     trust the server certificate (sqlcmd 18+ encrypts by default)
sqlcmd -S "$SERVER" -d "$DB" -U "$USER" -P "$HRS_PASSWORD" \
       -C -b -h -1 -W -w 65535 \
       -i extract_schema.sql -o "$DUMP"

python3 gen_drawio.py "$DUMP" -o "$OUT"
echo "wrote $OUT — open it at https://app.diagrams.net or in the VS Code Draw.io extension"
