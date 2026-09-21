"""
Standalone Fake Redis TCP service runner for adversarial and distributed tests.
Spins up fakeredis.TcpFakeServer on loopback interface and prints READY to stdout.
"""

from __future__ import annotations

import argparse
import sys
import fakeredis


def main() -> int:
    parser = argparse.ArgumentParser(description="Test Fake Redis TCP Service")
    parser.add_argument("--port", type=int, required=True, help="Port to bind fake Redis server to")
    args = parser.parse_args()

    server = fakeredis.TcpFakeServer(("127.0.0.1", args.port))
    sys.stdout.write(f"READY {args.port}\n")
    sys.stdout.flush()

    try:
        server.serve_forever()
    except Exception:
        pass
    finally:
        try:
            server.server_close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
