# Mu Booking (Party Booking App)

**Mu Booking** is a custom Frappe application designed to streamline the process of managing party and event bookings. It handles everything from initial booking requests (including AI Bot integrations) to asset management, recurring sessions, and financial returns.

## 🚀 Key Features

* **Bot Integration API**: A dedicated API endpoint (`create_bot_booking`) allowing AI bots or external systems to seamlessly create draft bookings while enforcing validation and preventing duplicates.
* **Recurring Bookings**: Support for recurring booking patterns (e.g., Daily sessions) with automatic scheduling and sequence generation.
* **Asset Management**: 
  * Book specific assets for events.
  * Automatically manage asset availability and statuses (Available, Booked, Damaged).
  * Prevent double-booking of assets on the same date.
* **Asset Return & Financials**: 
  * Handle the return of party assets.
  * Calculate deductions for lost or damaged items.
  * Validate refund amounts against original security deposits.
* **Robust Validation**: Extensive business logic to ensure data integrity (e.g., past dates rejection, proper mobile formatting, zero-day recurring prevention).
* **Comprehensive Reporting**: Includes custom reports for Security Deposits and Damaged/Lost Assets.

## 🛠️ Installation

1. Switch to your bench directory:
   ```bash
   cd frappe-bench
   ```
2. Get the app (if not already installed):
   ```bash
   bench get-app https://github.com/Mubtkir-ERP/Mu-Booking.git
   ```
3. Install the app on your site:
   ```bash
   bench --site [your-site-name] install-app mu_booking
   ```

## 🧪 Testing

The app comes with a comprehensive test suite (Unit and Integration tests) that can be run to ensure all business logic and edge cases are handled correctly:
```bash
bench --site [your-site-name] execute mu_booking.run_tests.run_all_tests
```

## 🛡️ License

MIT License.
