# Built-in imagegen edit prompt

Edit target: `artifacts/line-4/wall-v20.png` (record 40, SHA-256
`eaa5b1e9cdf1c45b8a7344565ec005291327baa5549cf54d51801cf3836fec4a`).
Tool: built-in `image_gen.imagegen`; transparent background: false.

> Use case: precise-object-edit. Edit target: the supplied ancestral cave painting. Keep the image exactly 1254 by 1254 square with identical rock, light, cracks, framing and every previous mark untouched. Add just ONE small prehistoric motif on bare rock near x=1100,y=1100 (lower right beneath the little frog, to the right of the bowl): a tiny worn charcoal fork-shaped twig with two small ochre seeds caught between its branches, representing a filter selecting values. About 80 pixels wide and 70 high. Rough uneven thumb and burnt stick earth pigments, bare stone showing through. Do not change or redraw either Pepe frog, any hands or any other marks. No new hands. No letters, numbers, writing, symbols resembling writing, logos, watermarks, borders, frames, photography or 3D render. Preserve all ancestral pixels except this tiny bare-rock addition. Save the resulting PNG to artifacts/line-4/wall-v21.png if possible.

The generated candidate had one seed and repainted other areas slightly.
The export retains only its twig/seed pigment in the reviewed bare-rock patch,
preserving the ancestor elsewhere. The candidate was consumed in place;
no extra generated picture is delivered.
