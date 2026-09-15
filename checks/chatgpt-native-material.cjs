// Run: node checks/chatgpt-native-material.cjs [archive-path]
// Tests the packaged selector's behavior; Windows/native visual checks are separate.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const archive = fs.readFileSync(process.argv[2] || 'D:/Documents/ChatGPT-Acrylic/app/resources/app.asar');
const header = JSON.parse(archive.subarray(16, 16 + archive.readUInt32LE(12)));
const entry = header.files['.vite'].files.build.files['main-D8abTQQE.js'];
const start = 8 + archive.readUInt32LE(4) + Number(entry.offset);
const code = archive.subarray(start, start + entry.size).toString();
const extract = (name, next) => {
  const from = code.indexOf('function ' + name + '(');
  const to = code.indexOf('function ' + next + '(', from);
  assert(from >= 0 && to > from, 'Unsupported app bundle');
  return code.slice(from, to);
};
const select = vm.runInNewContext(
  extract('P9', 'T6e') + extract('F9', 'A6e') + ';F9',
  {D9: '#00000000', r6e: '#dark', i6e: '#light'}
);
for (const appearance of ['primary', 'detached', 'secondary']) {
  const result = select({platform: 'win32', appearance, opaqueWindowSurfaceEnabled: false, prefersDarkColors: true});
  assert.equal(result.backgroundMaterial, 'acrylic', `${appearance}: transparent Windows surfaces must request Acrylic`);
  assert.equal(result.backgroundColor, '#00000000');
}
for (const dark of [false, true]) {
  const result = select({platform: 'win32', appearance: 'primary', opaqueWindowSurfaceEnabled: true, prefersDarkColors: dark});
  assert.equal(result.backgroundMaterial, 'none', 'Preserve explicit opaque fallback');
  assert.equal(result.backgroundColor, dark ? '#dark' : '#light');
}
for (const input of [{platform: 'darwin', appearance: 'primary'}, {platform: 'win32', appearance: 'avatarOverlay'}]) {
  assert.equal(select({...input, opaqueWindowSurfaceEnabled: false}).backgroundMaterial, null);
}
console.log('PASS: packaged selector requests Acrylic; opaque fallback and other surfaces retain their behavior.');
