const http = require('http');
const fs = require('fs');
if (!process.env.DATABASE_URL) { console.error('DATABASE_URL missing'); process.exit(1); }
http.createServer((req, res) => {
  if (req.url === '/healthz') return res.end('ok\n');
  const schema = fs.existsSync('/data/schema') ? fs.readFileSync('/data/schema', 'utf8') : 'none';
  res.end(`fixture node app, schema ${schema}\n`);
}).listen(3000, '0.0.0.0');
