"""
Centralized fee type definitions for TAMRIS.

Both Payment.payment_type and FeeConfiguration.fee_type use these same codes.
This is the single source of truth.
"""

# ─── All fee types (used by both Payment and FeeConfiguration) ───────────────

FEE_TYPES = [
    # Listing of Traditional Medicines
    ('LISTING_APP_FEE', 'Listing of Traditional Medicines: 1. Ada ya maombi (Application fee)'),
    ('LISTING_EVAL_FEE', 'Listing of Traditional Medicines: 2. Ada ya tathmini (Evaluation fee)'),
    ('LISTING_FEE', 'Listing of Traditional Medicines: 3. Ada ya uorodheshaji (Listing fee)'),
    ('LISTING_RENEWAL_FEE', 'Listing of Traditional Medicines: 4. Ada ya kuhuisha (Renewal fee)'),
    ('LISTING_AMENDMENT_FEE', 'Listing of Traditional Medicines: 5. Ada ya marekebisho (Amendment fee)'),

    # Registration of Category II Traditional Medicines
    ('CAT_II_APP_FEE', 'Registration of Category II Traditional Medicines: 1. Ada ya maombi (Application fee)'),
    ('CAT_II_EVAL_FEE', 'Registration of Category II Traditional Medicines: 2. Ada ya tathmini (Evaluation fee)'),
    ('CAT_II_INSPECTION_FEE', 'Registration of Category II Traditional Medicines: 3. Ada ya ukaguzi wa uzalishaji (Manufacturing inspection fee)'),
    ('CAT_II_REGISTRATION_FEE', 'Registration of Category II Traditional Medicines: 4. Ada ya usajili (Registration fee)'),
    ('CAT_II_RENEWAL_FEE', 'Registration of Category II Traditional Medicines: 5. Ada ya kuhuisha (Renewal fee)'),
    ('CAT_II_AMENDMENT_FEE', 'Registration of Category II Traditional Medicines: 6. Ada ya marekebisho (Amendment fee)'),
]

# ─── Helper lookups ──────────────────────────────────────────────────────────

LISTING_FEE_CODES = [code for code, _ in FEE_TYPES if code.startswith('LISTING_')]
CAT_II_FEE_CODES = [code for code, _ in FEE_TYPES if code.startswith('CAT_II_')]

# Default amounts (TZS) used when seeding the database
DEFAULT_AMOUNTS = {
    'LISTING_APP_FEE': 0.00,
    'LISTING_EVAL_FEE': 0.00,
    'LISTING_FEE': 0.00,
    'LISTING_RENEWAL_FEE': 0.00,
    'LISTING_AMENDMENT_FEE': 0.00,

    'CAT_II_APP_FEE': 0.00,
    'CAT_II_EVAL_FEE': 0.00,
    'CAT_II_INSPECTION_FEE': 0.00,
    'CAT_II_REGISTRATION_FEE': 0.00,
    'CAT_II_RENEWAL_FEE': 0.00,
    'CAT_II_AMENDMENT_FEE': 0.00,
}
