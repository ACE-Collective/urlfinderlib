import logging
import sys

import urlfinderlib


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s.%(funcName)s +%(lineno)s: %(levelname)-8s %(message)s",
    )

    try:
        file_path = sys.argv[1]
    except IndexError:
        print("Usage: urlfinder /path/to/file")
        sys.exit(1)

    try:
        with open(file_path, "rb") as f:
            urls = sorted(list(urlfinderlib.find_urls(f.read())))
            for url in urls:
                print(url)
    except Exception:
        logging.exception("exception parsing %s", file_path)
        sys.exit(1)


if __name__ == "__main__":
    main()
