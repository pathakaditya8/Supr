"""Laptop and phone repair / sales shops near BMU, from public listings (researched 2026-11-17).

These shops have NOT joined Supr. They are added with vendor status "listed": students can see
their services and contact details, but cannot place orders through Supr. Prices are included
only where the shop published one; everything else is "price on request". Each shop gets an
account nobody can sign in to, so no one can act on the shop's behalf until it claims the listing.

Row format for services: (section, name, category, price or None, note)
"""

TECH_CATEGORIES = ["Laptop Repair", "Laptops and Accessories", "Phone Repair", "Phones and Accessories"]

TECH_VENDORS = [
    {
        "name": "Hi-Tech Computer",
        "slug": "hi-tech-computer-bhiwadi",
        "phone": "9672126177",
        "address": "CD 56, Pocket-D, Aravali Vihar, near Nagar Parishad office, Bhiwadi, Rajasthan 301019",
        "about": "Computer and laptop sale, purchase, service, repair and upgrades in Bhiwadi.",
        "sources": ["https://www.hitech-computer.com/", "https://www.sulekha.com/laptop-repair-services/bhiwadi"],
        "services": [
            ("Repairs", "Laptop service and repair", "Laptop Repair", None, ""),
            ("Repairs", "Motherboard repair", "Laptop Repair", None, ""),
            ("Repairs", "Desktop and computer repair", "Laptop Repair", None, ""),
            ("Repairs", "Operating system installation", "Laptop Repair", None, ""),
            ("Repairs", "PC boost and speed enhancement", "Laptop Repair", None, ""),
            ("Repairs", "Mobile service", "Phone Repair", None, ""),
            ("Sales", "Laptop and computer sale and purchase", "Laptops and Accessories", None, "The shop buys and sells laptops and computers."),
            ("Sales", "Printer repair and cartridge refilling", "Laptops and Accessories", None, ""),
        ],
    },
    {
        "name": "Vislor Electronics",
        "slug": "vislor-electronics-manesar",
        "phone": "+91 80476 33117",
        "address": "Plot No 565, Sector 8, IMT Manesar, Gurugram, Haryana 122050",
        "about": "Laptop motherboard repair and laptop hire in IMT Manesar.",
        "sources": ["https://m.indiamart.com/vislor-electronics"],
        "services": [
            ("Repairs", "Laptop motherboard repair", "Laptop Repair", None, ""),
            ("Rentals", "Laptop hire", "Laptops and Accessories", None, ""),
        ],
    },
    {
        "name": "Make My Lappy",
        "slug": "make-my-lappy-gurugram",
        "phone": "+91 98885 45174",
        "address": "Shop No. 323-324, 2nd Floor, Ganpati Arcade, Sadar Bazar, Civil Lines, Gurugram, Haryana 122001. Serves Pataudi with doorstep visits and pickup.",
        "about": "Laptop, MacBook and phone repair with doorstep visits, pickup and drop, and in-store repair. Repairs carry a 3-month service warranty. Hours: Mon to Sat 10 am to 8 pm, Sun 11 am to 6 pm.",
        "sources": ["https://makemylappy.net/laptop-repair/pataudi/"],
        "services": [
            ("Visits", "Free in-store diagnosis", "Laptop Repair", 0, "Diagnosis at the store is free."),
            ("Visits", "Doorstep visit", "Laptop Repair", 500, "The visit charge is adjusted into your bill if you go ahead with the repair."),
            ("Laptop repairs", "Laptop repair", "Laptop Repair", None, "Starts from ₹499 according to the shop's website."),
            ("Laptop repairs", "Laptop screen replacement", "Laptop Repair", None, ""),
            ("Laptop repairs", "Keyboard and trackpad repair", "Laptop Repair", None, ""),
            ("Laptop repairs", "Battery, charging and DC jack repair", "Laptop Repair", None, ""),
            ("Laptop repairs", "Motherboard and chip-level repair", "Laptop Repair", None, ""),
            ("Laptop repairs", "Hinge and body replacement", "Laptop Repair", None, ""),
            ("Laptop repairs", "Slow laptop, virus removal and OS install", "Laptop Repair", None, ""),
            ("Laptop repairs", "Water-damaged laptop repair", "Laptop Repair", None, ""),
            ("Laptop repairs", "MacBook repair", "Laptop Repair", None, ""),
            ("Laptop repairs", "Data recovery", "Laptop Repair", None, ""),
            ("Phone repairs", "Mobile phone repair", "Phone Repair", None, ""),
            ("Phone repairs", "iPhone repair", "Phone Repair", None, ""),
        ],
    },
    {
        "name": "Shivam Mobile & Computers",
        "slug": "shivam-mobile-computers-gurugram",
        "phone": "+91 98719 24083 / +91 99716 03225",
        "address": "Basai Road, Gurugram, Haryana",
        "about": "Phone and computer accessories, refurbished laptops, and laptop, PC, printer and UPS repair, including on-site repair in Gurugram.",
        "sources": ["https://m.indiamart.com/src-computers/aboutus.html"],
        "services": [
            ("Laptops", "Refurbished laptop", "Laptops and Accessories", 17000, "Price per piece as listed by the shop."),
            ("Laptops", "Computer accessories (mice, cables)", "Laptops and Accessories", None, ""),
            ("Repairs", "Laptop and PC repair", "Laptop Repair", None, ""),
            ("Repairs", "On-site PC and laptop repair", "Laptop Repair", None, ""),
            ("Repairs", "Printer repair", "Laptop Repair", None, ""),
            ("Repairs", "UPS repair and rental", "Laptop Repair", None, ""),
            ("Phones", "Mobile display (Samsung J7 Pro combo)", "Phone Repair", 1000, "Price per piece as listed by the shop."),
            ("Phones", "Mobile covers and accessories", "Phones and Accessories", None, ""),
            ("Phones", "Neckband headphones", "Phones and Accessories", None, ""),
        ],
    },
    {
        "name": "AJ Mobile Repairing Hub",
        "slug": "aj-mobile-bilaspur",
        "phone": "",
        "address": "Near Krishna Maruti Terry Shop, Bilaspur, Manesar, Gurugram, Haryana 122413",
        "about": "Mobile phone repair near Bilaspur, close to BMU. Services and prices are not published; visit or ask locally to confirm.",
        "sources": ["https://www.dnb.com/business-directory/company-profiles.aj_mobile_repairing_hub.2bbfd3d162a860dc89e7af5613e3203c.html"],
        "services": [
            ("Repairs", "Mobile phone repair", "Phone Repair", None, ""),
        ],
    },
]

LISTED_NOTE = ("Listed from public information. This shop has not joined Supr yet, so you cannot order here; "
               "contact the shop directly and confirm services, prices and hours before you go.")
