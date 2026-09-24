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
    featured  true = rotates in the full-width slideshow at the top of the home page, in this order.
              The first 4 (or 6, once there are 6+) also fill "From the studio".
    focus     optional. Which part of the painting stays in view when the slideshow crops it to a wide band,
              as "x% y%" (e.g. "40% 45%"). Default is the center. The gallery always shows the whole painting.

  Titles below come from the file names on Susan's Padlet board. Years come only from signatures visible
  on the work. Everything else is blank until Susan confirms it.
  With no image (src: ""), a piece shows a generated color-field placeholder and uses "hue" for its colors.
*/
window.ARTWORKS = [
  { src: "images/art/sea-turtle.jpg",           title: "Turtle",              year: "2020", medium: "", size: "", category: "", status: "", ratio: 1.348, featured: true, focus: "45% 45%" },
  { src: "images/art/truck-in-las-cruces.jpg",  title: "Truck in Las Cruces", year: "",     medium: "", size: "", category: "", status: "", ratio: 1.671, featured: true, focus: "60% 50%" },
  { src: "images/art/santa-barbara.jpg",        title: "Santa Barbara",       year: "",     medium: "", size: "", category: "", status: "", ratio: 0.996, featured: true, focus: "50% 62%" },
  { src: "images/art/mountain-water.jpg",       title: "Untitled",            year: "2019", medium: "", size: "", category: "", status: "", ratio: 1.508, featured: true, focus: "50% 45%" },
  { src: "images/art/fields-and-palms.jpg",     title: "Untitled",            year: "",     medium: "", size: "", category: "", status: "", ratio: 1.447, featured: true, focus: "50% 40%" }
];
