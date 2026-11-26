"""Farm choices; other crops can be entered directly in the app."""

DISTRICTS = [
    'Mandya', 'Bagalkote', 'Ballari', 'Belagavi', 'Bengaluru Rural', 'Bengaluru Urban',
    'Bengaluru South', 'Bidar', 'Chamarajanagar', 'Chikkaballapur', 'Chikkamagaluru',
    'Chitradurga', 'Dakshina Kannada', 'Davanagere', 'Dharwad', 'Gadag', 'Hassan',
    'Haveri', 'Kalaburagi', 'Kodagu', 'Kolar', 'Koppal', 'Mysuru', 'Raichur',
    'Shivamogga', 'Tumakuru', 'Udupi', 'Uttara Kannada', 'Vijayapura', 'Vijayanagara', 'Yadgir',
]

# Kannada and Hindi names share this locale-aware alphabetical order. The order
# was generated with Unicode/ICU collation rather than sorting Unicode code points.
_INDIC_DISTRICT_ORDER = [
    'Udupi', 'Uttara Kannada', 'Kalaburagi', 'Kodagu', 'Koppal', 'Kolar', 'Gadag',
    'Chamarajanagar', 'Chikkaballapur', 'Chikkamagaluru', 'Chitradurga', 'Tumakuru',
    'Dakshina Kannada', 'Davanagere', 'Dharwad', 'Ballari', 'Bagalkote', 'Bidar',
    'Bengaluru Rural', 'Bengaluru South', 'Bengaluru Urban', 'Belagavi', 'Mandya',
    'Mysuru', 'Yadgir', 'Raichur', 'Vijayanagara', 'Vijayapura', 'Shivamogga',
    'Haveri', 'Hassan',
]


def districts_for_language(language):
    if language in ('Kannada', 'Hindi'):
        return list(_INDIC_DISTRICT_ORDER)
    return sorted(DISTRICTS, key=str.casefold)


CROPS = [
    'Tomato', 'Rice', 'Ragi', 'Sugarcane', 'Cotton', 'Maize',
    'Sorghum (Jowar)', 'Pearl millet (Bajra)', 'Foxtail millet', 'Little millet',
    'Kodo millet', 'Barnyard millet', 'Proso millet', 'Wheat', 'Barley',
    'Pigeon pea (Tur)', 'Chickpea (Bengal gram)', 'Green gram', 'Black gram',
    'Horse gram', 'Cowpea', 'Field bean', 'Lentil', 'Groundnut', 'Sunflower',
    'Sesame', 'Safflower', 'Soybean', 'Castor', 'Niger', 'Mustard',
    'Coconut', 'Arecanut', 'Coffee', 'Tea', 'Cashew', 'Rubber', 'Cocoa',
    'Banana', 'Mango', 'Grapes', 'Pomegranate', 'Papaya', 'Guava', 'Sapota',
    'Sweet orange', 'Lime', 'Jackfruit', 'Pineapple', 'Watermelon', 'Muskmelon',
    'Onion', 'Potato', 'Chilli', 'Brinjal', 'Okra', 'Cabbage', 'Cauliflower',
    'Beans', 'Peas', 'Carrot', 'Beetroot', 'Radish', 'Cucumber', 'Bitter gourd',
    'Bottle gourd', 'Ridge gourd', 'Pumpkin', 'Ash gourd', 'Drumstick (Moringa)',
    'Spinach', 'Amaranth', 'Coriander', 'Turmeric', 'Ginger', 'Garlic',
    'Black pepper', 'Cardamom', 'Clove', 'Nutmeg', 'Tamarind', 'Curry leaves',
    'Rose', 'Marigold', 'Jasmine', 'Chrysanthemum', 'Tuberose', 'Crossandra',
    'Tobacco', 'Mulberry', 'Fodder grass', 'Other',
]
