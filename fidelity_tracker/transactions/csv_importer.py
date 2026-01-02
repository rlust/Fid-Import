"""
CSV Transaction Importer

Parses Fidelity transaction export files and imports them into the database.
Supports multiple CSV formats with flexible column mapping.
"""

import csv
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from decimal import Decimal


class FidelityCSVImporter:
    """Import transactions from Fidelity CSV exports"""

    # Common column name variations
    COLUMN_MAPPINGS = {
        'date': ['date', 'run date', 'trade date', 'settlement date', 'transaction date'],
        'account': ['account', 'account number', 'account id', 'account name'],
        'action': ['action', 'transaction type', 'type', 'description'],
        'symbol': ['symbol', 'ticker', 'security', 'security description'],
        'quantity': ['quantity', 'qty', 'shares', 'amount'],
        'price': ['price', 'price per share', 'unit price', 'share price'],
        'amount': ['amount', 'total amount', 'net amount', 'value', 'total'],
        'commission': ['commission', 'fee', 'fees', 'charges'],
        'description': ['description', 'memo', 'notes', 'comment'],
    }

    # Transaction type mapping
    ACTION_MAPPING = {
        'buy': ['buy', 'bought', 'purchase', 'purchased'],
        'sell': ['sell', 'sold', 'sale'],
        'dividend': ['dividend', 'div', 'cash dividend', 'qualified dividend'],
        'interest': ['interest', 'int'],
        'deposit': ['deposit', 'electronic funds transfer received', 'contribution'],
        'withdrawal': ['withdrawal', 'electronic funds transfer paid', 'distribution'],
        'transfer': ['transfer', 'journal'],
        'split': ['stock split', 'split'],
        'reinvest': ['reinvestment', 'reinvest', 'drip'],
    }

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _normalize_column_name(self, name: str) -> str:
        """Normalize column name for matching"""
        return name.lower().strip()

    def _detect_columns(self, headers: List[str]) -> Dict[str, Optional[int]]:
        """
        Detect which columns correspond to which fields

        Returns mapping of field_name -> column_index
        """
        normalized_headers = [self._normalize_column_name(h) for h in headers]
        column_map = {}

        for field, variations in self.COLUMN_MAPPINGS.items():
            column_map[field] = None
            for i, header in enumerate(normalized_headers):
                for variation in variations:
                    if variation in header or header in variation:
                        column_map[field] = i
                        break
                if column_map[field] is not None:
                    break

        return column_map

    def _normalize_action(self, action: str) -> str:
        """
        Normalize transaction action to standard type

        Returns: BUY, SELL, DIVIDEND, FEE, SPLIT, TRANSFER
        """
        action_lower = action.lower().strip()

        for standard_type, variations in self.ACTION_MAPPING.items():
            for variation in variations:
                if variation in action_lower:
                    return standard_type.upper()

        # Default to the original action if no mapping found
        return action.upper()

    def _parse_date(self, date_str: str) -> str:
        """
        Parse date string into ISO format (YYYY-MM-DD)

        Handles common formats:
        - MM/DD/YYYY
        - DD-MMM-YYYY (e.g., 15-Jan-2024)
        - YYYY-MM-DD
        """
        date_str = date_str.strip()

        # Try MM/DD/YYYY
        try:
            dt = datetime.strptime(date_str, '%m/%d/%Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass

        # Try DD-MMM-YYYY
        try:
            dt = datetime.strptime(date_str, '%d-%b-%Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass

        # Try YYYY-MM-DD (already in correct format)
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass

        # Try MM-DD-YYYY
        try:
            dt = datetime.strptime(date_str, '%m-%d-%Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass

        raise ValueError(f"Unable to parse date: {date_str}")

    def _parse_amount(self, amount_str: str) -> Decimal:
        """
        Parse amount string to Decimal

        Handles: $1,234.56, (1234.56), -1234.56, 1234.56
        """
        if not amount_str or amount_str.strip() == '':
            return Decimal('0')

        # Remove currency symbols, commas, and whitespace
        cleaned = re.sub(r'[$,\s]', '', amount_str.strip())

        # Handle parentheses (negative)
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]

        try:
            return Decimal(cleaned)
        except:
            return Decimal('0')

    def parse_csv(self, file_path: str) -> Tuple[List[Dict], List[str]]:
        """
        Parse CSV file and extract transactions

        Returns: (transactions, errors)
        """
        transactions = []
        errors = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Try to detect if file has BOM
                first_char = f.read(1)
                if first_char != '\ufeff':
                    f.seek(0)

                reader = csv.reader(f)
                headers = next(reader)

                # Detect column mapping
                column_map = self._detect_columns(headers)

                # Check if we found required columns
                required = ['date', 'action']
                missing = [field for field in required if column_map.get(field) is None]

                if missing:
                    errors.append(f"Missing required columns: {', '.join(missing)}")
                    return transactions, errors

                # Parse rows
                for row_num, row in enumerate(reader, start=2):
                    try:
                        if not row or all(not cell.strip() for cell in row):
                            continue  # Skip empty rows

                        transaction = self._parse_row(row, column_map)
                        if transaction:
                            transactions.append(transaction)

                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")

        except Exception as e:
            errors.append(f"Failed to read CSV: {str(e)}")

        return transactions, errors

    def _parse_row(self, row: List[str], column_map: Dict[str, Optional[int]]) -> Optional[Dict]:
        """Parse a single CSV row into a transaction dict"""

        def get_value(field: str) -> str:
            idx = column_map.get(field)
            if idx is not None and idx < len(row):
                return row[idx].strip()
            return ''

        # Get values
        date_str = get_value('date')
        action_str = get_value('action')
        symbol = get_value('symbol') or 'CASH'
        quantity_str = get_value('quantity')
        price_str = get_value('price')
        amount_str = get_value('amount')
        commission_str = get_value('commission')
        description = get_value('description') or action_str
        account = get_value('account') or 'DEFAULT'

        # Skip if no date or action
        if not date_str or not action_str:
            return None

        # Parse date
        try:
            transaction_date = self._parse_date(date_str)
        except ValueError as e:
            raise ValueError(f"Invalid date: {str(e)}")

        # Normalize action
        transaction_type = self._normalize_action(action_str)

        # Parse amounts
        quantity = self._parse_amount(quantity_str) if quantity_str else Decimal('0')
        price = self._parse_amount(price_str) if price_str else Decimal('0')
        amount = self._parse_amount(amount_str) if amount_str else Decimal('0')
        commission = self._parse_amount(commission_str) if commission_str else Decimal('0')

        # Calculate missing values
        if amount == 0 and quantity > 0 and price > 0:
            amount = quantity * price

        if price == 0 and quantity > 0 and amount > 0:
            price = amount / quantity

        return {
            'account_id': account,
            'ticker': symbol.upper() if symbol else 'CASH',
            'transaction_type': transaction_type,
            'transaction_date': transaction_date,
            'quantity': float(quantity),
            'price_per_share': float(price) if price > 0 else None,
            'total_amount': float(amount),
            'fees': float(commission) if commission > 0 else None,
            'notes': description,
            'source': 'csv_import'
        }

    def validate_transactions(self, transactions: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """
        Validate parsed transactions

        Returns: (valid_transactions, errors)
        """
        valid = []
        errors = []

        for i, txn in enumerate(transactions, start=1):
            try:
                # Required fields
                if not txn.get('transaction_date'):
                    errors.append(f"Transaction {i}: Missing date")
                    continue

                if not txn.get('transaction_type'):
                    errors.append(f"Transaction {i}: Missing type")
                    continue

                # Validate amounts for buy/sell
                if txn['transaction_type'] in ['BUY', 'SELL']:
                    if txn.get('quantity', 0) <= 0:
                        errors.append(f"Transaction {i}: Invalid quantity for {txn['transaction_type']}")
                        continue

                    if txn.get('total_amount', 0) <= 0:
                        errors.append(f"Transaction {i}: Invalid amount for {txn['transaction_type']}")
                        continue

                valid.append(txn)

            except Exception as e:
                errors.append(f"Transaction {i}: Validation error - {str(e)}")

        return valid, errors
