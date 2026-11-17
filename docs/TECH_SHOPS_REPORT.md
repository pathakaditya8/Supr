# Laptop and phone shops near BMU

Researched 2026-11-17. Data in `backend/app/tech_vendors.py`; added to an existing database with `python -m app.import_tech_vendors` (safe to re-run) and included by `python -m app.seed`.

## How these shops are shown

They live on their own **Tech** page (laptop and phone services, category buttons, and the shops), separate from the food Menu, Discover and Vendors pages.

These are real local businesses found in public listings. **None of them has joined Supr.** To avoid misrepresenting them or letting students order from shops that do not know about Supr:

- They have vendor status **`listed`** (new). Students can see them, their services and contact details on the Tech page, which explains that they have not joined Supr.
- **Orders are refused** for listed shops (HTTP 409, "This shop has not joined Supr yet…"). Cards show "Contact shop" and a "Details" button instead of "Add"; the item view shows the shop's phone number instead of "Add to cart".
- No BMU "verified" tick is shown, and About Supr counts only vendors who joined.
- **Prices are shown only where the shop published one.** Everything else is "Price on request".
- Each shop has a disabled placeholder account (`listing+…@supr.invalid`, random unrecorded password), so nobody can sign in as the shop. A shop that wants to join should apply normally; an admin can then replace the listing.

Zomato was not used: its terms prohibit copying listings and menus, and its pages block automated access. Directory pages that block automated reading (D&B) were not fetched; their details come only from search-result summaries and are marked as such.

## Shops

| Shop | Location | Offers | Published prices | Source |
|---|---|---|---|---|
| Hi-Tech Computer | CD 56, Pocket-D, Aravali Vihar, Bhiwadi 301019 · 9672126177 | Laptop and computer sale, purchase, service, repair; motherboard repair; OS install; speed-up; mobile service; printer repair | none | [shop website](https://www.hitech-computer.com/), [Sulekha listing](https://www.sulekha.com/laptop-repair-services/bhiwadi) |
| Vislor Electronics | Plot 565, Sector 8, IMT Manesar 122050 · +91 80476 33117 | Laptop motherboard repair, laptop hire | none | [IndiaMART](https://m.indiamart.com/vislor-electronics) |
| Make My Lappy | Sadar Bazar, Gurugram 122001; serves Pataudi · +91 98885 45174 | Laptop, MacBook and phone repair; doorstep visit, pickup, in-store | Free in-store diagnosis; doorstep visit ₹500 (adjusted into the bill); laptop repair "from ₹499" (kept in the description, not as a fixed price) | [shop website](https://makemylappy.net/laptop-repair/pataudi/) |
| Shivam Mobile & Computers | Basai Road, Gurugram · +91 98719 24083 / +91 99716 03225 | Refurbished laptops, accessories, laptop/PC/printer/UPS repair, phone displays and accessories | Refurbished laptop ₹17,000; mobile display (Samsung J7 Pro combo) ₹1,000 | [IndiaMART](https://m.indiamart.com/src-computers/aboutus.html) |
| AJ Mobile Repairing Hub | Near Krishna Maruti Terry Shop, Bilaspur, Manesar 122413 (BMU's PIN) | Mobile phone repair | none | D&B directory (search-result summary only) |

34 service listings in total (Chaudhary Mobile Centre was removed on request on 2026-11-17), in four new categories: Laptop Repair, Laptops and Accessories, Phone Repair, Phones and Accessories.

## To confirm with each shop

Current address and hours, which services and products they actually offer, prices, whether they would deliver to or visit BMU, and whether they want to join Supr. Listings can be out of date; AJ Mobile Repairing Hub in particular is based only on a directory summary.

## Images

Hi-Tech Computer and Make My Lappy show their logos, taken from their own websites (see `backend/app/vendor_images.py`). Vislor Electronics, Shivam Mobile & Computers and AJ Mobile Repairing Hub have no website of their own, so they keep a name tile rather than an image copied from a directory.
