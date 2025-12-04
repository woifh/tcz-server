/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'court-available': '#10b981',  // green-500
        'court-reserved': '#ef4444',   // red-500
        'court-blocked': '#6b7280',    // gray-500
      },
    },
  },
  plugins: [],
}
