#!/usr/bin/env python3

'''Standalone server for obfs4proxy and other pluggable transports.

This script takes a pluggable transport binary and run it as a standalone
server, accepting obfuscated traffic, decodes it and forwards plaintext
traffic.'''

import logging
import argparse
import configparser
import signal, sys

from pluggabletransportadapter import PluggableTransportServerAdapter

def main_cli():
    # Argument Parsing
    parser = argparse.ArgumentParser(description="Run a Tor pluggable "
              "transport as standalone server.")
    
    parser.add_argument("configfile", type=argparse.FileType("r"), help=
            "Configuration file. See the example config file for details.")
    parser.add_argument("--verbose", "-v", action="count", help="Increase " 
        "verbosity level. Specify once to see logging.INFO, twice to see "
        "logging.DEBUG.")
    
    args = parser.parse_args()
    
    # Logging
    logger = logging.getLogger("")
    logger.setLevel(logging.DEBUG)
    
    logconsole = logging.StreamHandler()
    logconsoleformatter = logging.Formatter('[%(asctime)s] %(name)-6s '
            '%(levelname)-8s %(message)s')
    logconsole.setFormatter(logconsoleformatter)
    if args.verbose is None:
        logconsole.setLevel(logging.WARNING)
    elif args.verbose == 1:
        logconsole.setLevel(logging.INFO)
    else:
        logconsole.setLevel(logging.DEBUG)

    logger.addHandler(logconsole)
    
    logger.debug("Verbosity level set")
    logger.debug("Arguments:")
    logger.debug(args)
    
    # Read config file
    config = configparser.ConfigParser(empty_lines_in_values=False)
    config.read_file(args.configfile)
    args.configfile.close()
    
    logger.info("Read config file")
    
    ptexec = config["common"]["exec"]
    statedir = config["common"]["statedir"]
    orport = config["common"]["forward"]
    
    # Build server config
    transports = {}
    for t, b in config.items("transports"):
        transports[t] = {"bindaddr": b}
        if config.has_section(t + "-options"):
            transports[t]["options"] = dict(config.items(t + "-options"))
    
    logger.debug("Transports:")
    logger.debug(transports)
    
    # Start PT executable
    server = PluggableTransportServerAdapter(ptexec, statedir, orport, transports)
    server.start()
    logger.debug("Available transports:")
    logger.debug(server.transports)
    
    # Wait until PT terminates, or terminate on Ctrl+C / SIGTERM
    try:
        signal.signal(signal.SIGTERM, sigterm_handler)
        server.wait()
    except (KeyboardInterrupt, SystemExit) as e:
        logger.info("Received {}".format(repr(e)))
    finally:
        logger.info("Terminating")
        server.terminate()
    
def sigterm_handler(signal, frame):
    sys.exit(0)

if __name__ == "__main__":
    main_cli()
