import sqlite3

def find_agent():
    try:
        conn = sqlite3.connect('conversations.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Find agent
        print("Searching for 'Digital Lab' agent...")
        cursor.execute("SELECT * FROM agents WHERE business_name LIKE '%Digital Lab%'")
        agents = cursor.fetchall()
        
        if not agents:
            print("No specific agent found with name 'Digital Lab'.")
            print("Note: The system uses a HARDCODED default 'Digital Lab' persona if no agent is selected.")
        else:
            for agent in agents:
                print(f"\nFOUND AGENT: ID {agent['id']}")
                print(f"Name: {agent['business_name']}")
                
                # Find owner
                cursor.execute("SELECT * FROM users WHERE id = ?", (agent['user_id'],))
                user = cursor.fetchone()
                if user:
                    print(f"OWNED BY: {user['email']}")
                    print(f"User ID: {user['id']}")
                else:
                    print("Owner user not found (deleted?)")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_agent()
