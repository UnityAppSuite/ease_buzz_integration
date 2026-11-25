# Frappe Easebuzz Payment Gateway Integration

A comprehensive Frappe application for integrating Easebuzz Payment Gateway with ERPNext and other Frappe-based applications.

## 🚀 Features

- **Seamless Integration**: Easy integration with ERPNext Sales Orders, Invoices, and Payment Entries
- **Multiple Payment Methods**: Support for Credit/Debit Cards, Net Banking, UPI, and Wallets
- **Webhook Support**: Real-time payment status updates via webhooks
- **Transaction Management**: Complete transaction lifecycle management
- **Refund Support**: Handle partial and full refunds
- **Test & Live Mode**: Switch between sandbox and production environments
- **Comprehensive Logging**: Detailed transaction logs for debugging and auditing
- **Custom Fields**: Automatic creation of required custom fields

## 📋 Prerequisites

- Frappe Framework (v13.0+)
- ERPNext (v13.0+) - Optional, for ERP integrations
- Python 3.6+
- Valid Easebuzz merchant account

## 🔧 Installation

### Method 1: Using Bench (Recommended)

```bash
# Navigate to your frappe-bench directory
cd frappe-bench

# Get the app from GitHub
bench get-app https://github.com/yourusername/easebuzz_integration.git

# Install the app on your site
bench --site your-site-name install-app easebuzz_integration

# Run migrations
bench --site your-site-name migrate
```

### Method 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/easebuzz_integration.git

# Move to apps directory
mv easebuzz_integration frappe-bench/apps/

# Install the app
bench --site your-site-name install-app easebuzz_integration
```

## ⚙️ Configuration

### 1. Easebuzz Settings

Navigate to **Setup > Integrations > Easebuzz Settings** and configure:

- **Merchant Key**: Your Easebuzz merchant key
- **Salt Key**: Your Easebuzz salt key
- **Environment**: Choose between 'Sandbox' and 'Production'
- **Success URL**: URL to redirect after successful payment
- **Failure URL**: URL to redirect after failed payment
- **Webhook URL**: URL for receiving payment notifications

### 2. Payment Gateway Setup

Go to **Accounts > Payment Gateway** and create a new gateway:

- **Gateway**: Select "Easebuzz"
- **Settings**: Link to your Easebuzz Settings
- **Supported Currencies**: INR (Indian Rupee)

### 3. Webhook Configuration

Set up webhook endpoint in your Easebuzz merchant panel:
```
https://yoursite.com/api/method/easebuzz_integration.utils.webhook
```

## 🎯 Usage

### Basic Payment Integration

```python
# In your custom script or app
from easebuzz_integration.utils import create_payment_request

# Create payment request
payment_request = create_payment_request({
    "amount": 1000.00,
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "customer_phone": "9876543210",
    "reference_doctype": "Sales Order",
    "reference_docname": "SO-2024-001"
})

# Get payment URL
payment_url = payment_request.get_payment_url()
```

### Sales Order Integration

1. Create a Sales Order
2. Click **Create > Payment Request**
3. Select **Easebuzz** as Payment Gateway
4. Customer receives email with payment link

### Direct API Usage

```python
from easebuzz_integration.easebuzz_client import EasebuzzClient

client = EasebuzzClient()

# Initiate payment
response = client.initiate_payment({
    "txnid": "TXN001",
    "amount": "100.00",
    "productinfo": "Test Product",
    "firstname": "John",
    "email": "john@example.com",
    "phone": "9876543210"
})
```

## 🔌 API Reference

### Payment Methods

#### `create_payment_request(data)`
Creates a new payment request.

**Parameters:**
- `amount` (float): Payment amount
- `customer_name` (str): Customer name
- `customer_email` (str): Customer email
- `customer_phone` (str): Customer phone number
- `reference_doctype` (str): Reference document type
- `reference_docname` (str): Reference document name

#### `process_webhook(data)`
Processes webhook notifications from Easebuzz.

### Custom Fields Created

The app automatically creates the following custom fields:

**Sales Order:**
- `easebuzz_payment_request` (Link to Payment Request)
- `easebuzz_payment_status` (Select)

**Sales Invoice:**
- `easebuzz_transaction_id` (Data)
- `easebuzz_payment_mode` (Data)

## 🧪 Testing

### Running Tests

```bash
# Run all tests
bench --site your-site-name run-tests easebuzz_integration

# Run specific test
bench --site your-site-name run-tests easebuzz_integration.tests.test_payment
```

### Test Data

Use the following test credentials in sandbox mode:

**Test Card:**
- Card Number: `4111111111111111`
- CVV: `123`
- Expiry: Any future date

**Test UPI:**
- UPI ID: `test@upi`

## 🛠️ Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/easebuzz_integration.git
cd easebuzz_integration

# Create development branch
git checkout -b develop

# Install in development mode
bench --site your-site-name install-app easebuzz_integration --dev
```

### Project Structure

```
easebuzz_integration/
├── easebuzz_integration/
│   ├── easebuzz_integration/
│   │   ├── doctype/          # Custom DocTypes
│   │   ├── utils/            # Utility functions
│   │   └── api/              # API endpoints
│   ├── fixtures/             # Initial data
│   ├── patches/              # Database patches
│   └── public/               # Static files
├── tests/                    # Test files
├── requirements.txt          # Python dependencies
└── hooks.py                  # App hooks
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Add tests** for your changes
5. **Run tests** to ensure everything works
6. **Commit your changes**
   ```bash
   git commit -m 'Add some amazing feature'
   ```
7. **Push to your branch**
   ```bash
   git push origin feature/amazing-feature
   ```
8. **Open a Pull Request**

### Coding Standards

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Write tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Issues & Support

### Reporting Issues

If you encounter any issues, please:

1. Check existing [GitHub Issues](https://github.com/yourusername/easebuzz_integration/issues)
2. Create a new issue with:
   - Detailed description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (Frappe version, Python version, etc.)

### Getting Help

- **Documentation**: Check this README and inline code documentation
- **Community**: Join our [Discuss Forum](https://discuss.frappe.io/)
- **Email**: support@unityedu.ai

## 📈 Roadmap

- [ ] Support for EMI payments
- [ ] Recurring payment subscriptions
- [ ] Enhanced fraud detection
- [ ] Multi-currency support
- [ ] Payment analytics dashboard
- [ ] Mobile SDK integration

## 🙏 Acknowledgments

- Frappe Technologies for the amazing framework
- Easebuzz for their robust payment gateway
- All contributors who have helped improve this integration

**Made with ❤️ by [Unity]**
