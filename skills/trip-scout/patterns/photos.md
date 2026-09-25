---
pattern: photos
uses:
  sources: [kind=page-render]
  tools: [python+pillow]
---
# Photos (opt-in)

**Default: no copies.** Each card links to its listing, and the listing shows the photos.

Copy photos only after the user opts in, having been told that this reproduces copyrighted images and that private-copying exceptions vary by country. Limits:

- At most 2 low-res photos per listing.
- A private page only, with each photo credited and linked to its listing.
- Delete the copies if the page is ever shared.
- Never copy host portraits.

## Recipe

Use this when the workspace can't reach the image CDN:

1. Write a tiny HTML page whose script lays the image URLs out in a fixed grid (4 columns × 768×512 cells, `object-fit: cover`).
2. Render it with a `page-render` source in raw-HTML mode (wait for network idle, add a ~4 s delay, ≤12 images per run).
3. Read the image from the run's storage.
4. Crop the cells with Pillow to ~600×400, JPEG quality ~74.
5. Keep a map from each cell to its listing.
