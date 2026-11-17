# SUPR menu import report

Updated: 2026-11-14. Source files are retained in `docs/menu-sources/` for review. Product images were not derived from the menu boards; listings use the app's generic food placeholder until item photographs are supplied.

| Vendor | Source | Extracted/imported product records | Selectable price variants | Publicly published | Manual review |
|---|---|---:|---:|---:|---|
| Kolkata's Lazeez | Two-page `LAZZEZ.pdf`, plus the supplied momo menu photo | 128 (127 PDF items + Momos) | 138 (114 PDF size/portion prices + 24 momo preparation/filling combinations) | 0 | Spring Roll shows one ₹100 price under half/full headings with an ellipsis; serving size is unclear. Preserve spellings printed in the PDF, including `Patato`, `Singal`, `Schzwan`, `Mayonise`, and `Schzwan Saus`, for vendor confirmation. |
| Kathi Junction | Supplied menu photograph | 72 | 2 (Tea has ₹10 and ₹20, but no size labels) | 0 | Soft Drinks is marked `MRP`, with no numeric price. Chilli Chicken has no portion printed. |
| Greenox | [Official takeaway menu](https://greenox.dotpe.in/store/18/takeaway) | 0 | 0 | 0 | JavaScript-only site did not expose products/prices here. Manual capture required. |
| Domino's | [Domino's India website menu](https://www.dominos.co.in/menu), captured 2026-11-17 | 121 | 534 (size · crust combinations for pizzas) | 121 (zero stock) | National website listing with no outlet selected; outlet prices may differ. 24 items carried website promotional prices (regular price kept in the item note). Beverage prices are shown on the website as ₹66.66/₹28.57, which appear to exclude 5% GST. |

## Lazeez momo matrix

The supplied photo confirms the matrix. Prices are ₹70/₹100/₹100 for Steam; ₹80/₹110/₹110 for Fry; ₹110/₹140/₹140 for Kurkure; ₹130/₹160/₹160 for Schezwan, Makhani, Tandoori and Chilli Gravy; and ₹150/₹180/₹180 for Afghani (Veg/Paneer/Chicken respectively). “Schezwan” follows the text supplied with the menu; the photo print is less clear. Variant stock and availability remain off pending vendor confirmation.

## Add-ons, portion sizes, and vendor terms

The PDF's Lazeez roll section lists nine add-ons: Mayonise ₹10, Tandoor Mayonise ₹10, Schzwan Saus ₹10, Amul Butter ₹10, Egg ₹20, Dbl. Egg ₹30, Cheese Spread ₹20, Cheese Slice ₹20, and Wheat Base at no charge. They are attached to Lazeez roll items only and are disabled until current availability is confirmed.

Size and portion labels are represented as product variants: Tandoori Snacks 4/8 pcs; Rice 400/700 ml; Lazeez vegetarian main course Quarter/Half/Full (2/4/6 pcs as printed); non-vegetarian main course Quarter/Half/Full (chicken 1/2/4 pcs and egg 2/4/6 pcs); Chinese and French Fries 400/700 ml. Kathi portion labels and printed 300 ml servings are preserved. Product variants and add-ons are recalculated from database prices at cart and checkout.

Lazeez's PDF prints contact 8432813476, free delivery, and a ₹100 minimum order. The system stores those source notes, while delivery remains off and the minimum is not shown as a confirmed term until the vendor confirms it. Kathi Junction's photo prints order mobile 9211931195 and customer care 70426 80426; delivery/minimum terms are not printed. No hours, address, ratings, current stock, or vendor food photography are inferred.

The live database records admin approval decisions for all four vendor profiles. All 200 imported Lazeez/Kathi menu items are published and visible in the marketplace; they retain zero stock and disabled ordering until vendors confirm availability. Vendors can add, edit, pause, activate, or remove their own listings without admin approval. Admins can also pause, publish, or remove any listing. A reset seed now creates menu items as published with zero stock. Lazeez delivery terms and minimum order stay unconfirmed.

## Domino's website capture

Source: catalogue data embedded in the public page at https://www.dominos.co.in/menu (no store selected), captured 2026-11-17. Generated into `backend/app/dominos_menu.py`; `python -m app.import_dominos` adds it to an existing database without a reset, and `python -m app.seed` includes it on a reset.

- Imported: the 121 items listed in visible menu categories (Veg/Non-Veg Pizza, Cheese Burst, 2in1 Cheese Burst, Cheese Volcano, Cheese Lava, Chicken Feast, Big Big Pizza, Pizza Mania, No Onion No Garlic, Garlic Breads & Dips, Tacos & Parcels, Desserts, Beverages). Pizza size and crust combinations are selectable variants with the price shown on the website.
- Duplicate website names are disambiguated: the Cheese Burst category versions are suffixed `(Cheese Burst)`, and Pizza Mania versions `(Pizza Mania)`.
- Category mapping: pizzas → Fast Food; sides and garlic breads → Snacks and Quick Bites; beverages → Beverages; desserts → Desserts and Sweets.
- Not imported: 40 combos/meal deals (Value Combos, Lunch Feast, 5 Course Meal, Dominoid), which are time-limited, configurable bundles; size-dependent toppings and extra-cheese add-ons; internal items not shown in any menu category; and Domino's product photography.
- All items are published with zero stock and ordering disabled until the Domino's vendor account confirms current outlet prices and availability.
