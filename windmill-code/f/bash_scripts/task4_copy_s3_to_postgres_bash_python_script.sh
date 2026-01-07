# shellcheck shell=bash
# arguments of the form X="$I" are parsed as parameters X of type string

# the last line of the stdout is the return value
# unless you write json to './result.json' or a string to './result.out'

scheduling_interval="${1:-300}"
workflow_number="${2:-1}"
last_result="${3:-None}"

echo "Bash script started - task 4"


if [[ -n $last_result && $last_result != "None" ]]; then
  end_time=$(jq -r '.end_ts// empty' <<< $last_result)
  echo "end_time value $end_time retrived from the last result..."
  python3 /app/src/scripts/task4_copy_s3_to_postgres.py -st $end_time -wf $workflow_number
else
  python3 /app/src/scripts/task4_copy_s3_to_postgres.py -si $scheduling_interval -wf $workflow_number
fi

