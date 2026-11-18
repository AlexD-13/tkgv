#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
RUNTIME_DIR="$ROOT_DIR/.runtime"
BACKEND_LOG="$RUNTIME_DIR/backend.log"
FRONTEND_LOG="$RUNTIME_DIR/frontend.log"
BACKEND_PID="$RUNTIME_DIR/backend.pid"
FRONTEND_PID="$RUNTIME_DIR/frontend.pid"

mkdir -p "$RUNTIME_DIR"

stop_project() {
  echo "Deteniendo servicios anteriores..."

  for pid_file in "$BACKEND_PID" "$FRONTEND_PID"; do
    if [[ -f "$pid_file" ]]; then
      pid="$(cat "$pid_file" 2>/dev/null || true)"
      if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
      fi
      rm -f "$pid_file"
    fi
  done

  pkill -TERM -f '[u]vicorn main:app.*--port 8000' 2>/dev/null || true
  pkill -TERM -f '[n]uxt dev.*--port 3000' 2>/dev/null || true
  sleep 1
  pkill -KILL -f '[u]vicorn main:app.*--port 8000' 2>/dev/null || true
  pkill -KILL -f '[n]uxt dev.*--port 3000' 2>/dev/null || true

  sleep 1

  echo "Servicios detenidos."
}

status_project() {
  backend="off"
  frontend="off"

  if [[ -f "$BACKEND_PID" ]] && kill -0 "$(cat "$BACKEND_PID")" 2>/dev/null; then backend="on"; fi
  if [[ -f "$FRONTEND_PID" ]] && kill -0 "$(cat "$FRONTEND_PID")" 2>/dev/null; then frontend="on"; fi

  echo "Backend:  $backend (http://localhost:8000)"
  echo "Frontend: $frontend (http://localhost:3000)"
}

start_project() {
  if [[ ! -f "$ROOT_DIR/.env" ]]; then
    echo "Error: falta $ROOT_DIR/.env" >&2
    exit 1
  fi

  echo "Instalando/actualizando dependencias..."
  cd "$BACKEND_DIR"
  uv sync

  echo "Aplicando migraciones..."
  if ! uv run alembic upgrade head 2>&1 | tee -a "$BACKEND_LOG"; then
    echo "Error: la migración de PostgreSQL falló. Revisa DATABASE_URL y las credenciales." >&2
    exit 1
  fi

  cd "$BACKEND_DIR"
  nohup uv run uvicorn main:app --host 0.0.0.0 --port 8000 \
    >>"$BACKEND_LOG" 2>&1 &
  echo $! >"$BACKEND_PID"

  cd "$FRONTEND_DIR"
  nohup bun run dev --host 0.0.0.0 --port 3000 \
    >>"$FRONTEND_LOG" 2>&1 &
  echo $! >"$FRONTEND_PID"

  echo "Esperando disponibilidad de los servicios..."
  backend_ready=false
  frontend_ready=false

  for _ in {1..40}; do
    if curl -fsS http://localhost:8000/status >/dev/null 2>&1; then backend_ready=true; fi
    if curl -fsS http://localhost:3000/ >/dev/null 2>&1; then frontend_ready=true; fi
    if [[ "$backend_ready" == true && "$frontend_ready" == true ]]; then break; fi
    sleep 0.25
  done

  status_project

  if [[ "$backend_ready" == true ]]; then
    echo "API:       http://localhost:8000/docs"
  else
    echo "Advertencia: el backend no respondió. Revisa $BACKEND_LOG" >&2
  fi

  if [[ "$frontend_ready" == true ]]; then
    echo "App:       http://localhost:3000/"
    echo "Admin:     http://localhost:3000/admin"
  else
    echo "Advertencia: el frontend no respondió. Revisa $FRONTEND_LOG" >&2
  fi
}

case "${1:-restart}" in
  start)
    start_project
    ;;
  stop)
    stop_project
    ;;
  restart)
    stop_project
    start_project
    ;;
  status)
    status_project
    ;;
  *)
    echo "Uso: $0 {start|stop|restart|status}" >&2
    exit 2
    ;;
esac
