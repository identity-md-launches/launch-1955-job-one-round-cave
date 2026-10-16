# Gathering 41 image provenance

Used the built-in image_gen tool in edit mode, with
`artifacts/gathering/wall-v20.png` as the sole reference. Prompt:

> Use case: precise-object-edit. Edit this existing square cave painting minimally. Preserve exact 1254 by 1254 dimensions, every existing mark, Pepe, hands, rock cracks, torchlight and framing. Add only a tiny worn earth-pigment motif on the bare patch at x=620..700 y=170..235: four small uneven red/yellow ochre pebbles gathered around a chalk-white dot with a short crooked charcoal arc beneath. It signifies four useful tools meeting. Everything outside that small patch must remain pixel-identical. No new figures or hands. Keep the existing Pepe frog with wide mouth and heavy-lidded eyes and five digits per hand exactly. Prehistoric Lascaux stick and thumb marks, stone texture showing through. No letters, numbers, captions, signatures, logos, watermarks, border, frame, real people, politics, hateful symbols, photographs or 3D.

The candidate placed the motif over the inherited hand stencil and changed
other pixels. `finish_wall41.js` admitted only its new pigment silhouette onto
bare rock, leaving the stencil and all other ancestor pixels intact. The
candidate was overwritten by the finished wall; no additional image is kept.
858 pixels differ inside x=620..680,y=190..255; zero outside. The finish script
requires the original generated candidate, not the finished output.

Chosen visual review: open final PNG and 512 px JPEG, count all hand digits,
inspect for prohibited writing/symbols, and compare pixels with the ancestor.
Both figure hands retain four fingers and one thumb; the upper stencil retains
five digits. No new hands, figures, text, symbols, border or framing changes.
The addition is small and faint in the preview. No unmet visual requirement was
observed locally. This is local review, not independent visual certification.
