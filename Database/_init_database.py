from Database.database import get_connection


def create_table():

    

    conn = get_connection()

    try:

        with open("Database/schema.sql", "r") as file:
            sql = file.read()

        with conn.cursor() as cursor:
            cursor.execute(sql)
    
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    create_table()
    print("Database initialized successfully.")
