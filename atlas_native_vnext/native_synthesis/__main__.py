"""Public-only offline CLI. No model/API calls, no content imports."""
import argparse
import json
import sys
from pathlib import Path
from .engine import NativeSynthesis
from .responses import function_tools, handle_function_call
from .inventory import triage_public_inventory

def main():
    p=argparse.ArgumentParser(description='Atlas Native Synthesis (offline only)')
    p.add_argument('command',choices=['status','catalog','inventory','experiment','fusion','response-tools','response-call'])
    p.add_argument('--family',default='all')
    args=p.parse_args()
    e=NativeSynthesis()
    if args.command=='status': output=e.readiness()
    elif args.command=='catalog': output=e.catalog.list(args.family)
    elif args.command=='response-tools': output=function_tools()
    else:
        raw=sys.stdin.read()
        if args.command=='inventory':output=triage_public_inventory(raw)
        elif args.command=='experiment':output=e.prepare_experiment(raw)
        elif args.command=='fusion':output=e.propose_fusion(raw)
        else:
            try: output=handle_function_call(json.loads(raw),e)
            except (ValueError,TypeError):output={'status':'HOLD'}
    print(json.dumps(output,indent=2,ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()
