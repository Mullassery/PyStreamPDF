"""PyStreamPDF CLI - Command-line interface"""

import sys
import argparse
from pystreampdf.cli_dashboard import PyStreamPDFDashboard


def dashboard_command(args):
    """Handle dashboard command"""
    try:
        dashboard = PyStreamPDFDashboard(config_path=args.config)
        if args.export:
            dashboard.export_json(args.export)
        elif args.alerts:
            dashboard.show_alerts()
        elif args.recommendations:
            dashboard.show_recommendations()
        else:
            dashboard.run_dashboard(interactive=not args.static)
    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="PyStreamPDF - Document Processing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  pystreampdf dashboard\n  pystreampdf dashboard --static\n  pystreampdf dashboard --export metrics.json"
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Dashboard subcommand
    dashboard_parser = subparsers.add_parser('dashboard', help='View processing dashboard')
    dashboard_parser.add_argument('--static', action='store_true', help='Show static snapshot')
    dashboard_parser.add_argument('--alerts', action='store_true', help='Show alerts only')
    dashboard_parser.add_argument('--recommendations', action='store_true', help='Show recommendations')
    dashboard_parser.add_argument('--export', metavar='FILE', help='Export to JSON')
    dashboard_parser.add_argument('--config', metavar='PATH', help='Config file path')
    dashboard_parser.set_defaults(func=dashboard_command)

    parser.add_argument('--version', action='version', version='PyStreamPDF 2.1.0')

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if hasattr(args, 'func'):
        args.func(args)


if __name__ == '__main__':
    main()
