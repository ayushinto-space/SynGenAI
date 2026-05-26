import os 
import random
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd
import numpy as np

fake = Faker('en_US')

# seed selection (for reproducibility)
Faker.seed(7)
random.seed(7)
np.random.seed(7)

def profile_generator(num_customers=100):
    customers = []
    
    # unique --> batch genration 
    # unique maintains internal memory log, performance issue with large sets 
    unique_ids = [f"CUST-{fake.unique.random_number(digits=5, fix_len=True)}" for _ in range(num_customers)]

    for i in range(num_customers):
        tier = random.choices(
            ['Bronze', 'Silver', 'Gold', 'Platinum'],
            weights=[0.5, 0.3, 0.15, 0.05],
            k=1
        )[0]

        # tracking date obj to bound transaction dates 
        account_created_dt = fake.date_between(start_date='-3y', end_date='today')

        profile = {
            "customer_id": unique_ids[i],
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "street_address": fake.street_address(),
            "city": fake.city(),
            "state": fake.state(),
            "zipcode": fake.zipcode(),
            "birth_date": fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%Y-%m-%d'),
            "account_created": account_created_dt,  
            "membership_tier": tier
        }
        customers.append(profile)
    
    return pd.DataFrame(customers)

def transaction_generator(df_customers, num_transactions=500):
    transactions = []
    
    # mapping customer IDs: account creation date obj
    cust_creation_dates = dict(zip(df_customers['customer_id'], df_customers['account_created']))
    customer_ids = list(cust_creation_dates.keys())

    categories = {
        'Electronics': (50.00, 1200.00),
        'Apparel': (15.00, 150.00),
        'Home & Kitchen': (20.00, 400.00),
        'Books': (10.00, 50.00),
        'Beauty': (10.00, 200.00)
    }
    
    cat_keys = list(categories.keys())

    for i in range(num_transactions):
        cust_id = random.choice(customer_ids)
        category = random.choice(cat_keys)

        min_p, max_p = categories[category]
        amount = round(random.uniform(min_p, max_p), 2)
        status = random.choices(['Approved', 'Declined'], weights=[0.97, 0.03], k=1)[0]

        # track timeframe between creation and now 
        acct_created_date = cust_creation_dates[cust_id]
        days_since_creation = (datetime.today().date() - acct_created_date).days
        
        # randomize using timeframe
        random_days_offset = random.randint(0, max(0, days_since_creation))
        random_seconds_offset = random.randint(0, 86400)
        
        tx_timestamp = datetime.combine(acct_created_date, datetime.min.time()) + \
                       timedelta(days=random_days_offset, seconds=random_seconds_offset)

        tx = {
            "transaction_id": f"TXN-{100000 + i}",
            "customer_id": cust_id,
            "timestamp": tx_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "category": category,
            "amount_usd": amount,
            "payment_method": random.choice(['Credit Card', 'PayPal', 'Apple Pay', 'Bank Transfer']),
            "status": status
        }
        transactions.append(tx)

    # clean up :)
    df_customers['account_created'] = df_customers['account_created'].apply(lambda x: x.strftime('%Y-%m-%d'))

    # transaction chronologically
    df_transactions = pd.DataFrame(transactions)
    df_transactions = df_transactions.sort_values(by='timestamp').reset_index(drop=True)

    return df_transactions

def main():
    print("Starting Synthetic Data Generator...")

    # data depth
    CUSTOMERS_COUNT = 250
    TRANSACTIONS_COUNT = 1000

    print(f"Generating {CUSTOMERS_COUNT} customer profiles...")
    df_customers = profile_generator(CUSTOMERS_COUNT)
    
    print(f"Generating {TRANSACTIONS_COUNT} transaction records...")
    df_transactions = transaction_generator(df_customers, TRANSACTIONS_COUNT)

    output_dir = "output_data"
    os.makedirs(output_dir, exist_ok=True)

    # saving to CSV
    cust_file = os.path.join(output_dir, "customers.csv")
    tx_file = os.path.join(output_dir, "transactions.csv")
    
    df_customers.to_csv(cust_file, index=False)
    df_transactions.to_csv(tx_file, index=False)
    
    print("\nSuccess! Files saved to the 'output_data' folder:")
    print(f"   - {cust_file} ({len(df_customers)} rows)")
    print(f"   - {tx_file} ({len(df_transactions)} rows)")

    # preview
    print("\nCustomer Data Preview:")
    print(df_customers[['customer_id', 'name', 'account_created', 'membership_tier']].head(3))
    
    print("\nTransactions Data Preview (Sorted Chronologically):")
    print(df_transactions[['transaction_id', 'customer_id', 'timestamp', 'amount_usd']].head(3))

if __name__ == "__main__":
    main()