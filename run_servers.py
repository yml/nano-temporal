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
import sys
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
    asyncio.set_event_loop(loop)
    
    tasks = []
    try:
        tasks.append(loop.create_task(web_server(host=host, port=port)))
        tasks.append(loop.create_task(temporal_worker()))
        loop.run_forever()
    except KeyboardInterrupt:
        print("Interrupted. Shutting down...")
        interrupt_event.set()
        
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        
        # Wait for all tasks to be cancelled
        try:
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        except asyncio.CancelledError as e:
            print(f"asyncio.CancelledError: {e}")
        
        # Clean shutdown
        loop.run_until_complete(loop.shutdown_asyncgens())
        sys.exit(0)
