import csv

import numpy as np
import psycopg2
import pandas as pd
from collections import Counter
from flask import Flask, jsonify, request
from psycopg2.extensions import register_adapter, AsIs

register_adapter(np.int64, AsIs)
app = Flask(__name__)


@app.route('/etl')
def trigger_etl():
    try:
        # Step 1: Load CSV files from the given data directory.

        df_compounds = pd.read_csv("src/data/compounds.csv")
        df_users_experiments = pd.read_csv("src/data/user_experiments.csv")
        df_users = pd.read_csv("src/data/users.csv")

        df_users.rename(columns={'\tname': 'name', '\temail': 'email', '\tsignup_date': 'signup_date'}, inplace=True)
        df_users['name'] = df_users['name'].str[1:]
        df_users['email'] = df_users['email'].str[1:]
        df_users['signup_date'] = df_users['signup_date'].str[1:]

        df_users_experiments.rename(
            columns={'\tuser_id': 'user_id', '\texperiment_compound_ids': 'experiment_compound_ids',
                     '\texperiment_run_time': 'experiment_run_time'}, inplace=True)
        df_users_experiments['experiment_compound_ids'] = df_users_experiments['experiment_compound_ids'].str[1:]
        df_compounds.rename(columns={'\tcompound_name': 'compound_name', '\tcompound_structure': 'compound_structure'},
                            inplace=True)
        df_compounds['compound_name'] = df_compounds['compound_name'].str[1:]
        df_compounds['compound_structure'] = df_compounds['compound_structure'].str[1:]

        # Step 2: Process these files to derive some simple features.
        # a. Total experiments a user ran.

        total_experiments_per_user = df_users_experiments.groupby('user_id').agg({'experiment_id': pd.Series.nunique})
        df_user_part = df_users[['user_id', 'name']]
        total_experiments_per_user = pd.merge(total_experiments_per_user, df_user_part, on='user_id', how='inner')
        total_experiments_per_user = total_experiments_per_user.iloc[:, [0, 2, 1]]

        # b. Average experiments amount per user.

        avg_exp_amount = sum(total_experiments_per_user['experiment_id']) / total_experiments_per_user[
            'user_id'].count()

        # c. User's most commonly experimented compound.

        df_users_experiments['experiment_compound_ids'] = df_users_experiments['experiment_compound_ids'].str.split(";")
        flattened_compound = [item for sublist in df_users_experiments['experiment_compound_ids'] for item in sublist]
        counter_compound = Counter(flattened_compound)  # HashMap here to count
        key_with_max_value = max(counter_compound, key=counter_compound.get)
        most_experimented_compound = df_compounds.iloc[int(key_with_max_value) - 1]

        print(total_experiments_per_user)
        print(avg_exp_amount)
        print(most_experimented_compound)
        # Step 3: Upload the processed data into a postgres table.
        connection = psycopg2.connect(
            host='database',
            port='5432',
            database='etl-db',
            user='docker',
            password='docker'
        )
        cursor = connection.cursor()

        table1_name = 'total_experiments_per_user'
        table2_name = 'avg_experiments_amount'
        table3_name = 'most_experimented_compound'

        for i in range(len(total_experiments_per_user)):
            insert_query = f"INSERT INTO {table1_name} (user_id, name, experiment_qty) VALUES (%s, %s, %s)"
            values = (total_experiments_per_user.loc[i, "user_id"],
                      total_experiments_per_user.loc[i, "name"],
                      total_experiments_per_user.loc[i, "experiment_id"])
            cursor.execute(insert_query, values)

        insert_query = f"INSERT INTO {table2_name} (avg_amount) VALUES (%s)"
        values = (avg_exp_amount,)
        cursor.execute(insert_query, values)

        df = most_experimented_compound
        insert_query = f"INSERT INTO {table3_name} (comp_id, comp_name, comp_structure) VALUES (%s, %s, %s)"
        values = (df[0], df[1], df[2])
        cursor.execute(insert_query, values)

        connection.commit()

        # Close the database connection
        cursor.close()
        connection.close()

        # Return a success response
        return jsonify({'status': 'success', 'message': 'ETL process completed successfully.'})

    except Exception as e:
        # Return an error response if any exception occurs
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/data')
def get_data():
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(
            host='database',
            port='5432',
            database='etl-db',
            user='docker',
            password='docker'
        )
        cursor = connection.cursor()

        # Query to retrieve data from the first table
        query1 = 'SELECT * FROM total_experiments_per_user'
        cursor.execute(query1)
        rows1 = cursor.fetchall()

        # Query to retrieve data from the second table
        query2 = 'SELECT * FROM avg_experiments_amount'
        cursor.execute(query2)
        rows2 = cursor.fetchall()

        # Query to retrieve data from the third table
        query3 = 'SELECT * FROM most_experimented_compound'
        cursor.execute(query3)
        rows3 = cursor.fetchall()

        # Close the database connection
        cursor.close()
        connection.close()

        # Format the data from each table as a list of dictionaries
        data1 = []
        for row in rows1:
            data1.append({
                'id': row[0],
                'user_id': row[1],
                'name': row[2],
                'experiment_qty': row[3],
                'time_stamp': row[4],
            })

        data2 = []
        for row in rows2:
            data2.append({
                'id': row[0],
                'avg_amount': row[1],
                'time_stamp': row[2]
            })

        data3 = []
        for row in rows3:
            data3.append({
                'id': row[0],
                'comp_id': row[1],
                'comp_name': row[2],
                'comp_structure': row[3],
                'time_stamp': row[4],
            })

        # Combine the data from all tables into a single response
        combined_data = {
            'table1': data1,
            'table2': data2,
            'table3': data3
        }

        # Return the combined data as JSON response
        return jsonify({'status': 'success', 'data': combined_data})

    except Exception as e:
        # Return an error response if any exception occurs
        return jsonify({'status': 'error', 'message': str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=8000, host="0.0.0.0")
