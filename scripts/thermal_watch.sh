#!/bin/bash
# Watch a long job's thermal state and pause it when the machine is under thermal pressure (user's policy, 2026-11-03).
#   scripts/thermal_watch.sh JOB_PID LOGFILE THERMALSTATE_BINARY
# JOB_PID is the job's parent process; the pause signals it and its direct children by PID.
#
# Pause at once:   macOS thermal state serious or critical (2, 3).
# Pause if sustained: CPU_Speed_Limit below 90 for 2 min, or 90-99 for 5 min; any non-zero thermal warning for 2 min;
#                  GPU >= 90% for 10 min together with thermal state 1 or any throttling. GPU use alone never pauses.
# Logged only:     thermal state 1 (fair).
# Resume:          thermal state 0, speed limit 100 and no warning, all held for 5 min. No fixed waiting time.
# Sampled every minute, with a log line every 15 minutes and on every state change. Not read: die and ambient temperature
# (no unprivileged reading).
# Environment overrides for the test: SAMPLE, THERM_CMD, GPU_CMD.
PID=$1; LOG=$2; TS=$3
SAMPLE=${SAMPLE:-60}
THERM_CMD=${THERM_CMD:-"pmset -g therm"}
GPU_CMD=${GPU_CMD:-"ioreg -r -c IOAccelerator -d 1"}

resume() { kill -CONT "$PID" $(pgrep -P "$PID") 2>/dev/null; }
trap resume EXIT

read_state() {
  therm=$($THERM_CMD 2>/dev/null)
  state=$("$TS" 2>/dev/null); state=${state:-0}
  gpu=$($GPU_CMD 2>/dev/null | grep -oE '"Device Utilization %"=[0-9]+' | head -1 | grep -oE '[0-9]+$'); gpu=${gpu:-0}
  limit=$(echo "$therm" | sed -n 's/.*CPU_Speed_Limit[^0-9]*\([0-9]*\).*/\1/p' | head -1); limit=${limit:-100}
  warn=$(echo "$therm" | sed -n 's/.*[Tt]hermal [Ww]arning [Ll]evel[^0-9]*\([0-9][0-9]*\).*/\1/p' | head -1); warn=${warn:-0}
}
say() { echo "$(date '+%F %T') $1 state=$state speed_limit=$limit warning=$warn gpu=$gpu" >> "$LOG"; }

t_lim90=0; t_lim100=0; t_warn=0; t_gpu=0; n=0; last=""
while kill -0 "$PID" 2>/dev/null; do
  read_state
  [ "$limit" -lt 90 ] && t_lim90=$((t_lim90 + SAMPLE)) || t_lim90=0
  [ "$limit" -lt 100 ] && t_lim100=$((t_lim100 + SAMPLE)) || t_lim100=0
  [ "$warn" -gt 0 ] && t_warn=$((t_warn + SAMPLE)) || t_warn=0
  if [ "$gpu" -ge 90 ] && { [ "$state" -ge 1 ] || [ "$limit" -lt 100 ]; }; then t_gpu=$((t_gpu + SAMPLE)); else t_gpu=0; fi

  why=""
  [ "$state" -ge 2 ] && why="thermal state $state"
  [ "$t_lim90" -ge $((2 * SAMPLE)) ] && why="speed limit below 90 for 2 samples"
  [ "$t_lim100" -ge $((5 * SAMPLE)) ] && why="speed limit below 100 for 5 samples"
  [ "$t_warn" -ge $((2 * SAMPLE)) ] && why="thermal warning for 2 samples"
  [ "$t_gpu" -ge $((10 * SAMPLE)) ] && why="GPU at 90% or more with heat for 10 samples"

  now="$state/$limit/$warn"
  { [ "$now" != "$last" ] || [ $((n % 15)) -eq 0 ]; } && say "check"
  last=$now; n=$((n + 1))

  if [ -n "$why" ]; then
    say "PAUSE ($why)"
    kill -STOP "$PID" $(pgrep -P "$PID") 2>/dev/null
    ok=0
    while [ "$ok" -lt 5 ]; do
      sleep "$SAMPLE"
      read_state
      if [ "$state" -eq 0 ] && [ "$limit" -eq 100 ] && [ "$warn" -eq 0 ]; then ok=$((ok + 1)); else ok=0; fi
    done
    resume
    say "RESUME"
    t_lim90=0; t_lim100=0; t_warn=0; t_gpu=0
    continue
  fi
  sleep "$SAMPLE"
done
say "job ended; watcher exiting"
