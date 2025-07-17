import sqlite3

DATABASE = 'users.db'

def insert_dummy_entry(user_id, date, start, end, break_start, break_end):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO entries (user_id, date, start, end, break_start, break_end)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, date, start, end, break_start, break_end))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Beispiel: Eintrag für User 1, 17.07.2025, Arbeitszeit 09:00-17:00, Pause 12:00-12:30
    insert_dummy_entry(1, '2025-07-17', '09:00', '17:00', '12:00', '12:30')
    print("Dummy-Daten wurden eingefügt.")
