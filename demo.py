"""Offline fixtures: identical across versions; never research measurements."""
HEADINGS = {
 'English': ['Problem','Possible cause','What to do now','Prevention','Ask an expert','Follow-up'],
 'Kannada': ['ಸಮಸ್ಯೆ','ಸಂಭವನೀಯ ಕಾರಣ','ಈಗ ಮಾಡಬೇಕಾದದ್ದು','ಮುನ್ನೆಚ್ಚರಿಕೆ','ತಜ್ಞರ ಸಲಹೆ','ಹೆಚ್ಚಿನ ಮಾಹಿತಿ'],
 'Hindi': ['समस्या','संभावित कारण','अभी क्या करें','बचाव','विशेषज्ञ की सलाह','अगला सवाल'],
}
DISCLAIMER = {
 'English': 'Educational guidance only. Symptoms do not confirm a diagnosis. Consult your local agriculture officer or Krishi Vigyan Kendra before treatment.',
 'Kannada': 'ಇದು ಶೈಕ್ಷಣಿಕ ಮಾಹಿತಿ ಮಾತ್ರ. ಲಕ್ಷಣಗಳಿಂದಲೇ ರೋಗವನ್ನು ಖಚಿತಪಡಿಸಲಾಗದು. ಚಿಕಿತ್ಸೆಗೂ ಮೊದಲು ಸ್ಥಳೀಯ ಕೃಷಿ ಅಧಿಕಾರಿ ಅಥವಾ ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರವನ್ನು ಸಂಪರ್ಕಿಸಿ.',
 'Hindi': 'यह केवल शैक्षिक जानकारी है। लक्षणों से रोग की पुष्टि नहीं होती। उपचार से पहले स्थानीय कृषि अधिकारी या कृषि विज्ञान केंद्र से सलाह लें।',
}

def demo_advice(case):
    language = case['language']
    if language == 'Kannada':
        return dict(problem='ಬೆಳೆಯ ಸಮಸ್ಯೆಯ ಬಗ್ಗೆ ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಬೇಕು.',
          cause='ನೀರು, ಪೋಷಕಾಂಶ ಅಥವಾ ಕೀಟದ ಸಮಸ್ಯೆ ಇರಬಹುದು. ಕಾರಣ ಇನ್ನೂ ಖಚಿತವಾಗಿಲ್ಲ.',
          steps=['ಎಲೆಗಳ ಎರಡೂ ಬದಿಗಳನ್ನು ಮತ್ತು ಮಣ್ಣಿನ ತೇವವನ್ನು ಪರಿಶೀಲಿಸಿ.', 'ಲಕ್ಷಣಗಳು ಯಾವಾಗ ಆರಂಭವಾದವು ಮತ್ತು ಎಷ್ಟು ಸಸಿಗಳಲ್ಲಿ ಇವೆ ಎಂದು ದಾಖಲಿಸಿ.', 'ಕಾರಣ ತಿಳಿಯದೆ ಕೀಟನಾಶಕ ಬಳಸಬೇಡಿ ಅಥವಾ ರಾಸಾಯನಿಕಗಳನ್ನು ಮಿಶ್ರಣ ಮಾಡಬೇಡಿ.'],
          prevent='ಬೆಳೆಯನ್ನು ನಿಯಮಿತವಾಗಿ ಗಮನಿಸಿ. ರೋಗ ಖಚಿತವಾಗುವವರೆಗೆ ಉಪಕರಣಗಳನ್ನು ಸ್ವಚ್ಛವಾಗಿಡಿ.',
          expert='ಚಿಕಿತ್ಸೆಗೂ ಮೊದಲು ಸ್ಥಳೀಯ ಕೃಷಿ ಅಧಿಕಾರಿ ಅಥವಾ ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರದ ಸಲಹೆ ಪಡೆಯಿರಿ. ನಿಖರ ಕೀಟನಾಶಕ ಪ್ರಮಾಣವನ್ನು ಇಲ್ಲಿ ನೀಡಲಾಗುವುದಿಲ್ಲ.',
          follow_up='ಯಾವ ಲಕ್ಷಣಗಳು ಕಾಣುತ್ತಿವೆ? ಎಷ್ಟು ದಿನಗಳಿಂದ ಇವೆ?')
    if language == 'Hindi':
        return dict(problem='फसल की समस्या समझने के लिए और जानकारी चाहिए।',
          cause='पानी, पोषक तत्व या कीट से जुड़ी समस्या हो सकती है। कारण अभी पक्का नहीं है।',
          steps=['पत्तियों के दोनों तरफ और मिट्टी की नमी जाँचें।', 'लक्षण कब शुरू हुए और कितने पौधों पर हैं, यह लिख लें।', 'कारण जाने बिना कीटनाशक न डालें और रसायन न मिलाएँ।'],
          prevent='फसल को नियमित रूप से देखें और औजार साफ रखें।',
          expert='उपचार से पहले स्थानीय कृषि अधिकारी या कृषि विज्ञान केंद्र से सलाह लें। यहाँ कीटनाशक की सटीक मात्रा नहीं दी जाती।',
          follow_up='कौन से लक्षण दिख रहे हैं और कितने दिनों से हैं?')
    return dict(problem='More detail is needed to understand this crop concern.',
      cause='Water stress, nutrients or pests may be involved. The cause is unconfirmed.',
      steps=['Check both sides of leaves and soil moisture.', 'Record when symptoms began and how many plants are affected.', 'Avoid pesticide application or chemical mixing before identifying the problem.'],
      prevent='Inspect the crop regularly and keep tools clean.',
      expert='Ask your local agriculture officer or KVK before treatment. Exact pesticide dosages are not provided here.',
      follow_up='What symptoms do you see, and when did they start?')
