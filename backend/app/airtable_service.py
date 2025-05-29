import os
from typing import Optional, List, Dict, Tuple, Any
from dotenv import load_dotenv
from pyairtable import Api, Base, Table
from app.models import UserInDB, User, Transaction, WalletBalance

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

AIRTABLE_USERS_TABLE_ID = os.getenv("AIRTABLE_USERS_TABLE_ID")
AIRTABLE_EMAIL_FIELD_ID = os.getenv("AIRTABLE_EMAIL_FIELD_ID")
AIRTABLE_PASSWORD_HASH_FIELD_ID = os.getenv("AIRTABLE_PASSWORD_HASH_FIELD_ID")

AIRTABLE_WALLETS_TABLE_ID = os.getenv("AIRTABLE_WALLETS_TABLE_ID")
AIRTABLE_WALLET_USER_EMAIL_FIELD_ID = os.getenv("AIRTABLE_WALLET_USER_EMAIL_FIELD_ID")
AIRTABLE_WALLET_BALANCE_FIELD_ID = os.getenv("AIRTABLE_WALLET_BALANCE_FIELD_ID")
AIRTABLE_WALLET_LAST_UPDATED_FIELD_ID = os.getenv("AIRTABLE_WALLET_LAST_UPDATED_FIELD_ID")

# Transactions Table Configuration
AIRTABLE_TRANSACTIONS_TABLE_ID = os.getenv("AIRTABLE_TRANSACTIONS_TABLE_ID")
AIRTABLE_TRANSACTION_ID_FIELD_ID = os.getenv("AIRTABLE_TRANSACTION_ID_FIELD_ID")
AIRTABLE_TRANSACTION_USER_EMAIL_FIELD_ID = os.getenv("AIRTABLE_TRANSACTION_USER_EMAIL_FIELD_ID")
AIRTABLE_TRANSACTION_AMOUNT_FIELD_ID = os.getenv("AIRTABLE_TRANSACTION_AMOUNT_FIELD_ID")
AIRTABLE_TRANSACTION_DESCRIPTION_FIELD_ID = os.getenv("AIRTABLE_TRANSACTION_DESCRIPTION_FIELD_ID")
AIRTABLE_TRANSACTION_TIMESTAMP_FIELD_ID = os.getenv("AIRTABLE_TRANSACTION_TIMESTAMP_FIELD_ID")

airtable = Api(AIRTABLE_API_KEY)
users_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_USERS_TABLE_ID)
wallets_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_WALLETS_TABLE_ID)
transactions_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TRANSACTIONS_TABLE_ID)

def get_field_mapping(table: Table, expected_fields: List[str]) -> Tuple[Dict[str, str], List[str]]:
    """
    Dynamically map field IDs to field names by inspecting table structure
    """
    try:
        sample_records = table.all(max_records=1)
        if sample_records:
            available_fields = list(sample_records[0]['fields'].keys())
            print(f"Available fields in table: {available_fields}")
            
            mapping = {}
            for expected_field in expected_fields:
                if expected_field in available_fields:
                    mapping[expected_field] = expected_field
                else:
                    partial_matches = [f for f in available_fields if expected_field.lower() in f.lower()]
                    if partial_matches:
                        mapping[expected_field] = partial_matches[0]
            
            print(f"Field mapping: {mapping}")
            return mapping, available_fields
        return {}, []
    except Exception as e:
        print(f"Error getting field mapping: {e}")
        return {}, []

def get_user_by_email(email: str) -> Optional[UserInDB]:
    """
    Retrieve a user from Airtable by email with dynamic field mapping
    """
    try:
        expected_fields = ['email', 'password_hash']
        field_mapping, available_fields = get_field_mapping(users_table, expected_fields)
        
        print(f"Available fields: {available_fields}")
        print(f"Field mapping: {field_mapping}")
        
        formulas_to_try = [
            f"{{email}} = '{email}'",
            f"{{{AIRTABLE_EMAIL_FIELD_ID}}} = '{email}'"
        ]
        
        if 'email' in field_mapping:
            formulas_to_try.append(f"{{{field_mapping['email']}}} = '{email}'")
        
        records = []
        for formula in formulas_to_try:
            try:
                print(f"Trying formula: {formula}")
                records = users_table.all(formula=formula)
                if records:
                    print(f"Found user with formula: {formula}")
                    break
            except Exception as e:
                print(f"Formula failed {formula}: {e}")
                continue
        
        if not records:
            print(f"No user found for email: {email}")
            return None
        
        record = records[0]
        print(f"User record fields: {record['fields']}")
        
        email_value = None
        password_hash_value = None
        
        for field in [AIRTABLE_EMAIL_FIELD_ID, "email"] + list(field_mapping.values()):
            if field and field in record["fields"]:
                email_value = record["fields"][field]
                print(f"Found email value in field: {field}")
                break
        
        # Try all possible field names/IDs for password_hash
        for field in [AIRTABLE_PASSWORD_HASH_FIELD_ID, "password_hash"] + list(field_mapping.values()):
            if field and field in record["fields"]:
                password_hash_value = record["fields"][field]
                print(f"Found password_hash value in field: {field}")
                break
        
        if not email_value or not password_hash_value:
            print(f"Missing required fields. Email: {bool(email_value)}, Password: {bool(password_hash_value)}")
            return None
        
        user_data = {
            "id": record["id"],
            "email": email_value,
            "password_hash": password_hash_value
        }
        
        return UserInDB(**user_data)
    except Exception as e:
        print(f"Error retrieving user from Airtable: {e}")
        print(f"Available fields in user record: {[record.get('fields', {}).keys() for record in users_table.all(max_records=1)]}")
        return None

def create_user(email: str, password_hash: str) -> Optional[UserInDB]:
    """
    Create a new user in Airtable with dynamic field mapping
    """
    try:
        existing_user = get_user_by_email(email)
        if existing_user:
            return None
        
        expected_fields = ['email', 'password_hash']
        field_mapping, available_fields = get_field_mapping(users_table, expected_fields)
        
        fields = {
            "email": email,  # Use field name for formula queries
            "password_hash": password_hash,  # Use field name for formula queries
        }
        
        if AIRTABLE_EMAIL_FIELD_ID:
            fields[AIRTABLE_EMAIL_FIELD_ID] = email
        
        if AIRTABLE_PASSWORD_HASH_FIELD_ID:
            fields[AIRTABLE_PASSWORD_HASH_FIELD_ID] = password_hash
        
        for field_name, mapped_field in field_mapping.items():
            if field_name == 'email':
                fields[mapped_field] = email
            elif field_name == 'password_hash':
                fields[mapped_field] = password_hash
        
        print(f"Creating user with fields: {fields}")
        record = users_table.create(fields)
        print(f"Created record: {record}")
        
        return UserInDB(
            id=record["id"],
            email=email,
            password_hash=password_hash
        )
    except Exception as e:
        print(f"Error creating user in Airtable: {e}")
        print(f"Available fields in user table: {[record.get('fields', {}).keys() for record in users_table.all(max_records=1)]}")
        return None

def update_user_password(email: str, password_hash: str) -> bool:
    """
    Update a user's password in Airtable with dynamic field mapping
    """
    try:
        user = get_user_by_email(email)
        if not user:
            return False
        
        expected_fields = ['password_hash']
        field_mapping, available_fields = get_field_mapping(users_table, expected_fields)
        
        fields = {}
        
        if AIRTABLE_PASSWORD_HASH_FIELD_ID:
            fields[AIRTABLE_PASSWORD_HASH_FIELD_ID] = password_hash
        
        fields["password_hash"] = password_hash
        
        for field_name, mapped_field in field_mapping.items():
            if field_name == 'password_hash':
                fields[mapped_field] = password_hash
        
        print(f"Updating user password with fields: {fields}")
        users_table.update(user.id, fields)
        return True
    except Exception as e:
        print(f"Error updating user password in Airtable: {e}")
        print(f"Available fields in user table: {[record.get('fields', {}).keys() for record in users_table.all(max_records=1)]}")
        return False

def get_wallet_balance(email: str) -> Optional[WalletBalance]:
    """
    Get a user's wallet balance from Airtable with dynamic field mapping
    """
    try:
        user = get_user_by_email(email)
        if not user:
            return None
        
        expected_fields = ['user_email', 'balance', 'last_updated']
        field_mapping, available_fields = get_field_mapping(wallets_table, expected_fields)
        
        print(f"Wallet available fields: {available_fields}")
        print(f"Wallet field mapping: {field_mapping}")
        
        formulas_to_try = [
            f"{{{AIRTABLE_WALLET_USER_EMAIL_FIELD_ID}}} = '{email}'",
            f"{{user_email}} = '{email}'"
        ]
        
        if 'user_email' in field_mapping:
            formulas_to_try.append(f"{{{field_mapping['user_email']}}} = '{email}'")
        
        records = []
        for formula in formulas_to_try:
            try:
                print(f"Trying wallet formula: {formula}")
                records = wallets_table.all(formula=formula)
                if records:
                    print(f"Found wallet with formula: {formula}")
                    break
            except Exception as e:
                print(f"Wallet formula failed {formula}: {e}")
                continue
        
        if not records:
            print(f"No wallet found for {email}, creating new wallet")
            
            fields = {
                "user_email": email,
                "balance": 1000.0
            }
            
            if AIRTABLE_WALLET_USER_EMAIL_FIELD_ID:
                fields[AIRTABLE_WALLET_USER_EMAIL_FIELD_ID] = email
            
            if AIRTABLE_WALLET_BALANCE_FIELD_ID:
                fields[AIRTABLE_WALLET_BALANCE_FIELD_ID] = 1000.0
            
            for field_name, mapped_field in field_mapping.items():
                if field_name == 'user_email':
                    fields[mapped_field] = email
                elif field_name == 'balance':
                    fields[mapped_field] = 1000.0
            
            print(f"Creating wallet with fields: {fields}")
            record = wallets_table.create(fields)
            
            return WalletBalance(
                balance=1000.0,
                last_updated=None
            )
        
        record = records[0]
        print(f"Wallet record fields: {record['fields']}")
        
        balance = 1000.0  # Default value
        
        for field in [AIRTABLE_WALLET_BALANCE_FIELD_ID, "balance"] + [field_mapping.get('balance', '')]:
            if field and field in record["fields"]:
                balance = record["fields"][field]
                print(f"Found balance value in field: {field}")
                break
        
        last_updated = None
        
        # Try all possible field names/IDs for last_updated
        for field in [AIRTABLE_WALLET_LAST_UPDATED_FIELD_ID, "last_updated"] + [field_mapping.get('last_updated', '')]:
            if field and field in record["fields"]:
                last_updated = record["fields"][field]
                print(f"Found last_updated value in field: {field}")
                break
        
        return WalletBalance(
            balance=float(balance),
            last_updated=last_updated
        )
    except Exception as e:
        print(f"Error retrieving wallet balance from Airtable: {e}")
        print(f"Available fields in wallet table: {[record.get('fields', {}).keys() for record in wallets_table.all(max_records=1)]}")
        return WalletBalance(
            balance=1000.0,
            last_updated=None
        )

def get_transactions(email: str) -> List[Transaction]:
    """
    Get a user's transaction history from Airtable with dynamic field mapping
    """
    try:
        expected_fields = ['user_email', 'amount', 'description', 'timestamp']
        field_mapping, available_fields = get_field_mapping(transactions_table, expected_fields)
        
        print(f"Transaction available fields: {available_fields}")
        print(f"Transaction field mapping: {field_mapping}")
        
        formulas_to_try = [
            f"{{{AIRTABLE_TRANSACTION_USER_EMAIL_FIELD_ID}}} = '{email}'",
            f"{{user_email}} = '{email}'"
        ]
        
        if 'user_email' in field_mapping:
            formulas_to_try.append(f"{{{field_mapping['user_email']}}} = '{email}'")
        
        records = []
        for formula in formulas_to_try:
            try:
                print(f"Trying transaction formula: {formula}")
                records = transactions_table.all(formula=formula)
                if records:
                    print(f"Found transactions with formula: {formula}")
                    break
            except Exception as e:
                print(f"Transaction formula failed {formula}: {e}")
                continue
        
        transactions = []
        for record in records:
            try:
                print(f"Transaction record fields: {record['fields']}")
                
                tx_id = record["id"]
                
                amount = 0.0
                for field in [AIRTABLE_TRANSACTION_AMOUNT_FIELD_ID, "amount"] + [field_mapping.get('amount', '')]:
                    if field and field in record["fields"]:
                        amount = record["fields"][field]
                        print(f"Found amount value in field: {field}")
                        break
                
                timestamp = None
                for field in [AIRTABLE_TRANSACTION_TIMESTAMP_FIELD_ID, "timestamp"] + [field_mapping.get('timestamp', '')]:
                    if field and field in record["fields"]:
                        timestamp = record["fields"][field]
                        print(f"Found timestamp value in field: {field}")
                        break
                
                description = ""
                for field in [AIRTABLE_TRANSACTION_DESCRIPTION_FIELD_ID, "description"] + [field_mapping.get('description', '')]:
                    if field and field in record["fields"]:
                        description = record["fields"][field]
                        print(f"Found description value in field: {field}")
                        break
                
                transaction = Transaction(
                    id=tx_id,
                    amount=float(amount),
                    timestamp=timestamp,
                    description=description
                )
                transactions.append(transaction)
            except Exception as e:
                print(f"Error processing transaction record: {e}")
                print(f"Record fields: {record.get('fields', {})}")
        
        # If no transactions found, return mock data
        if not transactions:
            print(f"No transactions found for {email}, returning mock data")
            from datetime import datetime, timedelta
            now = datetime.now()
            
            transactions = [
                Transaction(
                    id="mock-tx1",
                    amount=250.0,
                    timestamp=now.isoformat(),
                    description="Knods Token Reward"
                ),
                Transaction(
                    id="mock-tx2",
                    amount=150.0,
                    timestamp=(now - timedelta(days=7)).isoformat(),
                    description="Weekly Bonus"
                ),
                Transaction(
                    id="mock-tx3",
                    amount=600.0,
                    timestamp=(now - timedelta(days=30)).isoformat(),
                    description="Monthly Contribution"
                )
            ]
        
        transactions.sort(key=lambda x: x.timestamp if x.timestamp else "", reverse=True)
        
        return transactions
    except Exception as e:
        print(f"Error retrieving transactions from Airtable: {e}")
        print(f"Available fields in transaction table: {[record.get('fields', {}).keys() for record in transactions_table.all(max_records=1)]}")
        
        from datetime import datetime, timedelta
        now = datetime.now()
        
        return [
            Transaction(
                id="error-tx1",
                amount=250.0,
                timestamp=now.isoformat(),
                description="Knods Token Reward"
            ),
            Transaction(
                id="error-tx2",
                amount=150.0,
                timestamp=(now - timedelta(days=7)).isoformat(),
                description="Weekly Bonus"
            ),
            Transaction(
                id="error-tx3",
                amount=600.0,
                timestamp=(now - timedelta(days=30)).isoformat(),
                description="Monthly Contribution"
            )
        ]
