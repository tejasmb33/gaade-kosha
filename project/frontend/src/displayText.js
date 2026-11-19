// Remove editorial prefixes only in presentation; originals and review metadata remain intact.
export function displayText(value='') {
 let text=String(value??'').trim();
 const prefix=/^(?:(?:context(?:ual)?\s+)?draft(?:\s+for\s+human\s+verification)?|(?:for\s+)?human\s+verification|(?:ಮಾನವ|ಮನುಷ್ಯ)\s*ಪರಿಶೀಲನೆಗಾಗಿ(?:\s*(?:ಕರಡು|ಡ್ರಾಫ್ಟ್))?|(?:ಕರಡು|ಡ್ರಾಫ್ಟ್)(?:\s*(?:ಮಾನವ|ಮನುಷ್ಯ)\s*ಪರಿಶೀಲನೆಗಾಗಿ)?)\s*[:：.\-–—]\s*/i;
 while(prefix.test(text))text=text.replace(prefix,'').trim();
 return text;
}
