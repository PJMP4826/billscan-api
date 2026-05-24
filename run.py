import uvicorn
from main import app  # type: ignore


def run_app():
    host = "0.0.0.0"
    port = 8000

    reload = True

    try:
        print("Server started successfully...")
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            workers=1,
            use_colors=False,
            log_config=None,
        )
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")


if __name__ == "__main__":
    run_app()
