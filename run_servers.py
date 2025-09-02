"""
Nano-Temporal Server Runner

This script runs both the web server and temporal worker concurrently.

Usage:
    python run_servers.py [OPTIONS]

Options:
    -h, --host HOST     Host address to bind to (default: 127.0.0.1:8000)
    --help             Show this help message and exit

Examples:
    python run_servers.py
    python run_servers.py --host=0.0.0.0:8000
    python run_servers.py -h 192.168.1.100:3000
"""

import asyncio
import argparse
import uvicorn
from web import app
from run_worker import temporal_worker

interrupt_event = asyncio.Event()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run web server and temporal worker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_servers.py
    python run_servers.py --host=0.0.0.0:8080
        """,
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1:8000",
        help="Host address and port to bind to (default: 127.0.0.1:8000)",
    )
    return parser.parse_args()


async def web_server(host="127.0.0.1", port=8000):
    config = uvicorn.Config(app, host=host, port=port)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    args = parse_args()
    app._prepare()
    host, port = app._prestart(host=args.host)
    loop = asyncio.new_event_loop()
    try:
        loop.create_task(web_server(host=host, port=port))
        loop.create_task(temporal_worker())
        loop.run_forever()
    except KeyboardInterrupt:
        interrupt_event.set()
        loop.run_until_complete(loop.shutdown_asyncgens())
