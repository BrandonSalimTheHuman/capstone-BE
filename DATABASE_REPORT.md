# Capstone Database Report

## 1. Introduction
This database was designed to support a grocery price comparison application. Its job is to keep store information, product details, price records, and shopping lists in a structure that is easy to query and scale as the project grows.

The main goals of the design are:
- let users compare prices between stores
- keep track of changing prices over time
- support practical list-making for shopping
- keep data organized and avoid repetition

## 2. Why The Database Is Designed This Way
The structure follows a simple idea: separate different types of information into clear groups, then connect them through relationships.

This was done for the following reasons:
- Stores and products are kept separately so they can be reused across many price records.
- Prices are stored in their own table so the system can keep many price entries over time, not just one current value.
- Shopping lists are split into parent list, store list, and list items so one user list can be organized by different stores.
- Relationships reduce duplicate data and make updates more reliable.

In short, the design supports both everyday app features (search, compare, checklist) and future analytics (trends, deal tracking).

## 3. Overview Of Main Data Groups
The database contains seven main tables:
- stores
- products
- prices
- price_history
- parent_lists
- store_lists
- store_list_items

Each table has a clear business role:
- stores: where products are sold
- products: what users search and compare
- prices: current and historical recorded prices
- price_history: captures changes between old and new prices
- parent_lists: a user’s main shopping list
- store_lists: a store-specific section inside a parent list
- store_list_items: the actual products and quantities in each store list

## 4. Relationship Summary
The relationships are intentionally straightforward:
- One store can have many prices.
- One product can have many prices.
- One price can have many history records.
- One parent list can have many store lists.
- One store list can have many list items.
- One product can appear in many list items.

This allows users to answer practical questions such as:
- Which store currently has the lowest price for this product?
- How has this product’s price changed over time?
- What should I buy at each store for my shopping plan?

## 5. How This Supports User Features
The database directly supports key app behaviors:
- Product browsing and search
- Price comparison across stores
- Viewing special offers
- Creating and editing shopping lists
- Checking off items while shopping

Because data is split into focused tables, each feature can be built cleanly without mixing unrelated information.

## 6. Strengths Of The Current Design
Current strengths include:
- clear separation of data responsibilities
- strong linking between related records
- support for multi-store and time-based pricing
- shopping list structure that is practical for real users
- scalable base for adding future features

Overall, it is a good fit for a capstone MVP because it balances simplicity with enough depth for real functionality.

## 7. Current Limitations
A few areas can still be improved:
- duplicate product/store entries may still be possible without stronger uniqueness rules
- not all validation rules (for example, non-negative price and quantity) are enforced at database level
- price_history exists but is not yet fully automated in all update flows
- security hardening (such as stricter API access control) can be improved for production

These are normal next-step improvements and do not prevent the current design from working for project demonstration.

## 8. Future Improvements
Recommended next improvements:
- add more database constraints to protect data quality
- fully automate writing price changes to price_history
- add stronger authentication and authorization around user-owned list data
- improve indexing as data volume grows
- introduce formal schema migration workflow for safer releases

## 9. Conclusion
This database is designed to match the project’s real user journey: find products, compare prices, and plan shopping by store.

The design is intentionally modular and relationship-based so that:
- core features are easy to build now
- data stays organized and reusable
- the system can be expanded later without major redesign

In summary, it is an appropriate and practical architecture for a grocery comparison capstone project.
