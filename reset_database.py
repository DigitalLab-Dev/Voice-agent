#!/usr/bin/env python3
"""
Database Reset Script for Digital Lab AI Agent
Clears all data and creates admin user
"""

from database import ConversationDatabase
from auth import auth_manager
import os

def reset_database():
    """Reset database and create admin user"""
    
    print("=" * 60)
    print("🔄 DATABASE RESET SCRIPT")
    print("=" * 60)
    print()
    
    # Confirm action
    print("⚠️  WARNING: This will DELETE ALL DATA!")
    print("   - All users and agents")
    print("   - All conversations and messages")
    print("   - All verification codes")
    print()
    
    confirm = input("Type 'DELETE ALL' to confirm: ")
    
    if confirm != "DELETE ALL":
        print("❌ Reset cancelled")
        return
    
    print()
    print("🗑️  Clearing data...")
    
    # Initialize database
    db = ConversationDatabase()
    
    # Clear conversation data
    db.clear_all_data()
    
    # Clear user and agent data
    auth_manager.clear_all_users_and_agents()
    
    print()
    print("✅ All data cleared!")
    print()
    
    # Create admin user
    print("👤 Creating admin user...")
    admin_email = "syedaliturab@gmail.com"
    admin_password = "Admin@123"
    
    auth_manager.create_admin_user(admin_email, admin_password)
    
    print()
    print("=" * 60)
    print("✅ DATABASE RESET COMPLETE!")
    print("=" * 60)
    print()
    print(f"📧 Admin Email: {admin_email}")
    print(f"🔑 Admin Password: {admin_password}")
    print()
    print("🚀 You can now start the application with:")
    print("   python app.py")
    print()

if __name__ == "__main__":
    reset_database()
