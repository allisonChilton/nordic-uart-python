import argparse
import logging

_parser = argparse.ArgumentParser(description="Nordic UART CLI")


def main(args=None):
    args = _parser.parse_args(args=args)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)