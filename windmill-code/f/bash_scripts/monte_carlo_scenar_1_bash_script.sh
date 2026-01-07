# shellcheck shell=bash
# arguments of the form X="$I" are parsed as parameters X of type string
scheduling_interval="${1:-300}"
workflow_number="${2:-1}"
last_result="${3:-None}"
task="${4:-1}"

if [[ -n $last_result && $last_result != "None" ]]; then
  end_time=$(jq -r '.end_ts// empty' <<< $last_result)
  echo "end_time value $end_time retrived from the last result..."
  python3 /app/src/scripts/monte_carlo.py -st $end_time -wf $workflow_number -t $task
else
  python3 /app/src/scripts/monte_carlo.py -si $scheduling_interval -wf $workflow_number
fi

