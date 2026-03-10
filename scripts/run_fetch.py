from __future__ import annotations

from ai_trends.data import run_pipeline


def main() -> None:
    articles = run_pipeline()
    print(f"Fetched and merged {len(articles)} articles.")


if __name__ == "__main__":
    main()

