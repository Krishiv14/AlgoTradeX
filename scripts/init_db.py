"""
Initialize Database and Fetch Historical Data
Run this script ONCE after setting up the database
"""
import sys
sys.path.append('..')

from app.database import init_db, SessionLocal
from app.services.data_fetcher import DataFetcher
from datetime import datetime, timedelta

def main():
    print("=" * 60)
    print("🚀 AlgoTradeX - Database Initialization")
    print("=" * 60)
    
    # Step 1: Create all tables
    print("\n📊 Step 1: Creating database tables...")
    init_db()
    print("✅ Database tables created successfully!")
    
    # Step 2: Fetch Nifty 50 historical data
    print("\n📥 Step 2: Fetching Nifty 50 historical data...")
    print("⚠️  This will take approximately 5-10 minutes")
    print("💡 Tip: Go grab a coffee! ☕")
    
    response = input("\nProceed with data download? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        db = SessionLocal()
        fetcher = DataFetcher(db)
        
        # Fetch 5 years of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5 * 365)
        
        print(f"\nDownloading data from {start_date.date()} to {end_date.date()}")
        fetcher.fetch_nifty50_data(start_date, end_date, delay=1.0)
        
        db.close()
        
        print("\n" + "=" * 60)
        print("✅ INITIALIZATION COMPLETE!")
        print("=" * 60)
        print("\n🎉 Your AlgoTradeX platform is ready!")
        print("\nNext steps:")
        print("1. Start backend: python -m app.main")
        print("2. Start frontend: streamlit run streamlit_app.py")
        print("3. Open browser: http://localhost:8501")
    else:
        print("\n⏭️  Skipping data download.")
        print("You can run this later with: python scripts/fetch_historical.py")

if __name__ == "__main__":
    main()
