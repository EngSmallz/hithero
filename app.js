const express = require('express');
const db = require('./db'); // Import your database connection module
const app = express();
const port = process.env.PORT || 3000;

// Connect to the database
db.connect();

// Your web application code goes here

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
