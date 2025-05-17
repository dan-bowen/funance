import json
import logging
import pdfplumber
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator

class Holding(BaseModel):
    """Model for a single holding."""
    ticker_symbol: str
    quantity: float

    @field_validator('ticker_symbol')
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate ticker symbol format."""
        if not v.isupper():
            raise ValueError(f"Ticker {v} must be uppercase")
        if any(c.isdigit() for c in v):
            raise ValueError(f"Ticker {v} must not contain numbers")
        if v.startswith('(') or v.endswith(')'):
            raise ValueError(f"Ticker {v} must not be in parentheses")
        if not (1 <= len(v) <= 5):
            raise ValueError(f"Ticker {v} must be between 1 and 5 characters")
        return v

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError(f"Quantity {v} must be positive")
        return v

class DividendSummary(BaseModel):
    """Model for dividend summary data."""
    current_month: Optional[float] = None
    year_to_date: Optional[float] = None

    @field_validator('current_month', 'year_to_date')
    @classmethod
    def validate_amount(cls, v: Optional[float]) -> Optional[float]:
        """Validate dividend amounts are non-negative."""
        if v is not None and v < 0:
            raise ValueError(f"Dividend amount {v} must be non-negative")
        return v

class VanguardStatement(BaseModel):
    """Model for Vanguard statement data."""
    total_value: float = Field(..., description="Total portfolio value")
    statement_date: str = Field(..., description="Statement date in YYYY-MM-DD format")
    cash_balance: Optional[float] = Field(None, description="Cash balance in sweep account")
    dividends: DividendSummary = Field(default_factory=DividendSummary)
    holdings: List[Holding] = Field(default_factory=list)

    @field_validator('statement_date')
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate date format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD")
        return v

    @field_validator('total_value')
    @classmethod
    def validate_total_value(cls, v: float) -> float:
        """Validate total value is positive."""
        if v <= 0:
            raise ValueError(f"Total value {v} must be positive")
        return v

    @field_validator('cash_balance')
    @classmethod
    def validate_cash_balance(cls, v: Optional[float]) -> Optional[float]:
        """Validate cash balance is non-negative."""
        if v is not None and v < 0:
            raise ValueError(f"Cash balance {v} must be non-negative")
        return v

    @model_validator(mode='after')
    def validate_portfolio(self) -> 'VanguardStatement':
        """Validate portfolio consistency."""
        # Calculate total holdings value (if we had price data)
        # holdings_total = sum(h.quantity * h.price for h in self.holdings)
        
        # Ensure we have at least one holding
        if not self.holdings:
            raise ValueError("No holdings found in statement")
        
        # Ensure total value is greater than cash balance
        if self.cash_balance is not None and self.total_value < self.cash_balance:
            raise ValueError(f"Total value {self.total_value} is less than cash balance {self.cash_balance}")
        
        return self

# Configure logging with fixed-width format
class FixedWidthFormatter(logging.Formatter):
    """Custom formatter that ensures log levels have fixed width and includes module:line."""
    def format(self, record):
        # Set fixed width for log level
        record.levelname = f"{record.levelname:8}"
        # Add module:line to the message
        record.msg = f"[{record.module}:{record.lineno:3}] {record.msg}"
        return super().format(record)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
# Apply custom formatter
for handler in logging.getLogger().handlers:
    handler.setFormatter(FixedWidthFormatter('%(levelname)s - %(message)s'))

_LOGGER = logging.getLogger(__name__)

def find_holdings_section(page) -> Tuple[float, float]:
    """
    Find the y-coordinates of the holdings section on a page.
    Returns (top, bottom) coordinates or (None, None) if not found.
    """
    words = page.extract_words()
    top = None
    bottom = None
    
    for word in words:
        if word['text'] == 'ETFs' or word['text'] == 'Stocks':
            top = word['top']
        elif word['text'] == 'Account' and 'activity' in [w['text'] for w in words if abs(w['top'] - word['top']) < 10]:
            bottom = word['top']
            break
    
    return (top, bottom)

def is_valid_ticker(ticker: str) -> bool:
    """
    Validate if a string is a valid ticker symbol.
    """
    # Must be all uppercase
    if not ticker.isupper():
        return False
    
    # Must not contain numbers
    if any(c.isdigit() for c in ticker):
        return False
    
    # Must not be in parentheses
    if ticker.startswith('(') or ticker.endswith(')'):
        return False
    
    # Must be between 1 and 5 characters
    if not (1 <= len(ticker) <= 5):
        return False
    
    return True

def extract_income_summary(text: str) -> Dict[str, float]:
    """
    Extract income summary data from text.
    Returns a dictionary with current_month and year_to_date values.
    """
    _LOGGER.info("Searching for income summary...")
    result = {
        "current_month": None,
        "year_to_date": None
    }
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if "Income summary" in line:
            _LOGGER.info(f"Found income summary section at line {i}")
            # Look for the next few lines for the totals
            for j in range(i, min(i + 10, len(lines))):
                current_line = lines[j]
                _LOGGER.debug(f"Checking line {j}: {current_line}")
                
                # Look for the current month line (e.g., "April $74.73 $0.00 $0.00 $0.00 $0.00 $0.00")
                if any(month in current_line for month in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]):
                    _LOGGER.info(f"Found current month line: {current_line}")
                    try:
                        # Get the first number after the month (dividends)
                        parts = current_line.split()
                        for part in parts:
                            if part.startswith('$'):
                                current_month_str = part.replace('$', '').replace(',', '')
                                if current_month_str.replace('.', '').isdigit():
                                    result["current_month"] = float(current_month_str)
                                    _LOGGER.info(f"Found current month income: {result['current_month']}")
                                    break
                    except (ValueError, IndexError) as e:
                        _LOGGER.error(f"Error parsing current month: {e}")
                
                # Look for the year-to-date line
                if "Year-to-date" in current_line:
                    _LOGGER.info(f"Found year-to-date line: {current_line}")
                    try:
                        # Get the first number after "Year-to-date" (dividends)
                        parts = current_line.split()
                        for part in parts:
                            if part.replace(',', '').replace('.', '').isdigit():
                                ytd_str = part.replace(',', '')
                                result["year_to_date"] = float(ytd_str)
                                _LOGGER.info(f"Found year-to-date income: {result['year_to_date']}")
                                break
                    except (ValueError, IndexError) as e:
                        _LOGGER.error(f"Error parsing year-to-date: {e}")
    
    if result["current_month"] is None and result["year_to_date"] is None:
        _LOGGER.warning("No income data found in the expected format")
    return result

def extract_cash_balance(text: str) -> Optional[float]:
    """
    Extract cash balance from text, looking for common cash fund names.
    """
    _LOGGER.info("Searching for cash balance...")
    lines = text.split('\n')
    for i, line in enumerate(lines):
        # Look for the Total Sweep Balance line
        if "Total Sweep Balance" in line:
            _LOGGER.info(f"Found sweep balance line: {line}")
            try:
                # Split by $ and take the last number
                parts = line.split('$')
                if len(parts) >= 3:  # We expect at least 3 parts: text, first number, second number
                    # Get the last number after the last $ symbol
                    balance_str = parts[-1].strip().replace(',', '')
                    balance = float(balance_str)
                    _LOGGER.info(f"Found cash balance: {balance}")
                    return balance
            except (ValueError, IndexError) as e:
                _LOGGER.error(f"Error parsing balance: {e}")
                continue
    
    _LOGGER.warning("No cash balance found")
    return None

def extract_vanguard_statement(pdf_path: str) -> VanguardStatement:
    """
    Extract investment data from a Vanguard PDF statement.
    
    Args:
        pdf_path: Path to the PDF statement
        
    Returns:
        VanguardStatement object containing extracted data
        
    Raises:
        ValueError: If required data is missing or invalid
    """
    # Initialize data dictionary for incremental building
    data = {
        "total_value": None,
        "statement_date": None,
        "cash_balance": None,
        "dividends": {
            "current_month": None,
            "year_to_date": None
        },
        "holdings": []
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        # First pass: get basic info
        for page_num, page in enumerate(pdf.pages, 1):
            _LOGGER.info(f"Processing page {page_num} for basic info")
            text = page.extract_text()
            
            # Extract statement date (found in header of each page)
            if "monthly transaction statement" in text:
                date_line = text.split('\n')[0]
                try:
                    data["statement_date"] = datetime.strptime(date_line, "%B %d, %Y, monthly transaction statement").strftime("%Y-%m-%d")
                except ValueError:
                    _LOGGER.error(f"Failed to parse date from line: {date_line}")
            
            # Extract total value (found in Statement overview section)
            if "Statement overview" in text:
                value_line = [line for line in text.split('\n') if "Statement overview" in line][0]
                try:
                    value_str = value_line.split("$")[1].strip().replace(",", "")
                    data["total_value"] = float(value_str)
                except (IndexError, ValueError) as e:
                    _LOGGER.error(f"Failed to parse total value: {e}")
            
            # Extract cash balance
            cash_balance = extract_cash_balance(text)
            if cash_balance is not None:
                data["cash_balance"] = cash_balance
                _LOGGER.info(f"Set cash balance to: {cash_balance}")
            
            # Extract income summary
            income_data = extract_income_summary(text)
            if income_data["current_month"] is not None:
                data["dividends"]["current_month"] = income_data["current_month"]
            if income_data["year_to_date"] is not None:
                data["dividends"]["year_to_date"] = income_data["year_to_date"]
        
        # Second pass: extract holdings using word extraction
        for page_num, page in enumerate(pdf.pages, 1):
            _LOGGER.info(f"Processing page {page_num} for holdings")
            
            # Find holdings section boundaries
            top, bottom = find_holdings_section(page)
            if not top:
                continue
                
            _LOGGER.info(f"Found holdings section at y={top}")
            
            # Extract words in the holdings section
            words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=True,
                use_text_flow=True,
                horizontal_ltr=True,
                vertical_ttb=True,
                extra_attrs=['fontname', 'size']
            )
            
            # Filter words to holdings section
            holdings_words = [w for w in words if top <= w['top'] <= (bottom if bottom else page.height)]
            
            # Group words into lines
            current_line = []
            current_y = None
            lines = []
            
            for word in holdings_words:
                if current_y is None:
                    current_y = word['top']
                
                # If y-coordinate changes significantly, start new line
                if abs(word['top'] - current_y) > 5:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word['text']]
                    current_y = word['top']
                else:
                    current_line.append(word['text'])
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Process each line
            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    # Check if first part is a valid ticker
                    ticker = parts[0]
                    if not is_valid_ticker(ticker):
                        continue
                    
                    # Find the quantity (first number after ticker)
                    for part in parts[1:]:
                        try:
                            quantity_str = part.replace(',', '')
                            if quantity_str.replace('.', '').isdigit():
                                quantity = float(quantity_str)
                                data["holdings"].append({
                                    "ticker_symbol": ticker,
                                    "quantity": quantity
                                })
                                _LOGGER.info(f"Added holding: {ticker} - {quantity}")
                                break
                        except ValueError:
                            continue
    
    # Validate and create the statement object
    try:
        statement = VanguardStatement(**data)
        _LOGGER.info("Successfully validated statement data")
        return statement
    except ValueError as e:
        _LOGGER.error(f"Validation error: {e}")
        raise

def main():
    # Get the current directory
    current_dir = Path.cwd()
    pdf_path = current_dir / "statement.pdf"
    
    if not pdf_path.exists():
        _LOGGER.error(f"Error: Could not find statement.pdf in {current_dir}")
        return
    
    try:
        # Extract data
        statement = extract_vanguard_statement(str(pdf_path))
        
        # Write to JSON file
        output_path = current_dir / "statement_data.json"
        with open(output_path, 'w') as f:
            json.dump(statement.model_dump(), f, indent=2)
        
        _LOGGER.info(f"Data extracted and saved to {output_path}")
        _LOGGER.info("Extracted data:")
        _LOGGER.info(json.dumps(statement.model_dump(), indent=2))
    except ValueError as e:
        _LOGGER.error(f"Failed to process statement: {e}")
        return

def test_validation():
    """Test function to demonstrate validation errors."""
    test_cases = [
        {
            "name": "Missing required fields",
            "data": {
                "total_value": None,
                "statement_date": None,
                "cash_balance": None,
                "dividends": {"current_month": None, "year_to_date": None},
                "holdings": []
            }
        },
        {
            "name": "Invalid ticker symbol",
            "data": {
                "total_value": 100000.0,
                "statement_date": "2024-03-15",
                "cash_balance": 1000.0,
                "dividends": {"current_month": 100.0, "year_to_date": 500.0},
                "holdings": [
                    {"ticker_symbol": "AAPL1", "quantity": 100.0},  # Contains number
                    {"ticker_symbol": "msft", "quantity": 50.0},    # Not uppercase
                    {"ticker_symbol": "(TSLA)", "quantity": 25.0},  # In parentheses
                    {"ticker_symbol": "TOOLONG", "quantity": 10.0}  # Too long
                ]
            }
        },
        {
            "name": "Invalid quantities and amounts",
            "data": {
                "total_value": -100000.0,  # Negative total value
                "statement_date": "2024-03-15",
                "cash_balance": -1000.0,   # Negative cash balance
                "dividends": {
                    "current_month": -100.0,  # Negative dividend
                    "year_to_date": -500.0    # Negative dividend
                },
                "holdings": [
                    {"ticker_symbol": "AAPL", "quantity": -100.0},  # Negative quantity
                    {"ticker_symbol": "MSFT", "quantity": 0.0}      # Zero quantity
                ]
            }
        },
        {
            "name": "Invalid date format",
            "data": {
                "total_value": 100000.0,
                "statement_date": "03/15/2024",  # Wrong format
                "cash_balance": 1000.0,
                "dividends": {"current_month": 100.0, "year_to_date": 500.0},
                "holdings": [
                    {"ticker_symbol": "AAPL", "quantity": 100.0}
                ]
            }
        },
        {
            "name": "Portfolio consistency",
            "data": {
                "total_value": 1000.0,     # Small total value
                "statement_date": "2024-03-15",
                "cash_balance": 2000.0,    # Larger than total value
                "dividends": {"current_month": 100.0, "year_to_date": 500.0},
                "holdings": []             # No holdings
            }
        }
    ]

    for test_case in test_cases:
        _LOGGER.info(f"\nTesting: {test_case['name']}")
        try:
            statement = VanguardStatement(**test_case['data'])
            _LOGGER.info("Unexpected: Validation passed")
        except ValueError as e:
            _LOGGER.error(f"Expected validation error: {e}")

if __name__ == "__main__":
    # Uncomment to run validation tests
    test_validation()
    main()
