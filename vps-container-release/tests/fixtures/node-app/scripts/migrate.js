const fs = require('fs');
fs.mkdirSync('/data', { recursive: true });
fs.writeFileSync('/data/schema', 'v2');
console.log('migrated to v2');
