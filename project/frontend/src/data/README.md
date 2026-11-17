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

The default illustrated view uses the user-supplied `public/images/karnataka-art-map.png`, preserved without raster edits. Its decorative borders are not administrative boundaries. Transparent SVG regions reuse the same 31 district identities and are placed over the image as illustrative hotspots with a scale/translation transform. The illustration is not georeferenced and hotspot outlines do not necessarily coincide with its decorative divisions; use the Previous map toggle to inspect the original district geometry. The card, language and selected district persist when changing map views. On hover/keyboard focus, a clipped copy of the supplied artwork lifts 8 SVG units and scales to 1.045, with a shadow and outline. The raised layer does not receive pointer events, preventing hover flicker/click interception. Reduced-motion users receive a static highlight.
