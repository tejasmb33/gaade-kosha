# District explorer content

The page lives at `/#districts` and is rendered by `DistrictExplorer.jsx`. It is lazy-loaded so the boundary data does not inflate the home-page bundle. It needs no API key or backend request.

## Edit district information

`karnataka-districts.json` is an array of 31 records imported from the supplied `Karnataka_31_Districts.docx`. English/Kannada descriptions preserve the supplied document. Kannada highlight labels translate the supplied English speciality list. Photographs were copied from the user's explicitly supplied Downloads files to `public/images/districts/`, with stable, URL-safe names. No ownership or licence for the supplied photographs is asserted.

Each record has this structure (empty fields are omitted from the card):

```json
{
  "id": "mysuru",
  "code": "MYS",
  "name": {"kn": "ಮೈಸೂರು", "en": "Mysuru"},
  "aliases": [],
  "image": {
    "src": "/images/districts/mysuru.jpg",
    "alt": {"kn": "ನಿಮ್ಮ ಕನ್ನಡ ಚಿತ್ರದ ವಿವರಣೆ", "en": "Your image description"},
    "position": "center"
  },
  "description": {"kn": "ನಿಮ್ಮ ಕನ್ನಡ ಪರಿಚಯ", "en": "Your district introduction"},
  "highlights": {"kn": ["ಮೊದಲ ವಿಶೇಷತೆ"], "en": ["First highlight"]},
  "history": {"kn": "", "en": ""},
  "places": {"kn": [], "en": []},
  "food": {"kn": [], "en": []},
  "culture": {"kn": "", "en": ""},
  "source": "Your content reference"
}
```

Keep `id` and `code` stable: `code` connects the district content to its SVG shape. Change `image.src` to any local public asset path; adjust `image.position` to change its crop. Provide both `kn` and `en` whenever adding text. Food/history/places/culture fields are placeholders until you supply those sections; the original overview already includes the cultural and food information present in the document. Nothing is inferred for empty fields.

The component also accepts `districts` and `geometry` props to reuse it elsewhere. Theme overrides are scoped CSS variables: `--district-panel`, `--district-text`, `--district-secondary`, `--district-primary`, `--district-highlight`, `--district-border`, and `--district-map-fill`. Existing app styles remain intact.

## Map attribution and boundary limitations

`karnataka-boundaries.json` extracts 31 district-filled paths from the 16 June 2023 version of [Vijayanagara in Karnataka (India).svg](https://commons.wikimedia.org/wiki/File:Vijayanagara_in_Karnataka_(India).svg), by C1MM, based on Nayvik. The geometry is licensed **CC BY-SA 3.0**, https://creativecommons.org/licenses/by-sa/3.0/. Changes: removed surrounding states, locator inset and boundary line overlays; retained district-filled paths, changed the viewBox, recoloured and connected shapes to interactive district cards. This derived geometry remains under CC BY-SA 3.0; the page includes visible source/licence attribution. SVG metadata/scripts/foreign content are not rendered.

District identities were cross-checked against the named Karnataka district shape reference at https://github.com/arav-ind/svgmaps-india/blob/master/packages/karnataka/src/constants/karnataka.ts. Only the licensed Wikimedia geometry is shipped. The 31 mappings are one-to-one and include Vijayanagara as a separate district. This is an educational/illustrative map, not a surveyed or certified boundary product. Replace the geometry when authoritative boundaries change.

The supplied document's Bengaluru South label is used for the Ramanagara shape. The naming change is corroborated by the district administration: https://bengalurusouth.nic.in/en/. Other labels follow the supplied document (including Bengaluru Rural). No unverified administrative-boundary changes are invented.

## Illustrated map view

The default illustrated view uses the user-supplied `public/images/karnataka-art-map.png`, preserved without raster edits. Its decorative divisions are not administrative boundaries. `karnataka-artwork-boundaries.json` contains 31 independent contours traced from the white separators in this exact 1086×1448 PNG. The background image, hit paths, clip paths, selected outline and raised outline all use the same native image coordinate system, with **no geographic scaling/translation matrix**. The previous-map toggle still uses `karnataka-boundaries.json` and the original geographic shapes.

The card, language and selected district persist when changing map views. On hover/keyboard focus, the corresponding clipped artwork region lifts 8 SVG units and scales to 1.045, with a shadow and outline. The raised layer does not receive pointer events, preventing flicker/click interception. Reduced-motion users receive a static highlight.

Illustrated region identities use a one-to-one spatial association with the existing district list. This is an artistic interface, not a georeferenced or certified district map; the illustrated landmarks/divisions must not be treated as geographic evidence. Use the previous boundary map for geographic district selection.

To regenerate contours after changing the artwork, run the authoring utility from the frontend directory (Playwright Chromium must already be installed):

```
node scripts/trace-artwork.cjs
```

The utility detects white separator pixels, closes small gaps, traces 31 connected region outlines, restores border thickness, simplifies the paths, and associates them with the district IDs. It does not alter the PNG or download models. Review the resulting associations and outlines when replacing the image. The production site uses the generated JSON directly; tracing is never run in a visitor's browser or during deployment.

The browser test compares contour vertices to the actual PNG's separator pixels and exercises all 31 interior hit areas, alongside map switching, language, keyboard and mobile interactions.
