#!/usr/bin/env python3
import json,sys
from pathlib import Path
root=Path(__file__).parents[1]; status=json.loads((root/'data/status.json').read_text()); alerts=[]
if not status.get('ok'):alerts.append({'severity':'critical','code':'pipeline_not_ok','detail':status})
(root/'data/alerts.json').write_text(json.dumps({'active':alerts,'checked_at':status.get('fetched_at'),'count':len(alerts)},indent=2))
if alerts:raise SystemExit('active data alert')
