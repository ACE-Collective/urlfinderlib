import argparse
import logging
import sys

import urlfinderlib


def main():
    parser = argparse.ArgumentParser(
        prog="urlfinder",
        description="Find URLs in files",
    )
    parser.add_argument("file", help="Path to the file to scan for URLs")
    parser.add_argument(
        "-b", "--base-url",
        default="",
        help="Base URL for resolving relative URLs (useful for HTML files)",
    )
    parser.add_argument(
        "-m", "--mimetype",
        default="",
        help="Override auto-detected mimetype",
    )
    parser.add_argument(
        "-d", "--domain-as-url",
        action="store_true",
        help="Treat standalone domains as URLs",
    )
    parser.add_argument(
        "-o", "--ocr-safe",
        action="store_true",
        help="Apply stricter domain validation for OCR text (reduces false positives when used with -d)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose/debug logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(name)s.%(funcName)s +%(lineno)s: %(levelname)-8s %(message)s",
        )

    try:
        with open(args.file, "rb") as f:
            urls = sorted(list(urlfinderlib.find_urls(
                f.read(),
                base_url=args.base_url,
                mimetype=args.mimetype,
                domain_as_url=args.domain_as_url,
                ocr_safe=args.ocr_safe,
            )))
            for url in urls:
                print(url)
    except Exception:
        logging.exception("exception parsing %s", args.file)
        sys.exit(1)


if __name__ == "__main__":
    main()
