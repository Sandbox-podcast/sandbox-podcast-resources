"""Local execution measurements, separate from monetary costs and audience results."""
from __future__ import annotations

from collections import defaultdict
from functools import wraps
import time
import uuid

from .contracts import iso, utcnow


def measured(stage):
    """Record direct CLI calls and worker calls, including failed/interrupted runs."""
    def decorate(function):
        @wraps(function)
        def run(store, config, episode_id, *args, **kwargs):
            identity = str(uuid.uuid4())
            record = {"run_id": identity, "episode_id": episode_id, "stage": stage,
                      "started_at": iso(utcnow()), "status": "running",
                      "elapsed_seconds": None, "python_cpu_seconds": None,
                      "energy_kwh": None, "monetary_cost": None}
            store.put("resource_run", identity, record, episode_id=episode_id)
            started, cpu_started = time.perf_counter(), time.process_time()
            try:
                result = function(store, config, episode_id, *args, **kwargs)
            except BaseException as error:
                record.update(status="failed", error_type=type(error).__name__)
                raise
            else:
                record.update(status="completed", execution_cache=result.get("execution_cache", {}))
                return result
            finally:
                record.update(finished_at=iso(utcnow()), elapsed_seconds=round(time.perf_counter()-started, 6),
                              python_cpu_seconds=round(time.process_time()-cpu_started, 6))
                store.put("resource_run", identity, record, episode_id=episode_id)
        return run
    return decorate


def summarize_runs(records):
    groups = defaultdict(list)
    for record in records:
        groups[record["stage"]].append(record)
    stages = []
    for stage, rows in sorted(groups.items()):
        durations = sorted(r["elapsed_seconds"] for r in rows if r.get("elapsed_seconds") is not None)
        cpu = [r["python_cpu_seconds"] for r in rows if r.get("python_cpu_seconds") is not None]
        caches = defaultdict(lambda: {"hits": 0, "misses": 0})
        for row in rows:
            for name, value in row.get("execution_cache", {}).items():
                if value in {"hit", "miss"}:
                    caches[name]["hits" if value == "hit" else "misses"] += 1
        stages.append({"stage": stage, "runs": len(rows),
                       "completed": sum(r["status"] == "completed" for r in rows),
                       "failed": sum(r["status"] == "failed" for r in rows),
                       "unfinished": sum(r["status"] == "running" for r in rows),
                       "elapsed_seconds": round(sum(durations), 6) if durations else None,
                       "maximum_elapsed_seconds": max(durations) if durations else None,
                       "python_cpu_seconds": round(sum(cpu), 6) if cpu else None,
                       "cache": dict(caches)})
    return {"stages": stages, "energy_kwh": None, "monetary_cost": None,
            "coverage": "process_and_render_calls_since_instrumentation",
            "limits": ["Le CPU mesuré couvre Python, pas FFmpeg ni les autres sous-processus.",
                       "La durée écoulée inclut les attentes ; elle ne mesure pas l'énergie consommée.",
                       "Les coûts financiers viennent des relevés de coûts, pas d'une estimation de durée."]}
