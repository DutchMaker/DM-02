#!/usr/bin/env python3
"""Read-only localhost dashboard, with live source/evidence freshness checks."""
import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from dm02.common import VROOT, BUILD, digest
from dm02.reporting import freshness


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        super().end_headers()

    def do_GET(self):
        route=urlsplit(self.path).path
        if route=='/api/state':
            try:
                report=json.loads((BUILD/'report.json').read_text())
                state=freshness(report)
                state['altered_evidence']=[p for p,h in report.get('artifact_hashes',{}).items()
                    if not (BUILD/p).is_file() or digest(BUILD/p)!=h]
                state['fresh'] &= not bool(state['altered_evidence'])
                data=json.dumps(dict(report=report,freshness=state)).encode()
                self.send_response(200)
            except FileNotFoundError:
                data=json.dumps(dict(error='No report yet. Run python3 Verification/run.py')).encode()
                self.send_response(404)
            self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(data)
        else:
            if route=='/': self.path='/dashboard/index.html'
            super().do_GET()


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8020)
    args=parser.parse_args()
    print(f'DM-02 verification dashboard: http://127.0.0.1:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(VROOT))).serve_forever()
