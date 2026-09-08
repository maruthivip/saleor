# SALEOR — PRODUCT REQUIREMENTS DOCUMENT

---

## Document Control

| Field | Value |
|-------|-------|
| **Product** | Saleor Commerce |
| **Repository** | `/Users/marvippa1/Downloads/saleor-main` (downloaded archive; no `.git` present) |
| **Version** | 3.24.0-a.0 (from `pyproject.toml`) |
| **PRD Version** | 1.0 |
| **Analysis Date** | 2026-08-28 |
| **Reconstruction Method** | Forensic reverse engineering from source code, models, GraphQL schema, enums, services, and tests |

> **Note:** This repository was provided as a downloaded archive without a `.git` directory. Version `3.24.0-a.0` is from `pyproject.toml`. All claims in this PRD are supported by evidence from the repository.

---

## 1. Executive Summary

Saleor is an **enterprise-grade, headless, API-first e-commerce platform** built with Python, Django, and GraphQL. It powers complex, high-traffic, multi-channel commerce operations requiring reliability, scalability, and flexible extensibility.

All functionality is exposed through a **single GraphQL API** — there is no server-rendered storefront. Storefronts and dashboards are built externally and connect via the GraphQL interface (`saleor/graphql/schema.graphql`, 38,140 lines).

**Primary Business Problem Solved:** Enable enterprise merchants to operate complex multi-channel, multi-currency, multi-warehouse storefronts with full control over pricing, inventory, promotions, payments, and fulfillment — extensible without core code modification.

**20 Business Capabilities Confirmed:**
1. Product Catalog Management  2. Channel Management  3. Shopping Cart (Checkout)
4. Order Management  5. Payment Orchestration  6. Inventory & Warehouse Management
7. Shipping Management  8. Promotions & Discounts  9. Gift Card Management
10. Tax Management  11. Customer Account Management  12. Staff & Permission Management
13. App & Extension Platform  14. Webhook & Event System  15. Content Management
16. Translations  17. Metadata  18. Data Export  19. Invoice Management
20. Shop Settings & Configuration

---

## 2. Product Vision — Reconstructed from Evidence

| Intent | Evidence |
|--------|---------|
| API-first architecture | `saleor/graphql/schema.graphql` (38,140 lines), all mutations/queries exposed via GraphQL |
| Headless commerce | `README.md`: "Headless and API only" |
| Native multi-channel | Channel FK present in every domain model; `saleor/channel/models.py` |
| Technology-agnostic extensibility | App manifest + webhook architecture: `saleor/app/models.py`, `saleor/webhook/event_types.py` |
| Enterprise-ready | Multi-warehouse, split payments, granted refunds, bulk ops, external reference IDs |

---

## 3. Product Scope

### In Scope (CONFIRMED from repository)
- Product catalog: types, products, variants, attributes, categories, collections, media
- Multi-channel management
- Checkout flow and checkout completion (incl. idempotent re-call handling)
- Order management: draft, confirmed, fulfilled, returned, canceled, expired states
- Payment: legacy gateway plugin flow AND transaction-based app flow (coexisting)
- Inventory, stock, warehouses, preorders, reservations
- Shipping zones and methods (price-based, weight-based, external via App)
- Promotions (catalogue and order type), vouchers, sales
- Gift cards (issuance, redemption, export)
- Tax classes, per-channel TaxConfiguration, external tax app
- Customer accounts, addresses, authentication (JWT + OIDC)
- Staff management, permission groups
- App installation (manifest-based), app tokens, dashboard extensions
- Webhooks: 100+ async event types, 21 synchronous event types
- CMS Pages, Page Types, Navigation Menus
- Translations for all customer-facing entities
- Metadata (public and private) on all major entities
- Product and gift card CSV export (background jobs)
- Invoice request/generation
- Global shop settings

### Partially Evidenced
- Observability / telemetry (MANAGE_OBSERVABILITY permission, `observability-reporter` Celery task, telemetry fields in SiteSettings — internals not fully traced)
- Email notifications (plugins present: user_email, admin_email, SendGrid; specific templates not fully reviewed)
- PostgreSQL full-text search (GIN indexes on search_vector fields confirmed; query resolution details partially reviewed)

### Undetermined from Repository Evidence
- Storefront/dashboard UI behavior (separate repositories not present)
- Braintree, Razorpay payment gateway behavior details (marked deprecated)
- AvaTax integration behavior details (plugin marked deprecated, not deeply analyzed)

---

## 4. Actors

| Actor ID | Name | Type | Auth Mechanism |
|----------|------|------|----------------|
| ACT-001 | Customer | Human | JWT (tokenCreate), OIDC (externalObtainAccessTokens) |
| ACT-002 | Staff User | Human | JWT, OIDC |
| ACT-003 | Third-Party App | System | App bearer token |
| ACT-004 | Local App | System | App bearer token |
| ACT-005 | Anonymous User | Human | None |
| ACT-006 | Payment App/Gateway | System | Webhook JWS/HMAC |
| ACT-007 | Tax App | System | Webhook JWS |
| ACT-008 | Background Worker | System | Internal (Celery) |

**Evidence:** `saleor/account/models.py`, `saleor/app/models.py`, `saleor/settings.py` (JWT TTL settings), `saleor/plugins/openid_connect/plugin.py`

---

## 5. Business Capabilities

### CAP-001 — Product Catalog Management
**Purpose:** Define and manage product catalog structures — types, attributes, products, variants, categories, collections, and their per-channel publication.

**Confirmed Features:**
- ProductType: name, slug, is_shipping_required, weight, tax_class, kind (NORMAL | GIFT_CARD)
- Attribute types: dropdown, multi-select, text, numeric, swatch, boolean, date, date-time, rich-text, file, reference
- Product: name, EditorJS description, SEO title/description, slug, weight, external_reference, category
- Per-channel ProductChannelListing: is_published, published_at, available_for_purchase_at, visible_in_listings
- ProductVariant: SKU, external_reference, weight, per-channel pricing (ProductVariantChannelListing)
- Category: MPTT hierarchy, unlimited depth, slug (unique), SEO fields, background image
- Collection: name, slug, per-channel publication, SEO fields, background image
- Product media (images)
- Full-text search (PostgreSQL GIN index on search_vector)

**Evidence:** `saleor/product/models.py`, `saleor/attribute/models/`, `saleor/graphql/product/mutations/`

---

### CAP-002 — Channel Management
**Purpose:** Isolate commerce operations by sales channel, each with its own currency, country, inventory strategy, payment flow, and order behavior.

**Confirmed Features:**
- Channel: slug (unique), name, currency_code, default_country, is_active
- AllocationStrategy: PRIORITIZE_SORTING_ORDER | PRIORITIZE_HIGH_STOCK
- MarkAsPaidStrategy: TRANSACTION_FLOW | PAYMENT_FLOW
- TransactionFlowStrategy: AUTHORIZATION | CHARGE
- automatically_confirm_all_new_orders (boolean)
- allow_unpaid_orders (boolean)
- automatically_complete_fully_paid_checkouts (boolean) + automatic_completion_delay
- expire_orders_after (minutes)
- delete_expired_orders_after (days)
- draft_order_line_price_freeze_period (hours)
- release_funds_for_expired_checkouts (boolean)
- automatically_fulfill_non_shippable_gift_card (boolean)

**Evidence:** `saleor/channel/models.py`, `saleor/channel/__init__.py`

---

### CAP-003 — Shopping Cart (Checkout)
**Purpose:** Stateful shopping session for assembling items, configuring delivery, applying promotions, and completing purchase.

**Confirmed Mutations:** checkoutCreate, checkoutLinesAdd, checkoutLinesUpdate, checkoutLinesDelete, checkoutLineDelete, checkoutShippingAddressUpdate, checkoutBillingAddressUpdate, checkoutDeliveryMethodUpdate, checkoutShippingMethodUpdate, checkoutAddPromoCode, checkoutRemovePromoCode, checkoutEmailUpdate, checkoutCustomerNote Update, checkoutLanguageCodeUpdate, checkoutCustomerAttach, checkoutCustomerDetach, checkoutDelete, checkoutComplete, checkoutCreateFromOrder

**Checkout Charge Status:** NONE | PARTIAL | FULL | OVERCHARGED
**Checkout Authorize Status:** NONE | PARTIAL | FULL

**Evidence:** `saleor/checkout/models.py`, `saleor/checkout/__init__.py`, `saleor/graphql/checkout/mutations/`, `saleor/checkout/complete_checkout.py`

---

### CAP-004 — Order Management
**Purpose:** Full lifecycle management of orders from creation through fulfillment, return, and cancellation.

**Order Status:** DRAFT → UNCONFIRMED | UNFULFILLED → PARTIALLY_FULFILLED → FULFILLED → PARTIALLY_RETURNED | RETURNED | CANCELED | EXPIRED

**Order Origin:** CHECKOUT | DRAFT | REUSE | BULK_CREATE

**Fulfillment Status:** WAITING_FOR_APPROVAL | FULFILLED | RETURNED | REFUNDED | REFUNDED_AND_RETURNED | REPLACED | CANCELED

**Confirmed Mutations:** draftOrderCreate, draftOrderUpdate, draftOrderComplete, draftOrderDelete, orderConfirm, orderFulfill, fulfillmentApprove, fulfillmentCancel, fulfillmentUpdateTracking, fulfillmentRefundProducts, fulfillmentReturnProducts, orderCancel, orderUpdate, orderUpdateShipping, orderDiscountAdd, orderDiscountUpdate, orderDiscountDelete, orderLineDelete, orderLineUpdate, orderLinesCreate, orderLineDiscountUpdate, orderLineDiscountRemove, orderMarkAsPaid, orderCapture, orderRefund, orderVoid, orderNoteAdd, orderNoteUpdate, orderGrantRefundCreate, orderGrantRefundUpdate

**Evidence:** `saleor/order/__init__.py`, `saleor/order/models.py`, `saleor/graphql/order/mutations/`

---

### CAP-005 — Payment Orchestration
**Purpose:** Two coexisting payment flows — legacy gateway plugins and modern transaction-based app flows.

**Legacy Payment ChargeStatus:** NOT_CHARGED | PARTIALLY_CHARGED | FULLY_CHARGED | PARTIALLY_REFUNDED | FULLY_REFUNDED | REFUSED | CANCELLED

**TransactionItem Event Types (CONFIRMED):**
- Authorization: AUTHORIZATION_REQUEST, AUTHORIZATION_SUCCESS, AUTHORIZATION_FAILURE, AUTHORIZATION_ADJUSTMENT, AUTHORIZATION_ACTION_REQUIRED
- Charge: CHARGE_REQUEST, CHARGE_SUCCESS, CHARGE_FAILURE, CHARGE_ACTION_REQUIRED, CHARGE_BACK
- Refund: REFUND_REQUEST, REFUND_SUCCESS, REFUND_FAILURE, REFUND_REVERSE
- Cancel: CANCEL_REQUEST, CANCEL_SUCCESS, CANCEL_FAILURE
- Other: INFO

**Order ChargeStatus:** NONE | PARTIAL | FULL | OVERCHARGED
**Order AuthorizeStatus:** NONE | PARTIAL | FULL

**Sync Webhook Payment Events:** PAYMENT_LIST_GATEWAYS, PAYMENT_AUTHORIZE, PAYMENT_CAPTURE, PAYMENT_REFUND, PAYMENT_VOID, PAYMENT_CONFIRM, PAYMENT_PROCESS, TRANSACTION_CHARGE_REQUESTED, TRANSACTION_REFUND_REQUESTED, TRANSACTION_CANCELATION_REQUESTED, PAYMENT_GATEWAY_INITIALIZE_SESSION, TRANSACTION_INITIALIZE_SESSION, TRANSACTION_PROCESS_SESSION, LIST_STORED_PAYMENT_METHODS, STORED_PAYMENT_METHOD_DELETE_REQUESTED, PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION_SESSION, PAYMENT_METHOD_INITIALIZE_TOKENIZATION_SESSION, PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION

**Evidence:** `saleor/payment/models.py`, `saleor/payment/__init__.py`, `saleor/webhook/event_types.py`

---

### CAP-006 — Inventory & Warehouse Management
**Purpose:** Track physical stock across multiple warehouses, support preorders, and enable click-and-collect.

**Confirmed Features:**
- Warehouse: name, address, email, external_reference, click_and_collect_option
- WarehouseClickAndCollectOption: DISABLED | LOCAL_STOCK | ALL_WAREHOUSES
- Stock: per-variant per-warehouse quantity + quantity_allocated
- Reservation: quantity_reserved per Stock per checkout (with expiry)
- Preorder: PreorderAllocation per variant channel listing
- Allocation: quantity per OrderLine per Stock

**Evidence:** `saleor/warehouse/__init__.py`, `saleor/warehouse/models.py`

---

### CAP-007 — Shipping Management
**Purpose:** Configure shipping options by country, order value, and weight with external app extension.

**Confirmed Features:**
- ShippingZone: name, countries (multi-country), default (boolean), channels M2M
- ShippingMethodType: PRICE_BASED | WEIGHT_BASED
- ShippingMethod: min/max price or weight, tax class, excluded products
- ShippingMethodChannelListing: per-channel price + min/max order price
- PostalCodeRuleInclusionType: INCLUDE | EXCLUDE
- External shipping via SHIPPING_LIST_METHODS_FOR_CHECKOUT sync webhook
- Filtering via CHECKOUT_FILTER_SHIPPING_METHODS and ORDER_FILTER_SHIPPING_METHODS

**Evidence:** `saleor/shipping/models.py`, `saleor/shipping/__init__.py`, `saleor/webhook/event_types.py`

---

### CAP-008 — Promotions & Discounts
**Purpose:** Flexible discounts at catalogue (product pricing) and order level.

**DiscountValueType:** FIXED | PERCENTAGE
**DiscountType:** SALE | PROMOTION | ORDER_PROMOTION | VOUCHER | MANUAL
**VoucherType:** SHIPPING | ENTIRE_ORDER | SPECIFIC_PRODUCT
**PromotionType:** CATALOGUE | ORDER
**RewardType:** SUBTOTAL_DISCOUNT | GIFT
**RewardValueType:** FIXED | PERCENTAGE

**PromotionEvents:** PROMOTION_CREATED, PROMOTION_UPDATED, PROMOTION_STARTED, PROMOTION_ENDED, RULE_CREATED, RULE_UPDATED, RULE_DELETED

**Evidence:** `saleor/discount/__init__.py`, `saleor/discount/models.py`, `saleor/graphql/discount/mutations/`

---

### CAP-009 — Gift Card Management
**Purpose:** Issue, track, and redeem monetary gift cards as a payment method.

**Confirmed Features:**
- GiftCard: code (8–16 chars, unique), is_active, expiry_date, currency, initial_balance, current_balance
- GiftCardTag: for categorization/filtering
- Used-by tracking (user FK + email)
- App-created gift cards
- Link to fulfillment_line (for non-shippable fulfillment)
- Full-text search (PostgreSQL GIN)

**Evidence:** `saleor/giftcard/models.py`, `saleor/giftcard/__init__.py`

---

### CAP-010 — Tax Management
**Purpose:** Per-channel tax calculation via flat rates or external tax app.

**TaxCalculationStrategy:** FLAT_RATES | TAX_APP (in `saleor/tax/__init__.py`)

**TaxConfiguration fields (per channel):**
- charge_taxes (bool), tax_calculation_strategy, display_gross_prices, prices_entered_with_tax, tax_app_id, use_weighted_tax_for_shipping

**TaxConfigurationPerCountry:** per-country overrides per channel

**TaxClass:** name + country rates (TaxClassCountryRate with country + rate decimal)
- unique_country_tax_class constraint
- unique_country_without_tax_class constraint (for default rates)

**Evidence:** `saleor/tax/models.py`, `saleor/tax/__init__.py`, `saleor/webhook/event_types.py`

---

### CAP-011 — Customer Account Management
**Purpose:** Full customer account lifecycle — registration, authentication, profile, addresses, order history.

**Confirmed Mutations:** accountRegister, confirmAccount, accountUpdate, accountDelete, accountRequestDeletion, accountAddressCreate, accountAddressUpdate, accountAddressDelete, accountSetDefaultAddress, requestEmailChange, confirmEmailChange, requestPasswordReset, setPassword, passwordChange, tokenCreate, tokenRefresh, tokenVerify, deactivateAllUserTokens, externalAuthenticationUrl, externalObtainAccessTokens, externalRefresh, externalVerify, externalLogout, sendConfirmationEmail

**Evidence:** `saleor/graphql/account/mutations/account/`, `saleor/graphql/account/mutations/authentication/`

---

### CAP-012 — Staff & Permission Management
**Purpose:** Granular domain-level permissions for internal operators organized into reusable groups.

**Permission Domains (CONFIRMED):**
- AccountPermissions: MANAGE_USERS, MANAGE_STAFF, IMPERSONATE_USER
- AppPermissions: MANAGE_APPS, MANAGE_OBSERVABILITY
- ChannelPermissions: MANAGE_CHANNELS
- CheckoutPermissions: MANAGE_CHECKOUTS, HANDLE_CHECKOUTS, HANDLE_TAXES, MANAGE_TAXES
- DiscountPermissions: MANAGE_DISCOUNTS
- GiftcardPermissions: MANAGE_GIFT_CARD
- MenuPermissions: MANAGE_MENUS
- OrderPermissions: MANAGE_ORDERS, MANAGE_ORDERS_IMPORT
- PagePermissions: MANAGE_PAGES | PageTypePermissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES
- PaymentPermissions: HANDLE_PAYMENTS
- PluginsPermissions: MANAGE_PLUGINS
- ProductPermissions: MANAGE_PRODUCTS | ProductTypePermissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES
- ShippingPermissions: MANAGE_SHIPPING
- SitePermissions: MANAGE_SETTINGS, MANAGE_TRANSLATIONS

**Evidence:** `saleor/permission/enums.py`

---

### CAP-013 — App & Extension Platform
**Purpose:** Extend Saleor via independently deployed applications integrating via webhooks.

**App.type:** LOCAL | THIRDPARTY
**AppExtension:** for dashboard UI integration
**App fields:** name, is_active, identifier, manifest_url, is_installed, app_token, brand

**Evidence:** `saleor/app/models.py`, `saleor/graphql/app/mutations/`

---

### CAP-014 — Webhook & Event System
**Purpose:** Event-driven integration with 100+ async events and 21 synchronous webhook types.

**Webhook Delivery Targets:** HTTP/HTTPS, AWS SQS, Google Cloud PubSub
**Payload Signing:** JWS (default from 3.5+), legacy HMAC secret key (deprecated)
**Delivery Tracking:** PENDING | SUCCESS | FAILED
**Webhook features:** GraphQL subscription queries for payload shaping, custom headers, channel filters

**Evidence:** `saleor/webhook/event_types.py`, `saleor/webhook/models.py`, `saleor/settings.py`

---

### CAP-015 — Content Management
**Purpose:** CMS pages with custom attributes and hierarchical navigation menus.

**Page fields:** slug (unique), title, page_type FK, content (EditorJS SanitizedJSONField), published_at, is_published, SEO fields
**MenuItem:** links to URL | Category | Collection | Page (exactly one)
**MenuItem hierarchy:** MPTT tree
**SiteSettings:** top_menu FK, bottom_menu FK

**Evidence:** `saleor/page/models.py`, `saleor/menu/models.py`

---

### CAP-016 — Translations
**Translatable entities (CONFIRMED):** Categories, Products, ProductVariants, Attributes, AttributeValues, Collections, Pages, MenuItems, ShippingMethods, Promotions, PromotionRules
**Permission required:** MANAGE_TRANSLATIONS

**Evidence:** `saleor/graphql/schema.graphql` (translation mutations), `saleor/core/utils/translations.py`

---

### CAP-017 — Metadata
**Entities with ModelWithMetadata mixin (CONFIRMED):** Product, ProductVariant, Category, Collection, ProductType, Order, OrderLine, Checkout, Payment, TransactionItem, GiftCard, User, App, Warehouse, Channel, ShippingZone, Invoice, Page, Menu, MenuItem, Attribute, AttributeValue, TaxConfiguration, SiteSettings

**Fields:** `metadata` (public JSON), `private_metadata` (private JSON), both with GIN indexes

**Evidence:** `saleor/core/models.py` (ModelWithMetadata class)

---

### CAP-018 — Data Export
**Confirmed:** Product export → CSV (background job, ExportFile model linked to Job), Gift card export → CSV
**Events:** PRODUCT_EXPORT_COMPLETED, GIFT_CARD_EXPORT_COMPLETED async webhooks

**Evidence:** `saleor/csv/models.py`, `saleor/csv/__init__.py`, `saleor/csv/tasks.py`

---

### CAP-019 — Invoice Management
**Invoice fields:** order FK, number (varchar), created (datetime), external_url, invoice_file
**Job status:** PENDING | SUCCESS | FAILURE (inherited from Job model via `saleor/core/models.py`)
**Events:** INVOICE_REQUESTED, INVOICE_DELETED, INVOICE_SENT async webhooks

**Evidence:** `saleor/invoice/models.py`

---

### CAP-020 — Shop Settings & Configuration
**SiteSettings key fields:** header_text, description, top_menu FK, bottom_menu FK, track_inventory_by_default, default_weight_unit, company_address FK, default_mail_sender_name/address, enable_account_confirmation_by_email, allow_login_without_confirmation, password_login_mode, customer_set_password_url, fulfillment_auto_approve, fulfillment_allow_unpaid, preserve_all_address_fields, reserve_stock_duration_anonymous_user, reserve_stock_duration_authenticated_user, limit_quantity_per_checkout (default 50), gift_card_expiry_type/period, refund_reason_reference_type, instance_id, usage_telemetry_reported_at

**Evidence:** `saleor/site/models.py`

---

## 6. Features

| Feature ID | Feature Name | Capability |
|------------|-------------|-----------|
| FEAT-001 | Product Type & Attribute Schema | CAP-001 |
| FEAT-002 | Product Creation & Channel Publication | CAP-001 |
| FEAT-003 | Product Variant Management | CAP-001 |
| FEAT-004 | Category & Collection Management | CAP-001 |
| FEAT-005 | Channel Create & Configure | CAP-002 |
| FEAT-006 | Channel Allocation, Payment & Order Strategies | CAP-002 |
| FEAT-007 | Checkout Lifecycle Management | CAP-003 |
| FEAT-008 | Checkout Completion | CAP-003 |
| FEAT-009 | Draft Order & Order Lifecycle | CAP-004 |
| FEAT-010 | Order Fulfillment & Approval | CAP-004 |
| FEAT-011 | Order Return, Refund & Granted Refunds | CAP-004 |
| FEAT-012 | Legacy Payment Gateway Flow | CAP-005 |
| FEAT-013 | Transaction-Based Payment Flow | CAP-005 |
| FEAT-014 | Stored Payment Method Tokenization | CAP-005 |
| FEAT-015 | Multi-Warehouse Stock Management | CAP-006 |
| FEAT-016 | Stock Reservations | CAP-006 |
| FEAT-017 | Click-and-Collect | CAP-006 |
| FEAT-018 | Shipping Zone & Method Configuration | CAP-007 |
| FEAT-019 | External Shipping via App | CAP-007 |
| FEAT-020 | Catalogue Promotions | CAP-008 |
| FEAT-021 | Order Promotions | CAP-008 |
| FEAT-022 | Voucher Management | CAP-008 |
| FEAT-023 | Gift Card Issuance & Redemption | CAP-009 |
| FEAT-024 | Tax Class Configuration | CAP-010 |
| FEAT-025 | External Tax App Integration | CAP-010 |
| FEAT-026 | Customer Registration & Authentication | CAP-011 |
| FEAT-027 | External OIDC Authentication | CAP-011 |
| FEAT-028 | Staff & Permission Group Management | CAP-012 |
| FEAT-029 | App Installation & Token Management | CAP-013 |
| FEAT-030 | Async Webhook Subscription & Delivery | CAP-014 |
| FEAT-031 | Synchronous Webhook Calls | CAP-014 |
| FEAT-032 | CMS Pages | CAP-015 |
| FEAT-033 | Navigation Menus | CAP-015 |
| FEAT-034 | Entity Translations | CAP-016 |
| FEAT-035 | Entity Metadata (Public & Private) | CAP-017 |
| FEAT-036 | Product & Gift Card CSV Export | CAP-018 |
| FEAT-037 | Invoice Request & Generation | CAP-019 |
| FEAT-038 | Global Shop Configuration | CAP-020 |

---

## 7. Functional Requirements

### FR-001 — Product Type Creation
**Actor:** ACT-002 | **Permission:** MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES | **Feature:** FEAT-001
The system SHALL create a ProductType with: name, slug, is_shipping_required, optional weight, optional tax_class FK, and kind (NORMAL | GIFT_CARD). The system SHALL persist the type and make it available for product creation.
**Business Rules:** BR-001

### FR-002 — Attribute Creation & Assignment
**Actor:** ACT-002 | **Permission:** MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES | **Feature:** FEAT-001
The system SHALL create Attributes with configurable input_type (dropdown, multi-select, text, numeric, swatch, boolean, date, date-time, rich-text, file, reference). Attributes SHALL be assignable to ProductTypes (for product or variant-level), or PageTypes.

### FR-003 — Product Creation with Channel Publication
**Actor:** ACT-002 | **Permission:** MANAGE_PRODUCTS | **Feature:** FEAT-002
The system SHALL create a Product with name, description (EditorJS), category FK, SEO title/description, slug, weight, and optional external_reference. Channel publication SHALL be controlled per channel via ProductChannelListing (is_published, published_at, available_for_purchase_at, visible_in_listings).
**Business Rules:** BR-002

### FR-004 — Product Variant Management
**Actor:** ACT-002 | **Permission:** MANAGE_PRODUCTS | **Feature:** FEAT-003
The system SHALL create ProductVariants with optional SKU, external_reference, weight, track_inventory flag, and attribute values. Per-channel pricing SHALL be configured via ProductVariantChannelListing (price, cost_price, preorder_quantity_threshold).

### FR-005 — Category Hierarchy
**Actor:** ACT-002 | **Permission:** MANAGE_PRODUCTS | **Feature:** FEAT-004
The system SHALL support an MPTT category tree of unlimited depth. Categories SHALL have name, slug (globally unique), description, background_image, SEO fields, and optional parent FK.
**Business Rules:** BR-003

### FR-006 — Collection Management
**Actor:** ACT-002 | **Permission:** MANAGE_PRODUCTS | **Feature:** FEAT-004
The system SHALL create Collections with name, slug, per-channel publication (CollectionChannelListing), SEO fields, and background image. Products SHALL be assigned to collections via M2M.

### FR-007 — Channel Creation
**Actor:** ACT-002 | **Permission:** MANAGE_CHANNELS | **Feature:** FEAT-005
The system SHALL create a Channel with unique slug, name, currency_code, default_country, and is_active=False initially.
**Business Rules:** BR-004

### FR-008 — Channel Allocation Strategy
**Actor:** ACT-002 | **Permission:** MANAGE_CHANNELS | **Feature:** FEAT-006
The system SHALL configure AllocationStrategy per channel: PRIORITIZE_SORTING_ORDER or PRIORITIZE_HIGH_STOCK.

### FR-009 — Channel Payment Flow Configuration
**Actor:** ACT-002 | **Permission:** MANAGE_CHANNELS | **Feature:** FEAT-006
The system SHALL configure per channel: default_transaction_flow_strategy (AUTHORIZATION | CHARGE) and mark_as_paid_strategy (TRANSACTION_FLOW | PAYMENT_FLOW).

### FR-010 — Channel Order Behavior Configuration
**Actor:** ACT-002 | **Permission:** MANAGE_CHANNELS | **Feature:** FEAT-006
The system SHALL configure per channel: automatically_confirm_all_new_orders, allow_unpaid_orders, automatically_complete_fully_paid_checkouts, automatic_completion_delay, expire_orders_after, delete_expired_orders_after, draft_order_line_price_freeze_period, release_funds_for_expired_checkouts, automatically_fulfill_non_shippable_gift_card.

### FR-011 — Checkout Creation
**Actor:** ACT-001, ACT-005 | **Feature:** FEAT-007
The system SHALL create a Checkout for a given channel with one or more variant lines and optional customer association. Anonymous checkouts SHALL be supported.
**Preconditions:** Channel active; variants available-for-purchase in channel.
**Business Rules:** BR-005, BR-006, BR-007

### FR-012 — Checkout Line Management
**Actor:** ACT-001, ACT-005 | **Feature:** FEAT-007
The system SHALL support adding, updating quantities of, and deleting checkout lines.

### FR-013 — Checkout Delivery Method Selection
**Actor:** ACT-001 | **Feature:** FEAT-007
The system SHALL allow selecting a delivery method: built-in shipping method, external app shipping method, or click-and-collect warehouse. Available methods SHALL be cached in CheckoutDelivery.
**Business Rules:** BR-008

### FR-014 — Promo Code and Gift Card Application
**Actor:** ACT-001 | **Feature:** FEAT-007
The system SHALL allow applying voucher codes and gift cards to a checkout, validating: code existence, date range, usage limits, channel assignment, minimum spend, minimum quantity, per-customer usage.
**Business Rules:** BR-009, BR-010, BR-011, BR-012

### FR-015 — Checkout Completion
**Actor:** ACT-001, ACT-005 | **Feature:** FEAT-008
The system SHALL complete a checkout by: validating required fields, allocating stock, processing payment, and creating an Order. Re-calling with same token for an already-completed checkout SHALL return the existing order (idempotent).
**Business Rules:** BR-013, BR-014, BR-015, BR-016

### FR-016 — Automatic Checkout Completion
**Actor:** ACT-008 | **Feature:** FEAT-008
When channel setting `automatically_complete_fully_paid_checkouts=True`, the system SHALL automatically complete a fully-paid checkout after `automatic_completion_delay`.

### FR-017 — Order Status Lifecycle
**Actor:** ACT-002 | **Feature:** FEAT-009
The system SHALL enforce Order status transitions among: DRAFT, UNCONFIRMED, UNFULFILLED, PARTIALLY_FULFILLED, FULFILLED, PARTIALLY_RETURNED, RETURNED, CANCELED, EXPIRED.
**Business Rules:** BR-017

### FR-018 — Draft Order Management
**Actor:** ACT-002 | **Permission:** MANAGE_ORDERS | **Feature:** FEAT-009
Staff SHALL create and edit draft orders (lines, addresses, discounts, notes). Placing a draft order SHALL trigger stock allocation and event emission.

### FR-019 — Order Confirmation
**Actor:** ACT-002 | **Feature:** FEAT-009
The system SHALL confirm UNCONFIRMED orders. When `automatically_confirm_all_new_orders=True`, new orders from checkout SHALL auto-confirm.

### FR-020 — Order Fulfillment
**Actor:** ACT-002 | **Permission:** MANAGE_ORDERS | **Feature:** FEAT-010
The system SHALL create Fulfillments grouping order line quantities for shipping from a warehouse. Status flow: WAITING_FOR_APPROVAL → FULFILLED (or direct FULFILLED when auto-approve=True).
**Business Rules:** BR-018

### FR-021 — Fulfillment Return and Refund
**Actor:** ACT-002 | **Permission:** MANAGE_ORDERS | **Feature:** FEAT-011
The system SHALL support returning fulfilled items with optional restock, creating refunds, and tracking replacements.
**Business Rules:** BR-019

### FR-022 — Order Cancellation
**Actor:** ACT-002 | **Permission:** MANAGE_ORDERS | **Feature:** FEAT-009
The system SHALL allow cancellation of non-fulfilled orders. Cancellation SHALL release allocated stock and emit ORDER_CANCELLED.
**Business Rules:** BR-020

### FR-023 — Order Expiry
**Actor:** ACT-008 | **Feature:** FEAT-009
The system SHALL automatically expire orders past their expiry_date (per channel config), transitioning them to EXPIRED status via background task.

### FR-024 — Granted Refund Management
**Actor:** ACT-002 | **Permission:** MANAGE_ORDERS | **Feature:** FEAT-011
The system SHALL allow creating/updating OrderGrantedRefund records with amount, reason, line details, and status (NONE | PENDING | SUCCESS | FAILURE).

### FR-025 — Order Notes & Audit Trail
**Actor:** ACT-002 | **Feature:** FEAT-009
The system SHALL allow adding and updating notes on orders. All significant state changes SHALL be recorded as OrderEvents.

### FR-026 — Legacy Payment Authorization
**Actor:** ACT-006 | **Feature:** FEAT-012
The system SHALL authorize payment via a gateway plugin, creating Payment with ChargeStatus=NOT_CHARGED and Transaction of kind=AUTH.

### FR-027 — Legacy Payment Capture, Refund & Void
**Actor:** ACT-002 | **Feature:** FEAT-012
The system SHALL capture authorized payments, refund (partial or full) captured payments, and void authorized payments.

### FR-028 — Transaction-Based Payment Flow
**Actor:** ACT-006 | **Feature:** FEAT-013
The system SHALL create TransactionItem records tracking authorized_value, charged_value, refunded_value, canceled_value, and pending amounts. TransactionEvents SHALL record lifecycle events.
**Business Rules:** BR-021

### FR-029 — Transaction Action Requests
**Actor:** ACT-002 | **Feature:** FEAT-013
The system SHALL request charge, refund, or cancel on a TransactionItem via TRANSACTION_CHARGE_REQUESTED, TRANSACTION_REFUND_REQUESTED, TRANSACTION_CANCELATION_REQUESTED synchronous webhooks.

### FR-030 — Order Charge & Authorize Status
**Actor:** ACT-008 | **Feature:** FEAT-013
The system SHALL recalculate Order.charge_status and Order.authorize_status whenever TransactionItem events are processed.
**Business Rules:** BR-022, BR-023

### FR-031 — Payment Method Tokenization
**Actor:** ACT-001 | **Feature:** FEAT-014
The system SHALL support storing payment methods via synchronous webhook flows: PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION_SESSION, PAYMENT_METHOD_INITIALIZE_TOKENIZATION_SESSION, PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION.

### FR-032 — Warehouse Creation
**Actor:** ACT-002 | **Permission:** MANAGE_PRODUCTS | **Feature:** FEAT-015
The system SHALL create Warehouses with name, address, email, click_and_collect_option (DISABLED | LOCAL_STOCK | ALL_WAREHOUSES), and optional external_reference.

### FR-033 — Stock Management
**Actor:** ACT-002 | **Feature:** FEAT-015
The system SHALL maintain Stock records per ProductVariant per Warehouse. Available = quantity - quantity_allocated.
**Business Rules:** BR-024

### FR-034 — Stock Reservation
**Actor:** ACT-008 | **Feature:** FEAT-016
When enabled, the system SHALL create Reservations during checkout (duration configurable per auth/anon user). Expired reservations SHALL be released.
**Business Rules:** BR-025

### FR-035 — Click-and-Collect
**Actor:** ACT-001 | **Feature:** FEAT-017
The system SHALL allow customers to select a click-and-collect warehouse when the warehouse option is LOCAL_STOCK or ALL_WAREHOUSES.
**Business Rules:** BR-026

### FR-036 — Shipping Zone Configuration
**Actor:** ACT-002 | **Permission:** MANAGE_SHIPPING | **Feature:** FEAT-018
The system SHALL create ShippingZones covering specified countries, with a default zone for unmatched countries, assigned to channels.

### FR-037 — Shipping Method Configuration
**Actor:** ACT-002 | **Permission:** MANAGE_SHIPPING | **Feature:** FEAT-018
The system SHALL create PRICE_BASED (min/max order price) or WEIGHT_BASED (min/max weight) shipping methods with per-channel pricing.
**Business Rules:** BR-027, BR-028

### FR-038 — Postal Code Rules
**Actor:** ACT-002 | **Feature:** FEAT-018
The system SHALL allow postal code inclusion/exclusion rules on shipping methods.

### FR-039 — Catalogue Promotions
**Actor:** ACT-002 | **Permission:** MANAGE_DISCOUNTS | **Feature:** FEAT-020
The system SHALL create CATALOGUE-type Promotions with rules reducing prices of products/variants/categories/collections by fixed or percentage per channel.
**Business Rules:** BR-029

### FR-040 — Order Promotions
**Actor:** ACT-002 | **Permission:** MANAGE_DISCOUNTS | **Feature:** FEAT-021
The system SHALL create ORDER-type Promotions with rules applying SUBTOTAL_DISCOUNT or GIFT reward to qualifying orders.

### FR-041 — Voucher Management
**Actor:** ACT-002 | **Permission:** MANAGE_DISCOUNTS | **Feature:** FEAT-022
The system SHALL create Vouchers with: type (ENTIRE_ORDER | SHIPPING | SPECIFIC_PRODUCT), discount_value_type (FIXED | PERCENTAGE), usage_limit, start_date, end_date, min_spent, min_checkout_items_quantity, countries, apply_once_per_customer, apply_once_per_order, single_use. Multiple codes per voucher SHALL be supported.
**Business Rules:** BR-009, BR-010, BR-011, BR-012

### FR-042 — Gift Card Creation
**Actor:** ACT-002 | **Permission:** MANAGE_GIFT_CARD | **Feature:** FEAT-023
The system SHALL create Gift Cards with code (8–16 chars, unique, indexed), is_active, currency, initial_balance, optional expiry_date, optional tags.
**Business Rules:** BR-030

### FR-043 — Gift Card Redemption
**Actor:** ACT-001 | **Feature:** FEAT-023
The system SHALL allow applying active, non-expired gift cards with sufficient balance to checkout. Balance SHALL decrement on order placement.
**Business Rules:** BR-031, BR-032

### FR-044 — Tax Class Configuration
**Actor:** ACT-002 | **Permission:** MANAGE_TAXES | **Feature:** FEAT-024
The system SHALL create named TaxClasses with per-country rates (TaxClassCountryRate). A default country rate (tax_class=NULL) SHALL serve as fallback.

### FR-045 — Per-Channel Tax Configuration
**Actor:** ACT-002 | **Permission:** MANAGE_TAXES | **Feature:** FEAT-024
The system SHALL configure per channel: charge_taxes, tax_calculation_strategy (FLAT_RATES | TAX_APP), display_gross_prices, prices_entered_with_tax, tax_app_id, use_weighted_tax_for_shipping. Per-country overrides SHALL be supported.

### FR-046 — External Tax Calculation
**Actor:** ACT-007 | **Feature:** FEAT-025
When tax_calculation_strategy=TAX_APP, the system SHALL call the tax app via CHECKOUT_CALCULATE_TAXES or ORDER_CALCULATE_TAXES synchronous webhook to obtain tax amounts.

### FR-047 — Customer Registration
**Actor:** ACT-005 | **Feature:** FEAT-026
The system SHALL allow new customer registration with email + password. When `enable_account_confirmation_by_email=True`, account SHALL require email confirmation before login.
**Business Rules:** BR-033

### FR-048 — JWT Authentication
**Actor:** ACT-001, ACT-002 | **Feature:** FEAT-026
The system SHALL issue JWT access tokens (TTL: configurable, default 5min) and refresh tokens (TTL: 30 days configurable) via tokenCreate. Token refresh and verification SHALL be supported. All user tokens SHALL be invalidatable via deactivateAllUserTokens.
**Business Rules:** BR-034

### FR-049 — External OIDC Authentication
**Actor:** ACT-001, ACT-002 | **Feature:** FEAT-027
The system SHALL support OIDC authentication via OpenIDConnectPlugin, providing externalAuthenticationUrl → externalObtainAccessTokens flow.

### FR-050 — Customer Address Management
**Actor:** ACT-001 | **Feature:** FEAT-026
The system SHALL allow customers to create, update, and delete multiple addresses, set default billing/shipping addresses. Addresses SHALL be validated against country-specific format rules (google-i18n-address).

### FR-051 — Staff User Management
**Actor:** ACT-002 | **Permission:** MANAGE_STAFF | **Feature:** FEAT-028
The system SHALL allow creating and managing staff users (is_staff=True) with granular permissions via PermissionGroup assignment.

### FR-052 — Permission Group Management
**Actor:** ACT-002 | **Permission:** MANAGE_STAFF | **Feature:** FEAT-028
The system SHALL allow creating named PermissionGroups with permission sets. Staff inherit all group permissions.

### FR-053 — App Installation via Manifest
**Actor:** ACT-002 | **Permission:** MANAGE_APPS | **Feature:** FEAT-029
The system SHALL install third-party apps by fetching and validating an app manifest URL. App SHALL NOT be granted MANAGE_APPS permission.
**Business Rules:** BR-035

### FR-054 — App Token Management
**Actor:** ACT-002, ACT-003 | **Feature:** FEAT-029
The system SHALL create authentication tokens for Apps used as Bearer tokens in API calls.

### FR-055 — Webhook Subscription
**Actor:** ACT-003 | **Permission:** MANAGE_APPS or AUTHENTICATED_APP | **Feature:** FEAT-030
The system SHALL allow Apps to create webhook subscriptions with target URL (HTTP, SQS, or PubSub), GraphQL subscription query, custom headers, and channel filter slugs.
**Business Rules:** BR-036

### FR-056 — Async Webhook Delivery
**Actor:** ACT-008 | **Feature:** FEAT-030
The system SHALL deliver async events via Celery, tracking status (PENDING | SUCCESS | FAILED). Payloads SHALL be JWS-signed. Manual retry SHALL be supported via eventDeliveryRetry.

### FR-057 — Synchronous Webhook Calls
**Actor:** ACT-003, ACT-006, ACT-007 | **Feature:** FEAT-031
The system SHALL invoke 21 synchronous webhook event types during checkout, payment, and shipping operations, processing app responses inline.

### FR-058 — Webhook Dry Run & Trigger
**Actor:** ACT-002 | **Permission:** AUTHENTICATED_STAFF_USER | **Feature:** FEAT-030
The system SHALL support webhookDryRun (payload preview) and webhookTrigger (live delivery) for testing purposes.

### FR-059 — CMS Pages
**Actor:** ACT-002 | **Permission:** MANAGE_PAGES | **Feature:** FEAT-032
The system SHALL allow creating Pages with slug (unique), title, EditorJS content, PageType FK, publication control, SEO fields, and full-text search.

### FR-060 — Navigation Menus
**Actor:** ACT-002 | **Permission:** MANAGE_MENUS | **Feature:** FEAT-033
The system SHALL allow creating hierarchical Menus with MenuItems linking to URL | Category | Collection | Page. Items SHALL support sort ordering.

### FR-061 — Entity Translations
**Actor:** ACT-002 | **Permission:** MANAGE_TRANSLATIONS | **Feature:** FEAT-034
The system SHALL allow translations for all customer-facing entities: Category, Product, ProductVariant, Attribute, AttributeValue, Collection, Page, MenuItem, ShippingMethod, Promotion, PromotionRule.

### FR-062 — Entity Metadata
**Actor:** ACT-002, ACT-003 | **Feature:** FEAT-035
The system SHALL provide public metadata and private metadata (GIN-indexed JSONFields) on all entities inheriting ModelWithMetadata.

### FR-063 — Product & Gift Card Export
**Actor:** ACT-002 | **Permission:** MANAGE_PRODUCTS or MANAGE_GIFT_CARD | **Feature:** FEAT-036
The system SHALL export product or gift card data to CSV via background job (ExportFile/Job model). PRODUCT_EXPORT_COMPLETED and GIFT_CARD_EXPORT_COMPLETED events SHALL be emitted.

### FR-064 — Invoice Management
**Actor:** ACT-002 | **Permission:** MANAGE_ORDERS | **Feature:** FEAT-037
The system SHALL support invoice request (creates background Job), number assignment, date, and optional external_url. INVOICE_REQUESTED, INVOICE_SENT, INVOICE_DELETED events SHALL be emitted.

### FR-065 — Global Shop Configuration
**Actor:** ACT-002 | **Permission:** MANAGE_SETTINGS | **Feature:** FEAT-038
The system SHALL maintain a global SiteSettings entity with configurable shop parameters including company info, email settings, fulfillment behavior, reservation durations, checkout limits, gift card expiry, and password policies.

---

## 8. Business Rules

| BR ID | Rule | Evidence |
|-------|------|---------|
| BR-001 | ProductType.kind must be NORMAL or GIFT_CARD | `saleor/product/models.py` |
| BR-002 | Products visible to customers only when is_published=True and channel is_active=True | `saleor/product/models.py` (ProductChannelListing) |
| BR-003 | Category slug must be globally unique | `saleor/product/models.py` (unique slug) |
| BR-004 | Channel slug must be globally unique | `saleor/channel/models.py` (unique slug) |
| BR-005 | Checkout cannot be created in inactive channel | `saleor/graphql/checkout/mutations/checkout_complete.py` (CHANNEL_INACTIVE error) |
| BR-006 | Total checkout quantity ≤ limit_quantity_per_checkout (default 50) | `saleor/site/models.py` (DEFAULT_LIMIT_QUANTITY_PER_CHECKOUT = 50) |
| BR-007 | Only available-for-purchase variants in the channel may be added to checkout | `saleor/checkout/` (purchasable variant validation) |
| BR-008 | Selected shipping method must be available in the checkout's channel | `saleor/shipping/models.py` (ShippingMethodChannelListing) |
| BR-009 | Voucher code only applicable within start_date to end_date | `saleor/discount/models.py` (Voucher date fields) |
| BR-010 | Voucher with usage_limit may not be used after limit reached | `saleor/discount/models.py` |
| BR-011 | Voucher with min_spent not applicable below minimum order total | `saleor/discount/models.py` |
| BR-012 | Voucher with apply_once_per_customer=True may be used at most once per customer email | `saleor/discount/models.py` |
| BR-013 | Checkout completion requires valid email | `saleor/checkout/checkout_cleaner.py` (validate_checkout_email) |
| BR-014 | When shipping required: shipping address + delivery method required for checkout completion | `saleor/checkout/checkout_cleaner.py` (clean_checkout_shipping) |
| BR-015 | Billing address required for checkout completion | `saleor/checkout/checkout_cleaner.py` (clean_billing_address) |
| BR-016 | Full payment coverage required for checkout completion unless channel allows unpaid orders | `saleor/checkout/checkout_cleaner.py` (clean_checkout_payment) |
| BR-017 | Order status transitions are enforced (DRAFT→UNCONFIRMED/UNFULFILLED, etc.) | `saleor/order/__init__.py` (OrderStatus) |
| BR-018 | Fulfillment quantity per line ≤ unfulfilled quantity on that line | `saleor/graphql/order/mutations/order_fulfill.py` |
| BR-019 | Stock optionally restocked to originating warehouse on return | `saleor/graphql/order/mutations/fulfillment_return_products.py` |
| BR-020 | Order cancellation releases all allocated stock | `saleor/order/actions.py` (cancel_order) |
| BR-021 | TransactionItem requests with same idempotency_key + app do not create duplicate events | `saleor/payment/models.py` (TransactionItem.idempotency_key) |
| BR-022 | Order.charge_status=FULL when sum(charged TransactionItem amounts) = order.total - totalGrantedRefund | `saleor/order/utils.py` (update_order_charge_data) |
| BR-023 | Order.authorize_status=FULL when sum(authorized + charged) ≥ order.total - totalGrantedRefund | `saleor/order/utils.py` (update_order_authorize_data) |
| BR-024 | Available stock = quantity - quantity_allocated; insufficient stock blocks order | `saleor/warehouse/availability.py` |
| BR-025 | Stock reservations expire after configured duration; expired reservations are released | `saleor/warehouse/models.py` (Reservation.reserved_until) |
| BR-026 | For click-and-collect, sufficient stock must exist at selected warehouse | `saleor/warehouse/availability.py` |
| BR-027 | PRICE_BASED shipping applies when order subtotal is within min/max price bounds (channel-specific) | `saleor/shipping/models.py` (_applicable_price_based_methods) |
| BR-028 | WEIGHT_BASED shipping applies when order weight is within min/max weight bounds | `saleor/shipping/models.py` (_applicable_weight_based_methods) |
| BR-029 | Catalogue promotion rules apply only within configured channels | `saleor/discount/models.py` (PromotionRuleChannel M2M) |
| BR-030 | Gift card codes must be 8–16 characters long | `saleor/giftcard/models.py` (MinLengthValidator(8), max_length=16) |
| BR-031 | Only active (is_active=True) and non-expired gift cards may be applied | `saleor/giftcard/models.py` (GiftCardQueryset.active()) |
| BR-032 | Gift card with zero current_balance cannot be applied | `saleor/checkout/checkout_cleaner.py` (_validate_gift_cards) |
| BR-033 | When enable_account_confirmation_by_email=True, new accounts require email confirmation before login (unless allow_login_without_confirmation=True) | `saleor/site/models.py`, `saleor/account/` |
| BR-034 | JWT access tokens expire after JWT_TTL_ACCESS (default 5min). Refresh tokens expire after JWT_TTL_REFRESH (default 30 days) | `saleor/settings.py` |
| BR-035 | Apps may not be granted MANAGE_APPS permission | `saleor/graphql/app/mutations/` |
| BR-036 | Webhook target URLs may not resolve to private/loopback IPs when HTTP_IP_FILTER_ENABLED=True | `saleor/settings.py` |
| BR-037 | Synchronous webhook responses must be received within a configured timeout | `saleor/webhook/transport/synchronous/` |
| BR-038 | Bulk delete mutations limited to BULK_DELETE_LIMIT IDs (default 100) | `saleor/settings.py` |

---

## 9. End-to-End Workflows

### WF-001 — Customer Checkout and Order Placement
**Trigger:** Customer adds item to checkout
1. `checkoutCreate` → channel active check, quantity limit check
2. `checkoutShippingAddressUpdate` → address validated
3. Delivery method candidates fetched (built-in + optional external via sync webhook)
4. `checkoutDeliveryMethodUpdate` → method validated for channel
5. `checkoutBillingAddressUpdate`
6. Optional: `checkoutAddPromoCode`, gift card application
7. Payment: `paymentGatewayInitializeSession` or `transactionInitializeSession` (sync webhook to payment app)
8. `checkoutComplete` → validates: email, addresses, payment coverage
9. System allocates stock (with 45s lock)
10. Order created (UNCONFIRMED or UNFULFILLED)
11. Webhooks emitted: ORDER_CREATED, CHECKOUT_FULLY_PAID, ORDER_CONFIRMED (if auto-confirm)
**Failure paths:** CHANNEL_INACTIVE, INSUFFICIENT_STOCK, EMAIL_NOT_SET, SHIPPING_ADDRESS_NOT_SET, BILLING_ADDRESS_NOT_SET, DELIVERY_METHOD_NOT_APPLICABLE

### WF-002 — Order Fulfillment
**Trigger:** Staff fulfills order
1. `orderFulfill` → validate quantities ≤ unfulfilled
2. System creates Fulfillment (WAITING_FOR_APPROVAL or FULFILLED per auto-approve setting)
3. If WAITING_FOR_APPROVAL: `fulfillmentApprove` required
4. Stock deallocated (transferred from allocated to shipped)
5. Order status → PARTIALLY_FULFILLED or FULFILLED
6. Webhooks: FULFILLMENT_CREATED, FULFILLMENT_APPROVED, ORDER_FULFILLED

### WF-003 — Transaction-Based Payment Processing
**Trigger:** Customer initiates payment
1. `transactionInitializeSession` → TRANSACTION_INITIALIZE_SESSION sync webhook sent to payment app
2. Payment app returns session data
3. Customer completes payment on external UI
4. Payment app calls `transactionEventReport`
5. System creates TransactionEvent (AUTHORIZATION_SUCCESS or CHARGE_SUCCESS)
6. System recalculates checkout/order charge+authorize status
7. If auto-complete enabled and fully paid: checkout auto-completes

### WF-004 — App Installation
**Trigger:** Staff calls `appInstall` with manifest URL
1. Manifest fetched and validated
2. App record created (is_installed=False)
3. Token sent to app callback URL
4. App calls Saleor API to complete installation
5. App marked is_installed=True; webhooks and extensions registered
6. APP_INSTALLED webhook emitted

### WF-005 — Voucher Application at Checkout
**Trigger:** `checkoutAddPromoCode`
1. Code found → validate date range (BR-009)
2. Validate usage_limit (BR-010)
3. Validate channel assignment
4. Validate min_spent (BR-011)
5. Validate per-customer usage (BR-012)
6. Apply voucher; recalculate totals
**Failure:** NOT_APPLICABLE error on each failed validation

---

## 10. State Models

### Order Status
```
─────────────────────────────────────────────────────────────────
 [New] ─────────────────────────────────────────────►  DRAFT
 [Checkout complete, auto-confirm=False] ──────────► UNCONFIRMED
 [Checkout complete, auto-confirm=True]  ──────────► UNFULFILLED
 DRAFT ──[place draft order]──────────────────────► UNFULFILLED/UNCONFIRMED
 UNCONFIRMED ──[confirm]───────────────────────────► UNFULFILLED
 UNFULFILLED ──[fulfill some]──────────────────────► PARTIALLY_FULFILLED
 UNFULFILLED ──[fulfill all]───────────────────────► FULFILLED
 PARTIALLY_FULFILLED ──[fulfill all]───────────────► FULFILLED
 FULFILLED ──[return some]─────────────────────────► PARTIALLY_RETURNED
 FULFILLED ──[return all]──────────────────────────► RETURNED
 PARTIALLY_RETURNED ──[return rest]────────────────► RETURNED
 any ──[staff cancel]──────────────────────────────► CANCELED
 any ──[background expiry task]────────────────────► EXPIRED
```

### Fulfillment Status
```
 [Create, auto_approve=False] ──► WAITING_FOR_APPROVAL ──[approve]──► FULFILLED
 [Create, auto_approve=True]  ──► FULFILLED
 WAITING_FOR_APPROVAL ──[cancel]──────────────────────────────────► CANCELED
 FULFILLED ──[return]────────────────────────────────────────────► RETURNED
 FULFILLED ──[refund]────────────────────────────────────────────► REFUNDED
 FULFILLED ──[return+refund]─────────────────────────────────────► REFUNDED_AND_RETURNED
 FULFILLED ──[replace]───────────────────────────────────────────► REPLACED
 FULFILLED ──[cancel]────────────────────────────────────────────► CANCELED
```

### Payment Legacy ChargeStatus
```
 NOT_CHARGED ──[capture]──► PARTIALLY_CHARGED | FULLY_CHARGED
 FULLY_CHARGED ──[refund partial]──► PARTIALLY_REFUNDED
 FULLY_CHARGED ──[refund full]──────► FULLY_REFUNDED
 NOT_CHARGED ──[void]──────────────► CANCELLED
 [refused]─────────────────────────► REFUSED
```

---

## 11. Webhook Event Catalogue

### Async Events (Confirmed — 100+ total)
Categories: Account, Address, App, Attribute, Category, Channel, Checkout, Collection, Customer, Draft Order, Export, Fulfillment, Gift Card, Invoice, Menu, Order, Page, Permission Group, Product, Product Variant, Promotion, Sale, Shipping, Staff, Tax, Transaction, Translation, Warehouse

Key examples:
- ORDER_CREATED, ORDER_CONFIRMED, ORDER_PAID, ORDER_FULLY_PAID, ORDER_CANCELLED, ORDER_EXPIRED, ORDER_FULFILLED
- CHECKOUT_CREATED, CHECKOUT_UPDATED, CHECKOUT_FULLY_AUTHORIZED, CHECKOUT_FULLY_PAID
- PRODUCT_VARIANT_OUT_OF_STOCK, PRODUCT_VARIANT_BACK_IN_STOCK, PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL
- FULFILLMENT_CREATED, FULFILLMENT_APPROVED, FULFILLMENT_CANCELED
- TRANSACTION_ITEM_METADATA_UPDATED

### Sync Events (21 confirmed)
| Event | Purpose | Permission |
|-------|---------|-----------|
| PAYMENT_LIST_GATEWAYS | List payment gateways | HANDLE_PAYMENTS |
| PAYMENT_AUTHORIZE | Authorize via gateway | HANDLE_PAYMENTS |
| PAYMENT_CAPTURE | Capture via gateway | HANDLE_PAYMENTS |
| PAYMENT_REFUND | Refund via gateway | HANDLE_PAYMENTS |
| PAYMENT_VOID | Void via gateway | HANDLE_PAYMENTS |
| PAYMENT_CONFIRM | Confirm payment | HANDLE_PAYMENTS |
| PAYMENT_PROCESS | Process payment | HANDLE_PAYMENTS |
| CHECKOUT_CALCULATE_TAXES | Tax for checkout | HANDLE_TAXES |
| ORDER_CALCULATE_TAXES | Tax for order | HANDLE_TAXES |
| TRANSACTION_CHARGE_REQUESTED | Request charge | HANDLE_PAYMENTS |
| TRANSACTION_REFUND_REQUESTED | Request refund | HANDLE_PAYMENTS |
| TRANSACTION_CANCELATION_REQUESTED | Request cancel | HANDLE_PAYMENTS |
| SHIPPING_LIST_METHODS_FOR_CHECKOUT | External shipping methods | MANAGE_SHIPPING |
| CHECKOUT_FILTER_SHIPPING_METHODS | Filter shipping | MANAGE_CHECKOUTS |
| ORDER_FILTER_SHIPPING_METHODS | Filter order shipping | MANAGE_ORDERS |
| PAYMENT_GATEWAY_INITIALIZE_SESSION | Init payment session | HANDLE_PAYMENTS |
| TRANSACTION_INITIALIZE_SESSION | Init transaction session | HANDLE_PAYMENTS |
| TRANSACTION_PROCESS_SESSION | Process transaction | HANDLE_PAYMENTS |
| LIST_STORED_PAYMENT_METHODS | List stored methods | HANDLE_PAYMENTS |
| STORED_PAYMENT_METHOD_DELETE_REQUESTED | Delete stored method | HANDLE_PAYMENTS |
| PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION_SESSION | Init tokenization | HANDLE_PAYMENTS |
| PAYMENT_METHOD_INITIALIZE_TOKENIZATION_SESSION | Init method tokenization | HANDLE_PAYMENTS |
| PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION | Process tokenization | HANDLE_PAYMENTS |

**Evidence:** `saleor/webhook/event_types.py`

---

## 12. External Integrations

| ID | Service | Purpose | Status |
|----|---------|---------|--------|
| INT-001 | Stripe | Payment gateway | Active (StripeGatewayPlugin) |
| INT-002 | Braintree | Payment gateway | Deprecated (DeprecatedBraintreeGatewayPlugin) |
| INT-003 | Razorpay | Payment gateway | Deprecated (DeprecatedRazorpayGatewayPlugin) |
| INT-004 | AvaTax | Tax calculation | Deprecated (DeprecatedAvataxPlugin) |
| INT-005 | AWS S3 | Media/export file storage | Active (configured via env) |
| INT-006 | Google Cloud Storage | Media/export file storage | Active (configured via env) |
| INT-007 | Azure Blob Storage | Media/export file storage | Active (configured via env) |
| INT-008 | AWS SQS | Webhook delivery | Active (CELERY_BROKER_URL + sqs://) |
| INT-009 | Google Cloud PubSub | Webhook delivery | Active |
| INT-010 | SendGrid | Email delivery | Deprecated (DeprecatedSendgridEmailPlugin) |
| INT-011 | Redis | Caching + CELERY_RESULT_BACKEND | Active (CACHE_URL / REDIS_URL) |
| INT-012 | OpenID Connect Provider | External authentication | Active (OpenIDConnectPlugin) |
| INT-013 | Celery Broker (RabbitMQ/SQS) | Background tasks | Active (CELERY_BROKER_URL) |
| INT-014 | google-i18n-address | Address validation | Active (library dependency) |

**Evidence:** `saleor/settings.py` (BUILTIN_PLUGINS list), `saleor/payment/gateways/`

---

## 13. Authentication & Authorization Requirements

### Authentication Mechanisms
1. **JWT (Staff + Customer):** tokenCreate → access token (default TTL: 5min) + refresh token (default TTL: 30 days). Settings: `JWT_TTL_ACCESS`, `JWT_TTL_REFRESH`. JWT manager: configurable via `JWT_MANAGER_PATH`.
2. **App Token (Apps):** Static bearer token issued per app. Scoped to app's granted permissions.
3. **OpenID Connect (Staff + Customer):** Via OpenIDConnectPlugin. Configurable: client_id, client_secret, oauth_authorization_url, oauth_token_url, json_web_key_set_url, enable_refresh_token.

### Authorization Model
- Permissions are domain-scoped database Permission objects mapped by `BasePermissionEnum` subclasses.
- Staff users inherit permissions from all assigned PermissionGroups plus direct permissions.
- Apps hold only explicitly granted permissions at installation.
- MANAGE_APPS is blocked from being granted to any App (BR-035).
- Public endpoints (no auth required): product browsing (published only), checkout create, customer registration.

### Webhook Security
- Payloads signed via JWS (from Saleor 3.5+).
- Legacy: HMAC secret key on Webhook model (deprecated as of 3.5).
- Webhook target URLs validated against private IP ranges when `HTTP_IP_FILTER_ENABLED=True`.

---

## 14. Configuration Requirements

| CFG ID | Setting | Default | Evidence |
|--------|---------|---------|---------|
| CFG-001 | JWT_TTL_ACCESS | 5 minutes | `saleor/settings.py` |
| CFG-002 | JWT_TTL_REFRESH | 30 days | `saleor/settings.py` |
| CFG-003 | JWT_TTL_APP_ACCESS | 5 minutes | `saleor/settings.py` |
| CFG-004 | CELERY_BROKER_URL | Empty (eager) | `saleor/settings.py` |
| CFG-005 | CACHE_URL / REDIS_URL | Not set | `saleor/settings.py` |
| CFG-006 | HTTP_IP_FILTER_ENABLED | True | `saleor/settings.py` |
| CFG-007 | RESERVE_DURATION | 45 seconds | `saleor/settings.py` |
| CFG-008 | ALLOWED_HOSTS | localhost, 127.0.0.1 | `saleor/settings.py` |
| CFG-009 | WEBHOOK_CELERY_QUEUE_NAME | None (default) | `saleor/settings.py` |
| CFG-010 | DEFAULT_CURRENCY | USD | `saleor/giftcard/models.py` |
| CFG-011 | Channel.expire_orders_after | None (disabled) | `saleor/channel/models.py` |
| CFG-012 | Channel.automatically_complete_fully_paid_checkouts | False | `saleor/channel/models.py` |
| CFG-013 | SiteSettings.limit_quantity_per_checkout | 50 | `saleor/site/models.py` |
| CFG-014 | SiteSettings.reserve_stock_duration_authenticated_user | None | `saleor/site/models.py` |
| CFG-015 | SiteSettings.reserve_stock_duration_anonymous_user | None | `saleor/site/models.py` |
| CFG-016 | SiteSettings.fulfillment_auto_approve | True | `saleor/site/models.py` |

---

## 15. Non-Functional Requirements

### Security
| NFR-SEC-001 | Public endpoints require no auth: product browse, checkout create, registration |
| NFR-SEC-002 | JWT access tokens are short-lived (default 5min); invalidatable per user |
| NFR-SEC-003 | Webhook payloads are JWS-signed; legacy HMAC also supported |
| NFR-SEC-004 | Webhook URLs validated against private/loopback IP ranges |
| NFR-SEC-005 | Password hashing via Django's configurable backend (AUTH_PASSWORD_VALIDATORS present) |
| NFR-SEC-006 | App token deletion revokes app access |
| NFR-SEC-007 | Private metadata is access-controlled separately from public metadata |
| NFR-SEC-008 | Apps cannot be granted MANAGE_APPS permission |

### Reliability
| NFR-REL-001 | Order creation in traced_atomic_transaction (saleor/core/tracing.py) |
| NFR-REL-002 | Stock allocation uses select_for_update row locking |
| NFR-REL-003 | TransactionItem uses idempotency_key to prevent duplicate processing |
| NFR-REL-004 | Webhook delivery status tracked; manual retry via eventDeliveryRetry |
| NFR-REL-005 | Checkout completion is idempotent (repeated calls return existing order) |
| NFR-REL-006 | Atomic F() expressions used for counter increments |
| NFR-REL-007 | update_or_create with unique constraints for upsert safety |

### Performance
| NFR-PERF-001 | DataLoader pattern for N+1 elimination (dataloaders.py in each GraphQL domain) |
| NFR-PERF-002 | GIN indexes on search_vector (Product, GiftCard, User, Page, Order) |
| NFR-PERF-003 | GIN indexes on metadata fields (all ModelWithMetadata entities) |
| NFR-PERF-004 | Redis caching (configurable TTL, default 7 days) |
| NFR-PERF-005 | Quantitative performance targets not determinable from repository |

### Scalability
| NFR-SCAL-001 | Celery workers scale independently for webhook delivery + data migrations |
| NFR-SCAL-002 | Webhook delivery targets include SQS and PubSub (not just HTTP) |
| NFR-SCAL-003 | Quantitative throughput targets not determinable from repository |

### Internationalization
| NFR-I18N-001 | All customer-facing entities support multilingual translations |
| NFR-I18N-002 | Multi-currency: each channel has exactly one currency code |
| NFR-I18N-003 | International address validation via google-i18n-address |
| NFR-I18N-004 | User and order language codes stored for notification localization |

---

## 16. Validation Requirements

| VAL ID | Field/Context | Condition | Error Code | Evidence File |
|--------|--------------|-----------|-----------|---------------|
| VAL-001 | Checkout.quantity | > limit_quantity_per_checkout | QUANTITY_GREATER_THAN_LIMIT | `saleor/site/models.py` |
| VAL-002 | Checkout.email | Missing at completion | EMAIL_NOT_SET | `saleor/checkout/checkout_cleaner.py` |
| VAL-003 | Checkout.shipping_address | Missing when shipping required | SHIPPING_ADDRESS_NOT_SET | `saleor/checkout/checkout_cleaner.py` |
| VAL-004 | Checkout.delivery_method | Missing when shipping required | DELIVERY_METHOD_NOT_APPLICABLE | `saleor/checkout/checkout_cleaner.py` |
| VAL-005 | Checkout.billing_address | Missing | BILLING_ADDRESS_NOT_SET | `saleor/checkout/checkout_cleaner.py` |
| VAL-006 | Voucher code | Not found | INVALID | `saleor/checkout/checkout_cleaner.py` |
| VAL-007 | Voucher code | Outside date range | NOT_APPLICABLE | `saleor/discount/models.py` |
| VAL-008 | Voucher code | Usage limit exceeded | NOT_APPLICABLE | `saleor/discount/models.py` |
| VAL-009 | Voucher code | Min spend not met | NOT_APPLICABLE | `saleor/discount/models.py` |
| VAL-010 | GiftCard.code | < 8 characters | INVALID | `saleor/giftcard/models.py` |
| VAL-011 | GiftCard | Inactive or expired | INVALID | `saleor/checkout/checkout_cleaner.py` |
| VAL-012 | Stock | Insufficient for order | INSUFFICIENT_STOCK | `saleor/warehouse/availability.py` |
| VAL-013 | Channel | Inactive at checkout complete | CHANNEL_INACTIVE | `saleor/graphql/checkout/mutations/checkout_complete.py` |
| VAL-014 | Webhook URL | Private/loopback IP | INVALID_URL | `saleor/settings.py` (HTTP_IP_FILTER_ENABLED) |
| VAL-015 | App permissions | MANAGE_APPS requested | FORBIDDEN | `saleor/graphql/app/mutations/` |
| VAL-016 | User.email | Not unique | ALREADY_EXISTS | `saleor/account/models.py` |
| VAL-017 | Fulfillment.quantity | > unfulfilled quantity | FULFILL_ORDER_LINES_ERROR | `saleor/graphql/order/mutations/order_fulfill.py` |
| VAL-018 | Address | Invalid country format | INVALID | google-i18n-address library |

---

## 17. Edge Cases

| Edge Case | Behavior | Evidence |
|-----------|---------|---------|
| Checkout completion retry | Returns existing order; no error | `saleor/graphql/checkout/mutations/checkout_complete.py` (get_by_checkout_token) |
| Inactive channel at checkout complete | CHANNEL_INACTIVE error | Same file |
| Concurrent checkout for same stock | select_for_update locking prevents oversell | `saleor/warehouse/availability.py` |
| Gift card zero balance | Not applicable to checkout | `saleor/checkout/checkout_cleaner.py` (_validate_gift_cards) |
| Voucher reuse by same customer | NOT_APPLICABLE (apply_once_per_customer) | `saleor/discount/models.py` |
| Order auto-expiry | Background task → EXPIRED; stock released | `saleor/order/__init__.py` |
| App reinstall | app_identifier matches existing TransactionItems | `saleor/payment/models.py` |
| Delete warehouse with allocated stock | OUT_OF_STOCK webhooks emitted | Schema mutation description |
| Fulfillment approval with auto-approve=False | Waits in WAITING_FOR_APPROVAL | `saleor/order/__init__.py` (FulfillmentStatus) |
| Draft order placement | Triggers stock allocation, event emission | `saleor/graphql/order/mutations/draft_order_complete.py` |

---

## 18. Assumptions

| ID | Assumption | Impact |
|----|-----------|--------|
| A-001 | Repository is complete production codebase | Medium — some plugin behaviors may exist separately |
| A-002 | Dashboard (separate repo) provides staff UI; no UI behavior evidenced here | Low — PRD correctly excludes UI |
| A-003 | Email delivery via plugin system; specific templates not fully reviewed | Medium — email triggers/content not fully captured |
| A-004 | Search powered by PostgreSQL FTS (search_vector GIN indexes confirmed) | Low |

---

## 19. Open Questions

| Q ID | Question | Impact |
|------|---------|--------|
| Q-001 | What is the synchronous webhook response timeout value? | Payment and tax flows |
| Q-002 | Is there full staff-channel access restriction enforcement? | Multi-tenant deployments |
| Q-003 | What exact email templates and triggers exist in user_email/admin_email plugins? | Customer communication |
| Q-004 | What is the full behavior of the AvaTax plugin? | Tax compliance |
| Q-005 | What preorder-specific rules govern checkout and fulfillment? | Physical goods merchants |
| Q-006 | What Celery scheduled tasks run and at what intervals? (CELERY_BEAT_SCHEDULE) | Operations |
| Q-007 | Are there quantitative performance SLAs or benchmarks? | Enterprise contracts |

---

*Document generated from forensic reverse engineering of Saleor v3.24.0-a.0 source code. All claims are backed by specific repository file evidence. Priority rankings are NOT DETERMINABLE from source code and must be assigned by the product team.*
