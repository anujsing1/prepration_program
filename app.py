#!/usr/bin/env python3
"""Morning Trading Agent application entry point."""

from morning_trading_agent.infrastructure.http.ssl_setup import configure_ssl_certificates

configure_ssl_certificates()

from morning_trading_agent.presentation.cli.run_morning_job import main

if __name__ == "__main__":
    main()
