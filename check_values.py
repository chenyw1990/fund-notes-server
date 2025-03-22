#!/usr/bin/env python

from app import create_app
from app.models import Fund, FundValue

def main():
    app = create_app()
    with app.app_context():
        latest = FundValue.query.filter_by(fund_id=3).order_by(FundValue.date.desc()).first()
        if latest:
            print("Latest value date:", latest.date)
            print("Unit value:", latest.net_value)
            print("Accumulated value:", latest.accumulated_value)
            print("Daily change:", latest.daily_change, "%")
            print("Week change:", latest.last_week_change, "%")
            print("Month change:", latest.last_month_change, "%")
            print("Year change:", latest.last_year_change, "%")
            print("Since inception:", latest.since_inception_change, "%")
        else:
            print("No fund value data found")

if __name__ == "__main__":
    main() 