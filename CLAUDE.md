# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**easebuzz** is a payment gateway integration app that provides EaseBuzz payment processing capabilities for Frappe applications, specifically designed for handling online payments and settlement logging.

## Architecture

### Core Components

1. **Payment Gateway Integration**
   - EaseBuzz API integration for payment processing
   - Settlement logging and tracking
   - Web form payment override functionality

2. **Key DocTypes**
   - `Easebuzz Settlement Log` - Payment settlement tracking and processing
   - Custom Web Form override for payment workflows

## Key Commands

### Development
```bash
# Start development server
bench start

# Build app
bench build --app easebuzz

# Install app on site
bench --site [site_name] install-app easebuzz
```

### Testing
```bash
# Run app tests
bench --site [site_name] run-tests --app easebuzz

# Run specific test modules
bench --site [site_name] run-tests --module easebuzz.tests.test_easebuzz_settlement_log
```

### Database Operations
```bash
# Apply migrations
bench --site [site_name] migrate

# Access database console
bench --site [site_name] mariadb
```

## Key Integration Points

### DocType Overrides
- **Web Form**: Custom payment web form functionality via `easebuzz.overrides.payment_webform.CustomPaymentWebForm`

### Document Events
- **Easebuzz Settlement Log**: Processes settlement logs on save via `process_log` function

## Development Patterns

### Payment Processing Pattern
The app provides integration with EaseBuzz payment gateway:
- Payment initiation and processing
- Settlement reconciliation
- Transaction logging and tracking
- Error handling and status updates

### Web Form Integration
Custom web form override enables:
- Seamless payment form integration
- Payment gateway redirection
- Response handling and confirmation
- Error management

## Payment Gateway Features

### EaseBuzz Integration
- Secure payment processing
- Multiple payment methods support
- Real-time transaction status
- Webhook handling for payment notifications

### Settlement Management
- Automated settlement logging
- Reconciliation with payment records
- Settlement status tracking
- Financial reporting integration

## Security Considerations

### Payment Security
- Secure API communication with EaseBuzz
- Transaction data encryption
- PCI DSS compliance considerations
- Audit logging for payment activities

### Data Protection
- Secure storage of payment logs
- Access control for financial data
- Privacy protection for customer information

## Dependencies

### Required
- **Frappe Framework**: Core dependency
- **EaseBuzz API**: Payment gateway services

### Integration
- **ERPNext**: Financial document integration
- **Custom Apps**: Payment processing for educational institutions

## Performance Considerations

### Transaction Processing
- Efficient payment processing workflows
- Optimized database queries for settlement logs
- Proper error handling and retry mechanisms

### Logging
- Structured logging for debugging
- Performance monitoring
- Transaction audit trails

## Integration with Other Apps

### Educational Apps
- Supports fee payment processing for education apps
- Integrates with student fee management
- Provides payment confirmation workflows

### ERPNext Integration
- Seamless integration with accounting modules
- Payment entry creation and reconciliation
- Financial reporting integration