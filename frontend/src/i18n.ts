// Interface language switch (English / Hindi).
//
// The app's screens are written in English. When Hindi is chosen, this module swaps
// interface text (and placeholder / aria-label / title attributes) for Hindi as it
// appears on screen, and restores the English when switching back. Menu data such as
// dish names, vendor names and descriptions has no entry here, so it is left as is.
// Only text node values are changed (nodes are never replaced), which React tolerates:
// when React writes new text, the observer translates the new value again.

export type Lang = 'en' | 'hi';

const HI: Record<string, string> = {
  // Header and navigation
  'Marketplace': 'मार्केटप्लेस', 'Menu': 'मेन्यू', 'Discover': 'खोजें', 'Vendors': 'विक्रेता', 'How it works': 'यह कैसे काम करता है',
  'Account': 'खाता', 'Help': 'मदद', 'Notifications': 'सूचनाएँ', 'Shopping bag': 'शॉपिंग बैग', 'Open menu': 'मेन्यू खोलें',
  'Your campus, a little closer.': 'आपका कैंपस, थोड़ा और करीब।', 'Made for BMU · Gurugram': 'BMU · गुरुग्राम के लिए बना',
  'BMU CAMPUS MARKET': 'BMU कैंपस मार्केट', 'Change language': 'भाषा बदलें',
  // Home
  'GOOD FOOD, RIGHT AROUND YOU': 'अच्छा खाना, आपके आस-पास', 'Campus life,': 'कैंपस की ज़िंदगी,', 'well fed.': 'भरपेट।',
  'From your favourite chai to a satisfying meal between classes. Discover the food spots around BMU, all in one place.':
    'पसंदीदा चाय से लेकर क्लास के बीच भरपेट खाने तक। BMU के आस-पास की खाने की जगहें, सब एक ही जगह।',
  'Explore food': 'खाना देखें', 'Join the marketplace': 'मार्केटप्लेस से जुड़ें', 'Made for the BMU community': 'BMU समुदाय के लिए बना',
  'Good finds, good neighbours.': 'अच्छी चीज़ें, अच्छे पड़ोसी।', 'NEAR CAMPUS, MADE WITH CARE': 'कैंपस के पास, प्यार से बना',
  'The neighbourhood edit': 'पड़ोस की ख़ास पसंद', 'A little bit of everything': 'हर चीज़ थोड़ी-थोड़ी',
  'Thoughtfully picked for campus': 'कैंपस के लिए सोच-समझकर चुना', 'Campus friendly': 'कैंपस के अनुकूल',
  'Delivery options shown upfront': 'डिलीवरी विकल्प पहले से दिखाए जाते हैं', 'Vetted local partners': 'जाँचे-परखे स्थानीय साझेदार',
  'Clear campus delivery info': 'कैंपस डिलीवरी की साफ़ जानकारी', 'A more local way to shop': 'ख़रीदारी का ज़्यादा स्थानीय तरीका',
  'Local food spots': 'स्थानीय खाने की जगहें', 'Discover food vendors around BMU': 'BMU के आस-पास के खाद्य विक्रेता खोजें',
  'Delivery, made clear': 'डिलीवरी, साफ़-साफ़', 'Know if they deliver to campus': 'जानें कि वे कैंपस तक डिलीवरी करते हैं या नहीं',
  'Vetted vendors': 'जाँचे-परखे विक्रेता', 'Food vendors are reviewed by BMU': 'खाद्य विक्रेताओं की समीक्षा BMU करता है',
  'Easy ordering': 'आसान ऑर्डर', 'Easy to place. Easy to follow.': 'ऑर्डर करना आसान, ट्रैक करना आसान।',
  'BMU CAMPUS MARKET · NOW OPEN': 'BMU कैंपस मार्केट · अब खुला है',
  // About Supr
  'ABOUT SUPR': 'Supr के बारे में', 'A campus market, made for BMU.': 'BMU के लिए बना एक कैंपस मार्केट।',
  'Supr brings the food spots around BMU into one place. Students browse real menus, see straight away whether a vendor delivers to campus, and send an order request in a few taps.':
    'Supr, BMU के आस-पास की खाने की जगहों को एक साथ लाता है। छात्र असली मेन्यू देखते हैं, तुरंत जान लेते हैं कि विक्रेता कैंपस तक डिलीवरी करता है या नहीं, और कुछ ही टैप में ऑर्डर अनुरोध भेज देते हैं।',
  'Every vendor applies first and is reviewed by BMU before their menu goes live. Orders are requests: the vendor confirms them, keeps you updated step by step, and payment is arranged directly with them.':
    'हर विक्रेता पहले आवेदन करता है और मेन्यू लाइव होने से पहले BMU उसकी समीक्षा करता है। ऑर्डर अनुरोध होते हैं: विक्रेता उनकी पुष्टि करता है, आपको हर कदम की जानकारी देता है, और भुगतान सीधे उन्हीं से होता है।',
  'Reviewed by BMU': 'BMU द्वारा समीक्षित', 'Only approved vendors appear, and BMU can pause any listing.': 'केवल स्वीकृत विक्रेता दिखते हैं, और BMU किसी भी लिस्टिंग को रोक सकता है।',
  'Delivery, stated upfront': 'डिलीवरी, पहले से बताई गई', 'Each vendor says whether they deliver to campus and to which gates.': 'हर विक्रेता बताता है कि वह कैंपस तक और किन गेटों तक डिलीवरी करता है।',
  'Track every order': 'हर ऑर्डर ट्रैक करें', 'Follow your order from placed to delivered, right on Supr.': 'ऑर्डर देने से डिलीवरी तक, सब Supr पर ही देखें।',
  'Good for local shops': 'स्थानीय दुकानों के लिए अच्छा', 'Neighbourhood vendors reach the BMU community without extra fees.': 'पड़ोस के विक्रेता बिना अतिरिक्त शुल्क के BMU समुदाय तक पहुँचते हैं।',
  'approved vendors': 'स्वीकृत विक्रेता', 'dishes on the menu': 'मेन्यू में व्यंजन', 'deliver to campus': 'कैंपस तक डिलीवरी करते हैं',
  // Discover
  'DISCOVER': 'खोजें', 'Discover food around BMU.': 'BMU के आस-पास खाना खोजें।',
  'Browse by kind of food, or start with a few local favourites.': 'खाने के प्रकार से देखें, या कुछ स्थानीय पसंदीदा से शुरू करें।',
  'A GOOD PLACE TO START': 'शुरुआत के लिए अच्छी जगह', 'Find your kind of food.': 'अपनी पसंद का खाना खोजें।', 'Explore all food': 'सारा खाना देखें',
  'Good food around BMU': 'BMU के आस-पास अच्छा खाना', 'A FEW LOCAL FAVOURITES': 'कुछ स्थानीय पसंदीदा',
  'Good food is closer than you think.': 'अच्छा खाना जितना सोचते हैं उससे ज़्यादा पास है।',
  'Fresh picks from approved food vendors near BMU.': 'BMU के पास के स्वीकृत विक्रेताओं के चुनिंदा व्यंजन।',
  // Food categories (fixed list)
  'Bakery and Confectionery': 'बेकरी और कन्फ़ेक्शनरी', 'Beverages': 'पेय पदार्थ', 'Combos and Special Offers': 'कॉम्बो और विशेष ऑफ़र',
  'Desserts and Sweets': 'मिठाइयाँ और डेज़र्ट', 'Fast Food': 'फ़ास्ट फ़ूड', 'Healthy Food': 'सेहतमंद खाना',
  'Meals and Main Course': 'भोजन और मुख्य व्यंजन', 'Snacks and Quick Bites': 'नाश्ता और झटपट खाना',
  // Laptop and phone shops
  'Listed shop, not on Supr yet': 'सूचीबद्ध दुकान, अभी Supr पर नहीं', 'Visit or call': 'जाएँ या कॉल करें', 'Listed price:': 'सूचीबद्ध दाम:', 'Veg & non-veg options': 'शाकाहारी और मांसाहारी विकल्प', 'Sign in to order and track food': 'ऑर्डर करने और ट्रैक करने के लिए साइन इन करें', 'My orders': 'मेरे ऑर्डर', 'Try:': 'आज़माएँ:', 'Screen': 'स्क्रीन', 'Battery': 'बैटरी', 'Motherboard': 'मदरबोर्ड', 'Data recovery': 'डेटा रिकवरी', 'Refurbished': 'रीफ़र्बिश्ड', 'Phone repair': 'फ़ोन रिपेयर', 'Clear search': 'खोज साफ़ करें', 'Searching…': 'खोज रहे हैं…', 'Show all services': 'सभी सेवाएँ दिखाएँ', 'Try a shorter word, or clear the search to see everything.': 'छोटा शब्द आज़माएँ, या सब कुछ देखने के लिए खोज साफ़ करें।',
  'FOOD AND TECH, RIGHT AROUND YOU': 'खाना और टेक, आपके आस-पास', 'well fed & well fixed.': 'भरपेट और ठीक-ठाक।',
  'From chai between classes to a laptop that will not start. Find food spots and repair shops around BMU, all in one place.': 'क्लास के बीच की चाय से लेकर न चलने वाले लैपटॉप तक। BMU के आस-पास खाने की जगहें और रिपेयर की दुकानें, सब एक ही जगह।',
  'BMU Campus, Sidhrawali': 'BMU कैंपस, सिधरावली', 'Search for a food spot, dish or repair shop': 'खाने की जगह, व्यंजन या रिपेयर की दुकान खोजें',
  'Laptop & phone help': 'लैपटॉप और फ़ोन सहायता', 'Laptops & phones': 'लैपटॉप और फ़ोन', 'Food': 'खाना', 'Filter shops': 'दुकानें फ़िल्टर करें',
  'Food delivery and pickup near BMU': 'BMU के पास खाने की डिलीवरी और पिकअप', 'Laptop and phone help near BMU': 'BMU के पास लैपटॉप और फ़ोन सहायता',
  'Delivering to BMU Campus': 'BMU कैंपस तक डिलीवरी', 'Food and tech near BMU Campus': 'BMU कैंपस के पास खाना और टेक',
  'Looking for something specific?': 'कुछ ख़ास ढूँढ रहे हैं?', 'Search in laptop & phone help': 'लैपटॉप और फ़ोन सहायता में खोजें',
  'Not on Supr yet': 'अभी Supr पर नहीं', 'Pickup from shop': 'दुकान से पिकअप', 'No shops match': 'कोई दुकान नहीं मिली',
  'Try another word, or clear the filter.': 'कोई और शब्द आज़माएँ, या फ़िल्टर हटाएँ।', 'Show all shops': 'सभी दुकानें दिखाएँ', 'items': 'आइटम', 'item': 'आइटम', 'services': 'सेवाएँ', 'service': 'सेवा',
  'Supr brings the food spots and repair shops around BMU into one place. Browse real menus, see whether a shop delivers to campus, and send an order request in a few taps.': 'Supr, BMU के आस-पास की खाने की जगहों और रिपेयर की दुकानों को एक साथ लाता है। असली मेन्यू देखें, जानें कि दुकान कैंपस तक डिलीवरी करती है या नहीं, और कुछ ही टैप में ऑर्डर अनुरोध भेजें।',
  'Vendors apply first, and BMU reviews them before their menu goes live.': 'विक्रेता पहले आवेदन करते हैं, और मेन्यू लाइव होने से पहले BMU उनकी समीक्षा करता है।',
  'Follow your order step by step, from placed to delivered.': 'ऑर्डर देने से डिलीवरी तक, हर कदम पर अपना ऑर्डर देखें।', 'laptop & phone shops': 'लैपटॉप और फ़ोन की दुकानें',
  'Laptop and phone shops are listed from public information and have not joined Supr yet, so contact them directly.': 'लैपटॉप और फ़ोन की दुकानें सार्वजनिक जानकारी से सूचीबद्ध हैं और अभी Supr से नहीं जुड़ी हैं, इसलिए सीधे संपर्क करें।',
  'Reset password': 'पासवर्ड रीसेट करें', 'Current password': 'मौजूदा पासवर्ड', 'New password': 'नया पासवर्ड', 'Confirm new password': 'नया पासवर्ड दोबारा लिखें',
  'Enter your current password, then choose a new one of at least 10 characters.': 'अपना मौजूदा पासवर्ड लिखें, फिर कम से कम 10 अक्षरों का नया पासवर्ड चुनें।',
  'The two new passwords do not match.': 'दोनों नए पासवर्ड मेल नहीं खाते।', 'Password changed': 'पासवर्ड बदल दिया गया', 'Current password is incorrect': 'मौजूदा पासवर्ड गलत है',
  'VENDOR ACCOUNT': 'विक्रेता खाता', 'UNIVERSITY ADMIN ACCOUNT': 'विश्वविद्यालय एडमिन खाता', 'Approval history': 'अनुमोदन इतिहास', 'Hide history': 'इतिहास छिपाएँ', 'All vendors': 'सभी विक्रेता', 'Application submitted': 'आवेदन जमा किया गया', 'Approved': 'स्वीकृत', 'Rejected': 'अस्वीकृत', 'Participation stopped': 'भागीदारी रोकी गई', 'Participation restarted': 'भागीदारी फिर शुरू की गई', 'No approval activity recorded yet.': 'अभी तक कोई अनुमोदन गतिविधि दर्ज नहीं है।', 'Clear bag': 'बैग खाली करें', 'Remove all items from your bag?': 'अपने बैग से सभी आइटम हटाएँ?', 'Your bag is empty': 'आपका बैग खाली है', 'Create student account': 'छात्र खाता बनाएँ', 'New to Supr?': 'Supr पर नए हैं?', 'Create a student account': 'छात्र खाता बनाएँ', 'Already have an account?': 'पहले से खाता है?', 'Use your BMU email in the form name.yearcourse@bmu.edu.in, for example dhruv.24cse@bmu.edu.in': 'अपना BMU ईमेल name.yearcourse@bmu.edu.in रूप में लिखें, जैसे dhruv.24cse@bmu.edu.in', 'Students sign up with their BMU email (name.yearcourse@bmu.edu.in). BMU administrators can also create accounts.': 'छात्र अपने BMU ईमेल (name.yearcourse@bmu.edu.in) से साइन अप करते हैं। BMU प्रशासक भी खाते बना सकते हैं।', 'Save new password': 'नया पासवर्ड सहेजें', 'Cancel': 'रद्द करें', 'Show': 'दिखाएँ', 'Hide': 'छिपाएँ', 'Show password': 'पासवर्ड दिखाएँ', 'Hide password': 'पासवर्ड छिपाएँ', 'All campus places': 'कैंपस की सभी जगहें', 'Your sign-in details.': 'आपके साइन-इन विवरण।', 'Sign-in email': 'साइन-इन ईमेल',
  'Tech': 'टेक', 'All': 'सभी', 'Laptop and phone help near BMU.': 'BMU के पास लैपटॉप और फ़ोन सहायता।', 'Laptop and phone help': 'लैपटॉप और फ़ोन सहायता',
  'Repair and gadget shops around campus, listed from public information. These shops have not joined Supr yet, so contact them directly to confirm services, prices and hours.': 'कैंपस के आस-पास की रिपेयर और गैजेट दुकानें, सार्वजनिक जानकारी से सूचीबद्ध। ये दुकानें अभी Supr से नहीं जुड़ी हैं, इसलिए सेवाएँ, दाम और समय की पुष्टि के लिए सीधे संपर्क करें।',
  'Search repairs, laptops or phones': 'रिपेयर, लैपटॉप या फ़ोन खोजें', 'THE SHOPS': 'दुकानें', 'No services match your search.': 'आपकी खोज से कोई सेवा नहीं मिली।',
  'Laptop Repair': 'लैपटॉप रिपेयर', 'Laptops and Accessories': 'लैपटॉप और एक्सेसरीज़', 'Phone Repair': 'फ़ोन रिपेयर', 'Phones and Accessories': 'फ़ोन और एक्सेसरीज़',
  'Repairs and gadgets near BMU': 'BMU के पास रिपेयर और गैजेट', 'Contact shop': 'दुकान से संपर्क करें', 'Price on request': 'पूछने पर दाम', 'Free': 'मुफ़्त', 'Details': 'विवरण',
  'LAPTOPS AND PHONES': 'लैपटॉप और फ़ोन', 'Repair and gadget shops near BMU.': 'BMU के पास रिपेयर और गैजेट की दुकानें।',
  'Listed from public information. These shops have not joined Supr yet, so contact them directly to confirm services, prices and hours.':
    'सार्वजनिक जानकारी से सूचीबद्ध। ये दुकानें अभी Supr से नहीं जुड़ी हैं, इसलिए सेवाएँ, दाम और समय की पुष्टि के लिए सीधे संपर्क करें।',
  'services · Contact directly': 'सेवाएँ · सीधे संपर्क करें', 'LISTED SHOP · NOT ON SUPR YET': 'सूचीबद्ध दुकान · अभी Supr पर नहीं', 'Address:': 'पता:',
  'laptop and phone shops listed': 'लैपटॉप और फ़ोन की दुकानें सूचीबद्ध',
  'We also list nearby laptop and phone repair and sales shops from public information, so you know where to go. They have not joined Supr yet, so contact them directly.':
    'हम आस-पास की लैपटॉप और फ़ोन रिपेयर व बिक्री की दुकानें भी सार्वजनिक जानकारी से दिखाते हैं, ताकि आपको पता रहे कहाँ जाना है। वे अभी Supr से नहीं जुड़ी हैं, इसलिए सीधे संपर्क करें।',
  'Visit the shop to confirm price and availability.': 'दाम और उपलब्धता की पुष्टि के लिए दुकान पर जाएँ।', 'to confirm price and availability.': 'पर कॉल करके दाम और उपलब्धता की पुष्टि करें।', 'Call': 'कॉल करें:',
  'This shop has not joined Supr yet, so it cannot take orders here. Please contact the shop directly.': 'यह दुकान अभी Supr से नहीं जुड़ी है, इसलिए यहाँ ऑर्डर नहीं ले सकती। कृपया सीधे दुकान से संपर्क करें।',
  // Vendors
  'VENDORS': 'विक्रेता', 'The food spots around BMU.': 'BMU के आस-पास खाने की जगहें।',
  'Every vendor here is reviewed by BMU. Open one to see its full menu, prices and delivery options.':
    'यहाँ हर विक्रेता की समीक्षा BMU ने की है। पूरा मेन्यू, दाम और डिलीवरी विकल्प देखने के लिए किसी एक को खोलें।',
  'menu items ·': 'मेन्यू आइटम ·', 'available ·': 'उपलब्ध ·', 'Delivers to BMU': 'BMU तक डिलीवरी', 'Pickup': 'पिकअप',
  'FOR BMU FOOD BUSINESSES': 'BMU के खाद्य व्यवसायों के लिए', 'Have a food business?': 'क्या आपका खाने का व्यवसाय है?',
  'Bring your food to campus.': 'अपना खाना कैंपस तक लाएँ।',
  'Bring your food to the BMU community. Get discovered by students and grow your local customer base.':
    'अपना खाना BMU समुदाय तक पहुँचाएँ। छात्रों तक पहुँचें और अपने स्थानीय ग्राहक बढ़ाएँ।',
  'OPEN': 'खुला', 'YOUR SHOP,': 'आपकी दुकान,', 'ON CAMPUS.': 'कैंपस में।', 'GOOD': 'अच्छी', 'THINGS': 'चीज़ें', 'GROW LOCAL': 'स्थानीय रूप से बढ़ती हैं',
  '← Back to marketplace': '← वापस जाएँ', 'BMU FOOD VENDOR': 'BMU खाद्य विक्रेता', 'Contact:': 'संपर्क:', 'Pickup from vendor': 'विक्रेता से पिकअप',
  // Menu page and cards
  'BMU FOOD, CLOSE BY': 'BMU का खाना, पास में', 'Find your next favourite bite.': 'अपना अगला पसंदीदा व्यंजन खोजें।',
  'Good food from the neighbourhood around BMU.': 'BMU के आस-पड़ोस का अच्छा खाना।', 'Filters': 'फ़िल्टर',
  'Sort: Recommended': 'क्रम: सुझाए गए', 'Price: Low to High': 'दाम: कम से ज़्यादा', 'Price: High to Low': 'दाम: ज़्यादा से कम',
  'Name: A to Z': 'नाम: A से Z', 'Everything': 'सब कुछ', 'Showing': 'दिखाए जा रहे हैं', 'of': 'में से', 'food listings': 'खाद्य आइटम',
  'Load more food': 'और खाना दिखाएँ', 'Search food, category or vendor': 'खाना, श्रेणी या विक्रेता खोजें', 'Sort food': 'खाना क्रमबद्ध करें',
  'Menu section': 'मेन्यू खंड', 'All menu sections': 'सभी मेन्यू खंड', 'In stock': 'स्टॉक में', 'Out of stock': 'स्टॉक में नहीं',
  'Awaiting confirmation': 'पुष्टि की प्रतीक्षा', 'Campus delivery': 'कैंपस डिलीवरी', 'Delivery unconfirmed': 'डिलीवरी की पुष्टि नहीं',
  'Veg': 'शाकाहारी', 'Non-veg': 'मांसाहारी', 'Vegetarian': 'शाकाहारी', 'Non-vegetarian': 'मांसाहारी', 'Vegan': 'वीगन',
  'From': 'शुरुआती', 'Add': 'जोड़ें', 'Options': 'विकल्प', 'Save food to favourites': 'पसंदीदा में सहेजें',
  'Remove from favourites': 'पसंदीदा से हटाएँ', 'min': 'मिनट', 'Not specified': 'निर्दिष्ट नहीं', 'Portion': 'मात्रा',
  'Single': 'सिंगल', 'Add to cart': 'कार्ट में जोड़ें', 'Choose a size or variant': 'आकार या प्रकार चुनें', 'Total': 'कुल',
  'Awaiting vendor verification': 'विक्रेता की पुष्टि की प्रतीक्षा',
  // Dialogs: help, how it works, join, sign in
  'How Supr works': 'Supr कैसे काम करता है', 'How can we help?': 'हम आपकी कैसे मदद कर सकते हैं?', 'Got it': 'समझ गए',
  'For students': 'छात्रों के लिए', 'For food vendors': 'खाद्य विक्रेताओं के लिए', 'For University Admin': 'विश्वविद्यालय प्रशासन के लिए',
  'Find local food, check campus delivery, then send an order request. Payment happens with the vendor.':
    'स्थानीय खाना खोजें, कैंपस डिलीवरी देखें, फिर ऑर्डर अनुरोध भेजें। भुगतान विक्रेता के साथ होता है।',
  'Apply with your business details and documents. BMU reviews your application before listings go live.':
    'अपने व्यवसाय के विवरण और दस्तावेज़ों के साथ आवेदन करें। लिस्टिंग लाइव होने से पहले BMU आपके आवेदन की समीक्षा करता है।',
  'Review applications, record agreement checks and manage vendor participation.':
    'आवेदनों की समीक्षा करें, अनुबंध की जाँच दर्ज करें और विक्रेताओं की भागीदारी संभालें।',
  'Orders': 'ऑर्डर',
  'Orders are requests. The vendor updates your order status, and payment is arranged directly with them.':
    'ऑर्डर अनुरोध होते हैं। विक्रेता आपके ऑर्डर की स्थिति अपडेट करता है, और भुगतान सीधे उन्हीं से होता है।',
  'Campus delivery help': 'कैंपस डिलीवरी सहायता',
  'Each food vendor states whether they deliver to BMU. Delivery areas and charges are not set by Supr.':
    'हर खाद्य विक्रेता बताता है कि वह BMU तक डिलीवरी करता है या नहीं। डिलीवरी क्षेत्र और शुल्क Supr तय नहीं करता।',
  'Only approved food vendors and the eight food categories appear in the marketplace.':
    'मार्केटप्लेस में केवल स्वीकृत खाद्य विक्रेता और आठ खाद्य श्रेणियाँ दिखती हैं।',
  'GROW WITH SUPR': 'Supr के साथ आगे बढ़ें', 'Bring your shop to campus.': 'अपनी दुकान कैंपस तक लाएँ।',
  'Start a vendor account and send your business details for BMU review.': 'विक्रेता खाता शुरू करें और BMU की समीक्षा के लिए अपने व्यवसाय का विवरण भेजें।',
  'Business name': 'व्यवसाय का नाम', 'Business email': 'व्यवसाय ईमेल', 'Password': 'पासवर्ड', 'Create vendor account': 'विक्रेता खाता बनाएँ',
  'Vendor application is reviewed by University Admin before listings can go live.': 'लिस्टिंग लाइव होने से पहले विश्वविद्यालय प्रशासन विक्रेता आवेदन की समीक्षा करता है।',
  'WELCOME TO YOUR NEIGHBOURHOOD': 'अपने पड़ोस में आपका स्वागत है', 'Good to see you.': 'आपको देखकर अच्छा लगा।',
  'Sign in to find your new favourite local.': 'अपनी नई पसंदीदा स्थानीय जगह खोजने के लिए साइन इन करें।', 'BMU email': 'BMU ईमेल',
  'Sign in': 'साइन इन करें', 'Student accounts are created by BMU administrators.': 'छात्र खाते BMU प्रशासक बनाते हैं।',
  'Password for all demo accounts: Demo@12345': 'सभी डेमो खातों का पासवर्ड: Demo@12345',
  'Email or password is incorrect': 'ईमेल या पासवर्ड ग़लत है', 'Please sign in to continue': 'जारी रखने के लिए कृपया साइन इन करें',
  // Footer
  'THE MARKET': 'मार्केट', 'Browse the menu': 'मेन्यू देखें', 'Our vendors': 'हमारे विक्रेता', 'For local vendors': 'स्थानीय विक्रेताओं के लिए',
  'GOOD TO KNOW': 'जानने योग्य', 'Made for the BMU community,': 'BMU समुदाय के लिए बना,', 'with love for the local ones.': 'स्थानीय लोगों के प्यार के साथ।',
  'GURUGRAM, INDIA · EST. 2026': 'गुरुग्राम, भारत · स्थापना 2026', '© 2026 Supr · BMU Campus Market': '© 2026 Supr · BMU कैंपस मार्केट',
  'Built around the neighbourhood.': 'पड़ोस के इर्द-गिर्द बना।', 'Privacy · Terms · Help': 'गोपनीयता · शर्तें · मदद',
  // Student workspace
  'Hi,': 'नमस्ते,', 'Overview': 'अवलोकन', 'Favourites': 'पसंदीदा', 'Your orders': 'आपके ऑर्डर', 'Order history': 'ऑर्डर इतिहास',
  'My profile': 'मेरी प्रोफ़ाइल', 'Sign out': 'साइन आउट', 'YOUR BMU MARKET': 'आपका BMU मार्केट',
  'Your campus orders and food finds.': 'आपके कैंपस ऑर्डर और खाने की खोजें।', 'Your BMU market is ready.': 'आपका BMU मार्केट तैयार है।',
  'Browse approved neighbourhood food vendors and delivery options.': 'पड़ोस के स्वीकृत खाद्य विक्रेता और डिलीवरी विकल्प देखें।',
  'Browse the marketplace': 'मार्केटप्लेस देखें', 'View your bag': 'अपना बैग देखें', 'Recent orders': 'हाल के ऑर्डर',
  'Published menus': 'प्रकाशित मेन्यू', 'Browse full menu': 'पूरा मेन्यू देखें', 'Total orders': 'कुल ऑर्डर', 'Pending': 'लंबित',
  'Completed': 'पूर्ण', 'Your order history': 'आपका ऑर्डर इतिहास', 'Your favourites': 'आपके पसंदीदा', 'No favourites yet': 'अभी कोई पसंदीदा नहीं',
  'Tap the heart on any menu item to save it here.': 'किसी भी मेन्यू आइटम को यहाँ सहेजने के लिए दिल पर टैप करें।',
  'No past orders yet': 'अभी कोई पुराना ऑर्डर नहीं', 'Completed, cancelled and declined orders will appear here.': 'पूरे, रद्द और अस्वीकार किए गए ऑर्डर यहाँ दिखेंगे।',
  'Nothing on the way right now': 'अभी कुछ भी रास्ते में नहीं है', 'No orders in progress': 'कोई ऑर्डर जारी नहीं',
  'When you place an order, you can follow it here step by step.': 'ऑर्डर देने पर आप उसे यहाँ कदम-दर-कदम देख सकते हैं।',
  'Cancel request': 'अनुरोध रद्द करें', 'Order placed': 'ऑर्डर दिया गया', 'Accepted': 'स्वीकार किया गया', 'Being prepared': 'तैयार हो रहा है',
  'Packed': 'पैक हो गया', 'Ready for pickup': 'पिकअप के लिए तैयार', 'On the way': 'रास्ते में', 'At campus gate': 'कैंपस गेट पर',
  'At hostel gate': 'हॉस्टल गेट पर', 'Delivered': 'डिलीवर हो गया', 'Collected': 'ले लिया गया', 'Cancelled': 'रद्द', 'Not accepted': 'स्वीकार नहीं हुआ',
  'Packed, leaving soon': 'पैक, जल्द निकलेगा', 'BMU STUDENT ACCOUNT': 'BMU छात्र खाता',
  'Your account and campus contact details.': 'आपका खाता और कैंपस संपर्क विवरण।', 'Active student': 'सक्रिय छात्र',
  'University email': 'विश्वविद्यालय ईमेल', 'Phone number': 'फ़ोन नंबर', 'Save phone number': 'फ़ोन नंबर सहेजें',
  'Enter your phone number': 'अपना फ़ोन नंबर दर्ज करें', 'YOUR UPDATES': 'आपके अपडेट', 'Welcome to Supr': 'Supr में आपका स्वागत है',
  'A good bite, made simple.': 'अच्छा खाना, आसान तरीके से।', 'Saved to your favourites': 'आपके पसंदीदा में सहेजा गया',
  'Removed from your favourites': 'पसंदीदा से हटाया गया', 'Order history (': 'ऑर्डर इतिहास (',
  // Bag and checkout
  'YOUR BAG': 'आपका बैग', 'A little something.': 'कुछ ख़ास।', 'Your bag is waiting for a good find.': 'आपका बैग किसी अच्छी चीज़ का इंतज़ार कर रहा है।',
  'Review order': 'ऑर्डर देखें', 'Back to cart': 'कार्ट पर वापस जाएँ', 'Subtotal': 'उप-योग', 'Campus pickup': 'कैंपस पिकअप',
  'No online payment is collected.': 'कोई ऑनलाइन भुगतान नहीं लिया जाता।', 'each': 'प्रति नग',
  'This vendor does not offer campus delivery. Please arrange pickup.': 'यह विक्रेता कैंपस डिलीवरी नहीं देता। कृपया पिकअप की व्यवस्था करें।',
  'This vendor offers pickup. Please arrange collection directly.': 'यह विक्रेता पिकअप देता है। कृपया सीधे जाकर ले लें।',
  'View my orders': 'मेरे ऑर्डर देखें', 'ORDER REQUEST SENT': 'ऑर्डर अनुरोध भेजा गया',
};

const STATUS_HI: Record<string, string> = { accepted: 'स्वीकार', rejected: 'अस्वीकार', cancelled: 'रद्द', preparing: 'तैयार हो रहा', ready: 'तैयार', completed: 'पूर्ण', out_for_delivery: 'रास्ते में' };
const GATE_HI: Record<string, string> = { 'college main gate': 'कॉलेज मुख्य गेट', 'hostel gate': 'हॉस्टल गेट' };
const NOTE_HI: Record<string, string> = {
  'the vendor accepted your order.': 'विक्रेता ने आपका ऑर्डर स्वीकार कर लिया।', 'the vendor could not accept your order.': 'विक्रेता आपका ऑर्डर स्वीकार नहीं कर सका।',
  'your order was cancelled.': 'आपका ऑर्डर रद्द हो गया।', 'your food is being prepared.': 'आपका खाना तैयार हो रहा है।', 'your order is ready.': 'आपका ऑर्डर तैयार है।',
  'your order is on the way to campus.': 'आपका ऑर्डर कैंपस के रास्ते में है।', 'your order is complete. Enjoy your food!': 'आपका ऑर्डर पूरा हुआ। खाने का आनंद लें!',
};

// Sentences that contain data (names, numbers). Each returns Hindi or undefined.
const PATTERNS: [RegExp, (...m: string[]) => string | undefined][] = [
  [/^(.+) added to your bag$/, (_, x) => `${x} आपके बैग में जोड़ा गया`],
  [/^Cart started with (.+)$/, (_, x) => `${x} के साथ नया कार्ट शुरू हुआ`],
  [/^Good to have you, (.+)\.$/, (_, x) => `आपका स्वागत है, ${x}।`],
  [/^Thanks, (.+)\.$/, (_, x) => `धन्यवाद, ${x}।`],
  [/^Waiting for (.+) to accept your order\.$/, (_, x) => `${x} के ऑर्डर स्वीकार करने की प्रतीक्षा है।`],
  [/^(.+) has accepted your order\.$/, (_, x) => `${x} ने आपका ऑर्डर स्वीकार कर लिया है।`],
  [/^(.+) is preparing your food\.$/, (_, x) => `${x} आपका खाना तैयार कर रहा है।`],
  [/^Ready\. Collect it from (.+)\.$/, (_, x) => `तैयार है। इसे ${x} से ले लें।`],
  [/^Packed and about to leave for (.+)\.$/, (_, x) => `पैक हो गया है और ${x === 'campus' ? 'कैंपस' : x} के लिए निकलने वाला है।`],
  [/^On its way to (.+)\.$/, (_, x) => `${x === 'campus' ? 'कैंपस' : x} के रास्ते में है।`],
  [/^Your order is at the (college main gate|hostel gate)(?: for (.+))?\. Please collect it\.$/, (_, g, x) => `आपका ऑर्डर ${GATE_HI[g]} पर है${x ? ` (${x})` : ''}। कृपया ले लें।`],
  [/^Reached (college main gate|hostel gate)$/, (_, g) => `${GATE_HI[g]} पर पहुँचा`],
  [/^Campus delivery to (.+)$/, (_, x) => `${x} तक कैंपस डिलीवरी`],
  [/^· Deliver to (.+)$/, (_, x) => `· ${x} पर डिलीवरी`],
  [/^(\d+) orders? in progress · updates every 20 seconds$/, (_, n) => `${n} ऑर्डर जारी · हर 20 सेकंड में अपडेट`],
  [/^(\d+) past orders?(?: · ₹([\d.,]+) on completed orders)?$/, (_, n, t) => `${n} पुराने ऑर्डर${t ? ` · पूरे ऑर्डरों पर ₹${t}` : ''}`],
  [/^(\d+) saved items?$/, (_, n) => `${n} सहेजे गए आइटम`],
  [/^From ₹([\d,.]+)$/, (_, n) => `₹${n} से शुरू`],
  [/^Search “(.+)” in the food menu$/, (_, x) => `खाने के मेन्यू में “${x}” खोजें`],
  [/^(\d+) services?$/, (_, n) => `${n} सेवाएँ`],
  [/^(\d+) in progress$/, (_, n) => `${n} जारी`],
  [/^Order #(\d+) is now (\w+)\.$/, (_, n, st) => STATUS_HI[st] ? `ऑर्डर #${n} अब ${STATUS_HI[st]} है।` : undefined],
  [/^Order #(\d+): (.+)$/, (_, n, rest) => NOTE_HI[rest] ? `ऑर्डर #${n}: ${NOTE_HI[rest]}` : undefined],
  [/^View (.+) details$/, (_, x) => `${x} का विवरण देखें`],
  [/^Search (.+) menu$/, (_, x) => `${x} का मेन्यू खोजें`],
  [/^(.+) has not joined Supr yet$/, (_, x) => `${x} अभी Supr से नहीं जुड़ी है`],
  [/^Order status: (.+)$/, (_, x) => `ऑर्डर की स्थिति: ${translate(x) ?? x}`],
  [/^Place order request · (.+)$/, (_, x) => `ऑर्डर अनुरोध भेजें · ${x}`],
];

export function translate(text: string): string | undefined {
  if (HI[text] !== undefined) return HI[text];
  for (const [re, fn] of PATTERNS) { const m = text.match(re); if (m) { const out = fn(...m); if (out) return out; } }
  return undefined;
}

let lang: Lang = 'en';
let observer: MutationObserver | null = null;
const originalText = new WeakMap<Text, string>();   // English value React last wrote
const writtenText = new WeakMap<Text, string>();    // Hindi value we wrote
const ATTRS = ['placeholder', 'aria-label', 'title'] as const;
const originalAttr = new WeakMap<Element, Record<string, string>>();
const writtenAttr = new WeakMap<Element, Record<string, string>>();

function textNode(n: Text) {
  const current = n.nodeValue ?? '';
  if (writtenText.get(n) === current) {           // our own Hindi value is showing
    if (lang === 'hi') return;
    n.nodeValue = originalText.get(n) ?? current; writtenText.delete(n); return;
  }
  originalText.set(n, current);                   // React wrote fresh (English) text
  if (lang !== 'hi') return;
  const key = current.trim(); if (!key) return;
  const hi = translate(key); if (!hi) return;
  const out = current.replace(key, hi); writtenText.set(n, out); n.nodeValue = out;
}

function element(el: Element) {
  const orig = originalAttr.get(el) ?? {}; const wrote = writtenAttr.get(el) ?? {};
  for (const a of ATTRS) {
    const v = el.getAttribute(a); if (v === null) continue;
    if (wrote[a] === v) { if (lang === 'en' && orig[a] !== undefined) { el.setAttribute(a, orig[a]); delete wrote[a]; } continue; }
    orig[a] = v;
    if (lang === 'hi') { const hi = translate(v.trim()); if (hi) { wrote[a] = hi; el.setAttribute(a, hi); } }
  }
  originalAttr.set(el, orig); writtenAttr.set(el, wrote);
}

function walk(root: Node) {
  if (root.nodeType === Node.TEXT_NODE) { textNode(root as Text); return; }
  if (root.nodeType !== Node.ELEMENT_NODE) return;
  const el = root as Element; if (el.closest('[data-no-translate]')) return;
  element(el);
  const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
  let n: Node | null;
  while ((n = w.nextNode())) { if (n.nodeType === Node.TEXT_NODE) textNode(n as Text); else element(n as Element); }
}

export function setLanguage(next: Lang) {
  lang = next;
  document.documentElement.lang = next;
  walk(document.body);
  if (!observer) {
    observer = new MutationObserver(records => {
      for (const r of records) {
        if (r.type === 'characterData') textNode(r.target as Text);
        else if (r.type === 'attributes') element(r.target as Element);
        else r.addedNodes.forEach(walk);
      }
    });
    observer.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: [...ATTRS] });
  }
}

export function savedLanguage(): Lang {
  try { return localStorage.getItem('supr_lang') === 'hi' ? 'hi' : 'en'; } catch { return 'en'; }
}
export function saveLanguage(l: Lang) { try { localStorage.setItem('supr_lang', l); } catch { /* private mode */ } }
