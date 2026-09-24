/*
  ARTWORK LIST — the only file you edit to change what shows on the site.

  For each piece:
    src       path to the image, e.g. "images/art/river-light.jpg"  (leave "" to show a placeholder)
    title     title of the work
    year      e.g. "2024"
    medium    e.g. "Oil on canvas"
    size      e.g. "24 × 30 in"
    category  used for the Gallery filters (e.g. "Painting", "Drawing", "Mixed Media")
    status    "Available", "Sold", "Private collection", or "" to hide
    ratio     width / height of the image (e.g. 0.8 for portrait 4:5, 1.25 for landscape) — keeps the grid tidy
    featured  true = shown on the home page. The FIRST featured piece is the big home image; the next 6 fill "Recent pieces".

  Everything below is PLACEHOLDER content until Susan's real images and details are added.
*/
window.ARTWORKS = [
  { src: "", title: "Untitled I",    year: "", medium: "", size: "", category: "Painting",    status: "", ratio: 0.8,  featured: true,  hue: [28, 14, 200] },
  { src: "", title: "Untitled II",   year: "", medium: "", size: "", category: "Painting",    status: "", ratio: 1.25, featured: true,  hue: [210, 190, 40] },
  { src: "", title: "Untitled III",  year: "", medium: "", size: "", category: "Mixed Media", status: "", ratio: 1,    featured: true,  hue: [8, 30, 180] },
  { src: "", title: "Untitled IV",   year: "", medium: "", size: "", category: "Drawing",     status: "", ratio: 0.75, featured: true,  hue: [40, 45, 30] },
  { src: "", title: "Untitled V",    year: "", medium: "", size: "", category: "Painting",    status: "", ratio: 1.33, featured: true,  hue: [160, 140, 20] },
  { src: "", title: "Untitled VI",   year: "", medium: "", size: "", category: "Mixed Media", status: "", ratio: 0.8,  featured: true,  hue: [350, 20, 220] },
  { src: "", title: "Untitled VII",  year: "", medium: "", size: "", category: "Drawing",     status: "", ratio: 1,    featured: true , hue: [30, 30, 30] },
  { src: "", title: "Untitled VIII", year: "", medium: "", size: "", category: "Painting",    status: "", ratio: 0.7,  featured: false, hue: [200, 25, 45] },
  { src: "", title: "Untitled IX",   year: "", medium: "", size: "", category: "Mixed Media", status: "", ratio: 1.2,  featured: false, hue: [90, 60, 20] },
  { src: "", title: "Untitled X",    year: "", medium: "", size: "", category: "Painting",    status: "", ratio: 0.85, featured: false, hue: [15, 355, 45] },
  { src: "", title: "Untitled XI",   year: "", medium: "", size: "", category: "Drawing",     status: "", ratio: 1.4,  featured: false, hue: [220, 210, 35] },
  { src: "", title: "Untitled XII",  year: "", medium: "", size: "", category: "Painting",    status: "", ratio: 0.8,  featured: false, hue: [45, 20, 190] }
];
