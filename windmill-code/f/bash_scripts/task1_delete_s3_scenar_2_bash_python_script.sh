# shellcheck shell=bash
# arguments of the form X="$I" are parsed as parameters X of type string

# the last line of the stdout is the return value
# unless you write json to './result.json' or a string to './result.out'

scheduling_interval="${1:-300}"
workflow_number="${2:-1}"

echo "Bash script started - task 1"

python3 /app/src/scripts/task1_delete_s3_and_tables.py -si $scheduling_interval -wf $workflow_number

