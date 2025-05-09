const express = require('express');
const path = require('path');
const app = express();
const port = 443; // Port 443 is typically used for HTTPS, may require elevated privileges

// Serve static files from the 'website' directory
app.use(express.static(path.join(__dirname, '/')));

// Catch-all route to serve index.html for any other requests
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(port, () => {
  console.log(`Web server listening on port ${port}`);
  console.log(`Serving files from: ${__dirname}`);
});
