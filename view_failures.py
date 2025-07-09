#!/usr/bin/env python3
"""
Utility script to view and manage failed conversions.
Usage: python view_failures.py [command] [options]
"""

import sys
import argparse
from failed_conversions import FailedConversionsTracker

def main():
    parser = argparse.ArgumentParser(description='View and manage failed conversions')
    parser.add_argument('command', choices=['summary', 'list', 'export', 'clear'], 
                       help='Command to execute')
    parser.add_argument('--hours', type=int, default=24, 
                       help='Hours to look back for recent failures (default: 24)')
    parser.add_argument('--days', type=int, default=30, 
                       help='Days to keep when clearing old records (default: 30)')
    parser.add_argument('--output', type=str, 
                       help='Output file for export command')
    parser.add_argument('--error-type', type=str, 
                       help='Filter by error type')
    parser.add_argument('--filename', type=str, 
                       help='Filter by filename')
    
    args = parser.parse_args()
    
    tracker = FailedConversionsTracker()
    
    if args.command == 'summary':
        show_summary(tracker)
    elif args.command == 'list':
        show_list(tracker, args.hours, args.error_type, args.filename)
    elif args.command == 'export':
        export_failures(tracker, args.output, args.error_type, args.filename)
    elif args.command == 'clear':
        clear_old_records(tracker, args.days)

def show_summary(tracker):
    """Display a summary of failed conversions."""
    summary = tracker.get_failure_summary()
    
    print("=== FAILED CONVERSIONS SUMMARY ===")
    print(f"Total failures: {summary['total_failures']}")
    print(f"Unique files with failures: {summary['unique_files']}")
    print(f"Failures in last 24h: {summary['recent_failures_24h']}")
    
    if summary['error_types']:
        print("\nError types breakdown:")
        for error_type, count in summary['error_types'].items():
            print(f"  {error_type}: {count}")
    
    if summary['total_failures'] == 0:
        print("\n[OK] No failed conversions recorded")
    else:
        print(f"\nDetailed records available in: failed_conversions.csv")

def show_list(tracker, hours, error_type, filename):
    """List failed conversions with optional filters."""
    if hours > 0:
        failures = tracker.get_recent_failures(hours)
        print(f"Recent failures (last {hours} hours):")
    else:
        failures = tracker.get_failed_conversions()
        print("All failed conversions:")
    
    # Apply filters
    if error_type:
        failures = [f for f in failures if f['error_type'] == error_type]
        print(f"Filtered by error type: {error_type}")
    
    if filename:
        failures = [f for f in failures if filename in f['filename']]
        print(f"Filtered by filename: {filename}")
    
    if not failures:
        print("No failures found matching the criteria.")
        return
    
    print(f"\nFound {len(failures)} failures:")
    print("-" * 80)
    
    for i, failure in enumerate(failures, 1):
        print(f"{i}. {failure['filename']}")
        print(f"   Timestamp: {failure['timestamp']}")
        print(f"   Error Type: {failure['error_type']}")
        print(f"   Error Message: {failure['error_message']}")
        print(f"   File Size: {failure['file_size_bytes']} bytes")
        print(f"   Attempt Count: {failure['attempt_count']}")
        print()

def export_failures(tracker, output_file, error_type, filename):
    """Export failed conversions to a new CSV file."""
    if not output_file:
        output_file = f"failed_conversions_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    filters = {}
    if error_type:
        filters['error_type'] = error_type
    if filename:
        # For filename filtering, we'll need to handle this differently
        # since it's a partial match
        pass
    
    try:
        tracker.export_failures_to_csv(output_file, filters)
        print(f"[OK] Exported failures to: {output_file}")
    except Exception as e:
        print(f"[FAILED] Error exporting failures: {str(e)}")

def clear_old_records(tracker, days):
    """Clear old failed conversion records."""
    try:
        before_count = len(tracker.get_failed_conversions())
        tracker.clear_old_records(days)
        after_count = len(tracker.get_failed_conversions())
        removed_count = before_count - after_count
        
        print(f"[OK] Cleared {removed_count} old records (older than {days} days)")
        print(f"Remaining records: {after_count}")
    except Exception as e:
        print(f"[FAILED] Error clearing old records: {str(e)}")

if __name__ == "__main__":
    import datetime
    main() 