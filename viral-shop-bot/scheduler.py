"""Agenda local para 3 entregas diárias. Horários brasileiros em America/Sao_Paulo."""
import json
import os
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

TZ = ZoneInfo(os.getenv("TZ", "America/Sao_Paulo"))
HOURS = [int(h) for h in os.getenv("SCHEDULE_HOURS", "8,13,19").split(",")]
if not HOURS or len(set(HOURS)) != len(HOURS) or any(h < 0 or h > 23 for h in HOURS):
    raise ValueError("SCHEDULE_HOURS inválido: use horas únicas entre 0 e 23")
HOURS.sort()
MARKER = Path(os.getenv("SCHEDULE_STATE", "/app/output/schedule.json"))


def run_pending(now):
    state = json.loads(MARKER.read_text()) if MARKER.exists() else {}
    today = now.date().isoformat()
    if state.get("date") != today:
        state = {"date": today, "completed_slots": []}
    due = [hour for hour in HOURS if hour <= now.hour and hour not in state["completed_slots"]]
    if not due:
        return
    # Se o serviço iniciou tarde, não dispare lotes antigos em sequência.
    hour = max(due)
    state["completed_slots"].extend(due)
    if hour in due:
        # Marca antes de executar para impedir execução duplicada após reinício.
        state["completed_slots"].append(hour)
        MARKER.parent.mkdir(parents=True, exist_ok=True)
        tmp = MARKER.with_suffix(".tmp")
        tmp.write_text(json.dumps(state))
        tmp.replace(MARKER)
        print(f"Executando lote diário: {today}, horário {hour}:00", flush=True)
        result = subprocess.run([sys.executable, "/app/main.py"], env={**os.environ, "MAX_PRODUCTS": "1"}, check=False)
        print(f"Finalizado com código {result.returncode}", flush=True)


if __name__ == "__main__":
    while True:
        run_pending(datetime.now(TZ))
        time.sleep(60)
