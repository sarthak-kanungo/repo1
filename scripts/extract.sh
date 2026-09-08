#!/usr/bin/env bash
# Extract HRS_SPARES relational metadata with sqlcmd into TSV files.
#
#   export SQLCMDPASSWORD='...'      # never hardcode / commit the password
#   ./scripts/extract.sh                    # uses the defaults below
#   ./scripts/extract.sh -S host,1433 -d DB -U user -o out
#
# Produces: <outdir>/tables.tsv, <outdir>/columns.tsv, <outdir>/foreign_keys.tsv
set -euo pipefail

SERVER="192.168.17.1,1433"
DATABASE="HRS_SPARES"
DBUSER="admin"
OUTDIR="extract"

while getopts "S:d:U:o:h" opt; do
  case "$opt" in
    S) SERVER="$OPTARG"   ;;
    d) DATABASE="$OPTARG" ;;
    U) DBUSER="$OPTARG"   ;;
    o) OUTDIR="$OPTARG"   ;;
    h) sed -n '2,9p' "$0"; exit 0 ;;
    *) exit 2 ;;
  esac
done

if [[ -z "${SQLCMDPASSWORD:-}" ]]; then
  echo "ERROR: export SQLCMDPASSWORD first, e.g.  export SQLCMDPASSWORD='...'" >&2
  exit 1
fi

command -v sqlcmd >/dev/null 2>&1 || {
  echo "ERROR: sqlcmd not on PATH. Install mssql-tools18 (Linux) or SQL Server command line utilities (Windows)." >&2
  exit 1
}

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$OUTDIR"

# -h -1   no column headers        -W    strip trailing blanks
# -s TAB  tab separated            -w    wide rows, no wrapping
# -C      trust server certificate (needed by sqlcmd 18+ against a self-signed cert)
# -Y/-y 0 do not truncate character columns
run_query() {
  local sql_file="$1" out_file="$2"
  echo ">> $(basename "$sql_file") -> $out_file"
  sqlcmd -S "$SERVER" -d "$DATABASE" -U "$DBUSER" \
         -C -l 30 -h -1 -W -s $'\t' -w 65535 -y 0 -Y 0 \
         -i "$sql_file" -o "$out_file"
  # sqlcmd writes errors into -o; fail loudly instead of generating an empty diagram
  if grep -qE '^(Msg [0-9]+|Sqlcmd:|HResult)' "$out_file"; then
    echo "ERROR: sqlcmd reported a problem:" >&2
    sed -n '1,20p' "$out_file" >&2
    exit 1
  fi
}

run_query "$HERE/sql/01_tables.sql"             "$OUTDIR/tables.tsv"
run_query "$HERE/sql/02_relational_columns.sql" "$OUTDIR/columns.tsv"
run_query "$HERE/sql/03_foreign_keys.sql"       "$OUTDIR/foreign_keys.tsv"

echo
echo "tables:       $(grep -cve '^\s*$' "$OUTDIR/tables.tsv")"
echo "rel. columns: $(grep -cve '^\s*$' "$OUTDIR/columns.tsv")"
echo "fk col pairs: $(grep -cve '^\s*$' "$OUTDIR/foreign_keys.tsv")"
echo
echo "Next:  python3 scripts/build_drawio.py --input $OUTDIR --output HRS_SPARES.drawio"
