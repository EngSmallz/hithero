const sql = require('mssql');

const config = {
  user: 'hithero_admin',
  password: 'MedL&ke15',
  server: 'hithero.database.windows.net',
  database: 'hithero_learn',
  options: {
    encrypt: true, // Use encryption
  },
};

async function connect() {
  try {
    await sql.connect(config);
    console.log('Connected to the database');
  } catch (err) {
    console.error('Database connection error:', err);
  }
}

module.exports = {
  connect,
};
