"""Entry point for running the backend server."""

import sys

import uvicorn

from backend.main import app

if __name__ == "__main__":
    # Get port from command line or default to 8000
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)

    uvicorn.run(app, host="0.0.0.0", port=port)
