"""A fake OpenAI-compatible chat endpoint for the pi tests (tests/test_pi_role.py): each request answers with the next
tool call of the script in argv[2] (a JSON list of [tool name, arguments]), counted by the tool results the request
already holds, then with a plain "done". Port in argv[1]; every request's tool results are appended to argv[3] as JSON
lines. No model is called."""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

port, script, log = int(sys.argv[1]), json.load(open(sys.argv[2], encoding="utf-8")), sys.argv[3]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        results = [m for m in body.get("messages", []) if m.get("role") == "tool"]
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"results": [str(m.get("content")) for m in results], "body": json.dumps(body)}) + "\n")
        n = len(results)
        if n < len(script):
            name, args = script[n]
            delta = {"role": "assistant", "tool_calls": [{"index": 0, "id": f"call{n}", "type": "function",
                                                           "function": {"name": name, "arguments": json.dumps(args)}}]}
            finish = "tool_calls"
        else:
            delta, finish = {"role": "assistant", "content": "done"}, "stop"
        chunks = [{"id": "x", "object": "chat.completion.chunk", "model": "fake-chat",
                   "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
                  {"id": "x", "object": "chat.completion.chunk", "model": "fake-chat",
                   "choices": [{"index": 0, "delta": {}, "finish_reason": finish}],
                   "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}]
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for c in chunks:
            self.wfile.write(f"data: {json.dumps(c)}\n\n".encode())
        self.wfile.write(b"data: [DONE]\n\n")


ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
