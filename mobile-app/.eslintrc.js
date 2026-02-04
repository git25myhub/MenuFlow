module.exports = {
  root: true,
  extends: ['expo', 'eslint:recommended'],
  env: {
    browser: true,
    es2021: true,
  },
  ignorePatterns: ['/node_modules/', '/dist/', '/build/', '*.config.js'],
};
