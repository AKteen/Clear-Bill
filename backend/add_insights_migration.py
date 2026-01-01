from sqlalchemy import text
from database import engine

def add_insights_column():
    """Add insights column to documents table"""
    try:
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='documents' AND column_name='insights'
            """))
            
            if not result.fetchone():
                # Add the column
                conn.execute(text("ALTER TABLE documents ADD COLUMN insights JSON"))
                conn.commit()
                print("Added insights column to documents table")
            else:
                print("Insights column already exists")
                
    except Exception as e:
        print(f"Error adding insights column: {e}")

if __name__ == "__main__":
    add_insights_column()