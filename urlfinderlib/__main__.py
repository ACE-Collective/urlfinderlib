import argparse
import logging
import sys

import urlfinderlib


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s.%(funcName)s +%(lineno)s: %(levelname)-8s %(message)s",
    )

    parser = argparse.ArgumentParser(description="Find URLs in a file")
    parser.add_argument("file", help="path to the file to scan")
    parser.add_argument(
        "--domain-as-url",
        action="store_true",
        default=False,
        help="treat domains as URLs",
    )
    args = parser.parse_args()

    try:
        with open(args.file, "rb") as f:
            urls = sorted(list(urlfinderlib.find_urls(f.read(), domain_as_url=args.domain_as_url)))
            for url in urls:
                print(url)
    except Exception:
        logging.exception("exception parsing %s", args.file)
        sys.exit(1)


if __name__ == "__main__":
    main()
