from app import init_app

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run with different configuration file."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Default config file path (default: ../config.yaml)"
    )
    args = parser.parse_args()

    app = init_app(args.config)
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)
