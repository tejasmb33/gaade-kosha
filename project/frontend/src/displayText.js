// Presentation-only editorial labels; source records remain unchanged.
export function displayText(value='') {
 return value.replace(/^(?:Draft(?: for human verification)?|ಮಾನವ ಪರಿಶೀಲನೆಗಾಗಿ (?:ಕರಡು|ಡ್ರಾಫ್ಟ್)|ಕರಡು|ಡ್ರಾಫ್ಟ್)\s*:\s*/i,'').trim();
}
